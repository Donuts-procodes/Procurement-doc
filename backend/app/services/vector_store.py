from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from typing import Any, Literal

logger = logging.getLogger("gdocs.vector_store")

MILVUS_URI = os.environ.get("MILVUS_URI", "http://localhost:19531")
MILVUS_HOST = os.environ.get("MILVUS_HOST", "milvus")
MILVUS_PORT = int(os.environ.get("MILVUS_PORT", 19530))
MILVUS_LOCAL_FILE = os.environ.get("MILVUS_LOCAL_FILE", "./milvus_data/milvus_demo.db")

# Vector dimension for Milvus collection
VECTOR_DIM = 384


def _deterministic_embedding(text: str, dim: int = VECTOR_DIM) -> list[float]:
    """
    Generates a deterministic normalized pseudo-embedding vector from text
    when external embedding providers are not configured.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    raw = [float(b) / 255.0 for b in h]
    # Tile to target dimension
    extended = (raw * ((dim // len(raw)) + 1))[:dim]
    norm = sum(x * x for x in extended) ** 0.5 or 1.0
    return [round(x / norm, 6) for x in extended]


class MilvusVectorStoreManager:
    """Manages connection and collections for Milvus Vector Database."""

    def __init__(self) -> None:
        self.client: Any = None
        self._init_milvus_client()

    def _init_milvus_client(self) -> None:
        """Initializes connection to Milvus standalone server or local Milvus-lite fallback."""
        try:
            from pymilvus import MilvusClient
            # Try remote URI first (e.g. http://milvus:19530 in docker-compose)
            uri = f"http://{MILVUS_HOST}:{MILVUS_PORT}" if MILVUS_HOST != "localhost" else MILVUS_URI
            self.client = MilvusClient(uri=uri)
            logger.info(f"✅ Connected to Milvus Vector Database at {uri}")
        except Exception as exc:
            logger.warning(f"⚠️ Remote Milvus at {MILVUS_URI} unreachable ({exc}). Using Milvus-lite or fallback...")
            try:
                from pymilvus import MilvusClient
                os.makedirs(os.path.dirname(MILVUS_LOCAL_FILE), exist_ok=True)
                self.client = MilvusClient(uri=MILVUS_LOCAL_FILE)
                logger.info(f"✅ Using local embedded Milvus-lite at '{MILVUS_LOCAL_FILE}'")
            except Exception as e:
                logger.error(f"❌ Could not initialize Milvus client: {e}")
                self.client = None

    def ensure_collection(self, collection_name: str) -> None:
        if not self.client:
            return
        try:
            if not self.client.has_collection(collection_name):
                self.client.create_collection(
                    collection_name=collection_name,
                    dimension=VECTOR_DIM,
                    metric_type="COSINE",
                    auto_id=True,
                )
                logger.info(f"Created Milvus collection: {collection_name}")
        except Exception as exc:
            logger.warning(f"Error ensuring Milvus collection {collection_name}: {exc}")


_milvus_manager = MilvusVectorStoreManager()


class KnowledgeBase:
    """Enterprise Knowledge Base powered by Milvus Vector Database."""

    def __init__(self, kb_id: str | None = None, collection_type: Literal["general", "policy", "vendor"] = "general") -> None:
        self.kb_id = kb_id or uuid.uuid4().hex
        self.collection_type = collection_type
        # Milvus collection names must be valid identifiers
        clean_kb_id = self.kb_id.replace("-", "_").lower()
        self.collection_name = f"kb_{self.collection_type}_{clean_kb_id}"[:60]
        
        # Local fallback store in case Milvus connection is initializing
        self._local_fallback: list[dict[str, Any]] = []

        if _milvus_manager.client:
            _milvus_manager.ensure_collection(self.collection_name)

    def add_chunks(self, chunks: list[str], source: str, metadata_extra: dict[str, Any] | None = None) -> int:
        if not chunks:
            return 0

        rows: list[dict[str, Any]] = []
        for c in chunks:
            vec = _deterministic_embedding(c, VECTOR_DIM)
            meta_json = json.dumps(metadata_extra or {})
            rows.append({
                "vector": vec,
                "text": c,
                "source": source,
                "collection_type": self.collection_type,
                "metadata": meta_json,
            })
            self._local_fallback.append({
                "vector": vec,
                "text": c,
                "source": source,
                "metadata": metadata_extra or {},
            })

        if _milvus_manager.client:
            try:
                _milvus_manager.ensure_collection(self.collection_name)
                _milvus_manager.client.insert(
                    collection_name=self.collection_name,
                    data=rows,
                )
                logger.info(f"✅ Ingested {len(chunks)} chunks into Milvus collection '{self.collection_name}'")
                return len(chunks)
            except Exception as exc:
                logger.warning(f"Milvus insertion error ({exc}), using local store buffer.")

        return len(chunks)

    def query(self, text: str, limit: int = 5) -> list[str]:
        logger.info(f"Executing ANN Dense search in Milvus for: '{text[:80]}...'")

        if _milvus_manager.client:
            try:
                _milvus_manager.ensure_collection(self.collection_name)
                query_vec = _deterministic_embedding(text, VECTOR_DIM)
                search_res = _milvus_manager.client.search(
                    collection_name=self.collection_name,
                    data=[query_vec],
                    limit=limit,
                    output_fields=["text", "source"],
                )
                if search_res and len(search_res) > 0:
                    hits = search_res[0]
                    documents: list[str] = []
                    for h in hits:
                        entity = h.get("entity") or {}
                        txt = entity.get("text")
                        if txt:
                            documents.append(str(txt))
                    if documents:
                        return documents
            except Exception as exc:
                logger.warning(f"Milvus search error ({exc}), querying local fallback buffer.")

        # Local fallback search using cosine similarity over local buffer
        if not self._local_fallback:
            return []

        query_vec = _deterministic_embedding(text, VECTOR_DIM)
        scored: list[tuple[float, str]] = []
        for item in self._local_fallback:
            vec = item["vector"]
            # Dot product for normalized vectors
            sim = sum(a * b for a, b in zip(query_vec, vec))
            scored.append((sim, item["text"]))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scored[:limit]]


def get_knowledge_base(kb_id: str, collection_type: Literal["general", "policy", "vendor"] = "general") -> KnowledgeBase:
    return KnowledgeBase(kb_id=kb_id, collection_type=collection_type)
