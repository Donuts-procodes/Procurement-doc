from __future__ import annotations

import logging
import os
import re
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.services.vector_store import KnowledgeBase

logger = logging.getLogger("gdocs.saas_connectors")

# security-auditor: All tokens from environment, never hardcoded
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
CRM_API_KEY = os.environ.get("CRM_API_KEY")
CRM_BASE_URL = os.environ.get("CRM_BASE_URL")


class SaaSRecord(BaseModel):
    """Normalized record from any 3rd-party SaaS source."""
    record_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    source_type: Literal["google_drive", "crm", "custom"] = "custom"
    source_label: str = ""
    title: str = ""
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    attribution_tag: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.attribution_tag:
            self.attribution_tag = f"[^{self.source_type}_{self.record_id[:6]}]"


class SaaSIngestionResult(BaseModel):
    records_fetched: int = 0
    chunks_indexed: int = 0
    source_type: str = ""
    attribution_tags: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


def _sanitize_content(raw: str, max_len: int = 6000) -> str:
    """rag-vector-pipeline: Strip noise, PII markers, and structural junk before vector indexing."""
    cleaned = re.sub(r"<[^>]+>", " ", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # security-auditor: Mask obvious PII patterns (emails, phone numbers)
    cleaned = re.sub(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", "[EMAIL_REDACTED]", cleaned)
    cleaned = re.sub(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE_REDACTED]", cleaned)
    return cleaned[:max_len]


def _chunk_content(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """rag-vector-pipeline: Deterministic fixed-token chunking with controlled overlap."""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


async def fetch_google_drive_document(file_id: str, kb_id: str | None = None) -> SaaSIngestionResult:
    """Fetch a Google Drive document and ingest into the vector store.
    ponytail: Stubbed HTTP call — actual google-api-python-client integration
    requires the user's service account JSON to be provisioned."""
    result = SaaSIngestionResult(source_type="google_drive")

    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        result.errors.append("GOOGLE_SERVICE_ACCOUNT_JSON env var not configured")
        logger.warning("SaaS Connector: Google Drive not configured (missing service account)")
        return result

    try:
        # ponytail: Placeholder for google.oauth2 + googleapiclient.discovery
        # Actual implementation:
        #   creds = service_account.Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_JSON)
        #   service = build("drive", "v3", credentials=creds)
        #   content = service.files().export(fileId=file_id, mimeType="text/plain").execute()
        logger.info(f"📂 SaaS Connector: Would fetch Google Drive file '{file_id}'")
        result.errors.append("Google Drive connector ready but requires active service account credentials")
        return result
    except Exception as e:
        result.errors.append(str(e)[:200])
        return result




async def fetch_crm_opportunity(opportunity_id: str, kb_id: str | None = None) -> SaaSIngestionResult:
    """Fetch CRM opportunity/deal record and ingest into vector store."""
    result = SaaSIngestionResult(source_type="crm")

    if not CRM_API_KEY or not CRM_BASE_URL:
        result.errors.append("CRM_API_KEY or CRM_BASE_URL env var not configured")
        logger.warning("SaaS Connector: CRM not configured")
        return result

    try:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            headers = {"Authorization": f"Bearer {CRM_API_KEY}", "Accept": "application/json"}
            resp = await client.get(f"{CRM_BASE_URL}/api/opportunities/{opportunity_id}", headers=headers)
            resp.raise_for_status()
            data = resp.json()

            raw = f"Opportunity: {data.get('name', '')}. Value: {data.get('amount', 'N/A')}. Stage: {data.get('stage', '')}. Notes: {data.get('notes', '')}"
            sanitized = _sanitize_content(raw)
            record = SaaSRecord(
                source_type="crm",
                source_label=f"CRM Opportunity {opportunity_id}",
                title=data.get("name", opportunity_id),
                content=sanitized,
                metadata={"opportunity_id": opportunity_id, "stage": data.get("stage", "")},
            )
            result.records_fetched = 1
            if kb_id:
                result = await _ingest_records_to_kb([record], kb_id, result)

    except Exception as e:
        result.errors.append(str(e)[:200])
        logger.warning(f"SaaS Connector CRM error: {e}")

    return result


async def _ingest_records_to_kb(
    records: list[SaaSRecord], kb_id: str, result: SaaSIngestionResult
) -> SaaSIngestionResult:
    """rag-vector-pipeline: Chunk and index SaaS records into ChromaDB with source attribution."""
    kb = KnowledgeBase(kb_id=kb_id, collection_type="general")
    total_chunks = 0

    for record in records:
        chunks = _chunk_content(record.content)
        if chunks:
            added = kb.add_chunks(
                chunks,
                source=record.source_label,
                metadata_extra={"saas_source": record.source_type, "attribution": record.attribution_tag},
            )
            total_chunks += added
            result.attribution_tags.append(record.attribution_tag)

    result.chunks_indexed = total_chunks
    logger.info(f"📂 SaaS Connector: Indexed {total_chunks} chunks from {len(records)} {result.source_type} records into KB '{kb_id}'")
    return result
