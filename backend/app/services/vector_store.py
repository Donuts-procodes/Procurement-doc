from __future__ import annotations

import logging
import os
import uuid
from typing import Literal

import chromadb

logger = logging.getLogger("gdocs.vector_store")

CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", 8002))
CHROMA_LOCAL_PATH = os.environ.get("CHROMA_LOCAL_PATH", "./chroma_data")


def _create_chroma_client() -> chromadb.ClientAPI:
    """Factory that attempts remote ChromaDB HTTP client first,
    then falls back to local persistent embedded client."""
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        client.heartbeat()  # Verify connectivity
        logger.info(f"✅ Connected to remote ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
        return client
    except Exception as exc:
        logger.warning(
            f"⚠️ Remote ChromaDB at {CHROMA_HOST}:{CHROMA_PORT} unreachable ({exc}). "
            f"Falling back to local persistent storage at '{CHROMA_LOCAL_PATH}'."
        )
        client = chromadb.PersistentClient(path=CHROMA_LOCAL_PATH)
        logger.info(f"✅ Using local embedded ChromaDB at '{CHROMA_LOCAL_PATH}'")
        return client


_client = _create_chroma_client()


class KnowledgeBase:
    def __init__(self, kb_id: str | None = None, collection_type: Literal["general", "policy", "vendor"] = "general") -> None:
        self.kb_id = kb_id or uuid.uuid4().hex
        self.collection_type = collection_type
        self.collection_name = f"kb_{self.collection_type}_{self.kb_id}"
        self.collection = _client.get_or_create_collection(name=self.collection_name)

    def add_chunks(self, chunks: list[str], source: str, metadata_extra: dict | None = None) -> int:
        if not chunks:
            return 0
        ids = [uuid.uuid4().hex for _ in chunks]
        metadatas = []
        for _ in chunks:
            m = {"source": source, "collection_type": self.collection_type}
            if metadata_extra:
                m.update(metadata_extra)
            metadatas.append(m)

        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids,
        )
        return len(chunks)

    def query(self, text: str, limit: int = 5) -> list[str]:
        logger.info(f"Executing Dense search in ChromaDB for: {text}")
        
        results = self.collection.query(
            query_texts=[text],
            n_results=limit,
        )
        
        if not results or not results["documents"] or not results["documents"][0]:
            return []
            
        return results["documents"][0]


def get_knowledge_base(kb_id: str, collection_type: Literal["general", "policy", "vendor"] = "general") -> KnowledgeBase:
    return KnowledgeBase(kb_id=kb_id, collection_type=collection_type)
