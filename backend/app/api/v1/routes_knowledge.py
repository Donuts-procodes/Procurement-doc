from __future__ import annotations

import logging
from typing import Any
import uuid
from fastapi import APIRouter, HTTPException, UploadFile

from app.db.clause_store import clause_store
from app.db.document_store import DocumentStatus, document_store
from app.schemas.schemas import ImageSpatialAnchor, KnowledgeFileSummary, KnowledgeUploadResponse, ProcurementDocType
from app.services.document_parser import (
    chunk_text,
    extract_images_from_docx,
    extract_images_from_pdf,
    extract_images_with_anchors_docx,
    extract_images_with_anchors_pdf,
    extract_structured_tables_docx,
    extract_structured_tables_from_text,
    extract_text,
)
from app.services.vector_store import KnowledgeBase

logger = logging.getLogger("gdocs.routes_knowledge")
router = APIRouter(tags=["procurement"])

# Global cache for extracted PDF base64 images per kb_id (bounded to max 50 entries to prevent memory leaks)
KB_IMAGE_STORE: dict[str, list[str]] = {}
KB_SPATIAL_IMAGE_STORE: dict[str, list[ImageSpatialAnchor]] = {}
KB_STRUCTURED_TABLE_STORE: dict[str, list[dict[str, Any]]] = {}
KB_RAW_TEXT_STORE: dict[str, str] = {}

def _prune_cache(cache_dict: dict, max_size: int = 50) -> None:
    while len(cache_dict) > max_size:
        oldest_key = next(iter(cache_dict))
        cache_dict.pop(oldest_key, None)


@router.post("/knowledge/upload", response_model=KnowledgeUploadResponse)
async def upload_knowledge_files(
    files: list[UploadFile],
    kb_id: str | None = None,
) -> KnowledgeUploadResponse:
    target_kb_id = kb_id or uuid.uuid4().hex
    logger.info(f"POST /api/knowledge/upload: Ingesting {len(files)} files into Knowledge Base '{target_kb_id}'...")
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    kb = KnowledgeBase(kb_id=target_kb_id, collection_type="general")

    summaries: list[KnowledgeFileSummary] = []
    total_chunks = 0
    extracted_pdf_images: list[str] = []
    extracted_spatial_anchors: list[ImageSpatialAnchor] = []
    extracted_tables: list[dict[str, Any]] = []
    raw_texts: list[str] = []

    for upload in files:
        content = await upload.read()
        filename = upload.filename or "unnamed"
        logger.info(f"Parsing uploaded file '{filename}' ({len(content)} bytes)...")
        try:
            text = extract_text(filename, content)
            raw_texts.append(text)
        except ValueError as exc:
            logger.error(f"Failed to extract text from file '{filename}': {exc}")
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        # Extract images & diagrams from PDF and DOCX files with spatial anchors
        if filename.lower().endswith(".pdf"):
            anchors = extract_images_with_anchors_pdf(content, max_pages=10)
            logger.info(f"🖼️ Extracted {len(anchors)} spatial images/diagrams from PDF '{filename}'.")
            extracted_spatial_anchors.extend(anchors)
            extracted_pdf_images.extend([a.url_or_base64 for a in anchors])
        elif filename.lower().endswith(".docx"):
            anchors = extract_images_with_anchors_docx(content)
            logger.info(f"🖼️ Extracted {len(anchors)} spatial images/diagrams from DOCX '{filename}'.")
            extracted_spatial_anchors.extend(anchors)
            extracted_pdf_images.extend([a.url_or_base64 for a in anchors])
            tables = extract_structured_tables_docx(content)
            if tables:
                extracted_tables.extend(tables)

        # Extract markdown pipe tables from any uploaded text/markdown/pdf content
        text_tables = extract_structured_tables_from_text(text)
        if text_tables:
            extracted_tables.extend(text_tables)

        chunks = chunk_text(text)
        added = kb.add_chunks(chunks, source=filename)
        logger.info(f"File '{filename}' chunked into {added} vectors in ChromaDB collection '{kb.collection_name}'.")
        total_chunks += added
        summaries.append(KnowledgeFileSummary(filename=filename, chunk_count=added))

    if extracted_pdf_images:
        KB_IMAGE_STORE.setdefault(target_kb_id, []).extend(extracted_pdf_images)
        _prune_cache(KB_IMAGE_STORE)
    if extracted_spatial_anchors:
        KB_SPATIAL_IMAGE_STORE.setdefault(target_kb_id, []).extend(extracted_spatial_anchors)
        _prune_cache(KB_SPATIAL_IMAGE_STORE)
    if extracted_tables:
        KB_STRUCTURED_TABLE_STORE.setdefault(target_kb_id, []).extend(extracted_tables)
        _prune_cache(KB_STRUCTURED_TABLE_STORE)
    if raw_texts:
        if target_kb_id in KB_RAW_TEXT_STORE:
            KB_RAW_TEXT_STORE[target_kb_id] += "\n\n" + "\n\n".join(raw_texts)
        else:
            KB_RAW_TEXT_STORE[target_kb_id] = "\n\n".join(raw_texts)
        _prune_cache(KB_RAW_TEXT_STORE)

    logger.info(
        f"Knowledge Base ingestion complete: kb_id='{target_kb_id}', "
        f"new_chunks={total_chunks}, extracted_images={len(extracted_pdf_images)}, "
        f"spatial_anchors={len(extracted_spatial_anchors)}"
    )
    return KnowledgeUploadResponse(kb_id=target_kb_id, files=summaries, total_chunks=total_chunks)


@router.post("/knowledge/policy-upload", response_model=KnowledgeUploadResponse)
async def upload_policy_files(kb_id: str, files: list[UploadFile]) -> KnowledgeUploadResponse:
    logger.info(f"POST /api/knowledge/policy-upload: Ingesting policy files for kb_id='{kb_id}'")
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    kb = KnowledgeBase(kb_id=f"{kb_id}_policy", collection_type="policy")
    summaries: list[KnowledgeFileSummary] = []
    total_chunks = 0

    for upload in files:
        content = await upload.read()
        try:
            text = extract_text(upload.filename or "unnamed", content)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        chunks = chunk_text(text)
        added = kb.add_chunks(chunks, source=upload.filename or "unnamed")
        total_chunks += added
        summaries.append(KnowledgeFileSummary(filename=upload.filename or "unnamed", chunk_count=added))

    return KnowledgeUploadResponse(kb_id=kb_id, files=summaries, total_chunks=total_chunks)


@router.post("/knowledge/vendor-upload", response_model=KnowledgeUploadResponse)
async def upload_vendor_files(kb_id: str, files: list[UploadFile]) -> KnowledgeUploadResponse:
    logger.info(f"POST /api/knowledge/vendor-upload: Ingesting vendor files for kb_id='{kb_id}'")
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    kb = KnowledgeBase(kb_id=f"{kb_id}_vendor", collection_type="vendor")
    summaries: list[KnowledgeFileSummary] = []
    total_chunks = 0

    for upload in files:
        content = await upload.read()
        try:
            text = extract_text(upload.filename or "unnamed", content)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        chunks = chunk_text(text)
        added = kb.add_chunks(chunks, source=upload.filename or "unnamed")
        total_chunks += added
        summaries.append(KnowledgeFileSummary(filename=upload.filename or "unnamed", chunk_count=added))

    return KnowledgeUploadResponse(kb_id=kb_id, files=summaries, total_chunks=total_chunks)


@router.get("/clauses")
def list_clauses(doc_type: ProcurementDocType | None = None):
    logger.info(f"GET /api/clauses: listing approved clauses for doc_type='{doc_type}'")
    return clause_store.list_clauses(doc_type=doc_type)


@router.post("/document/{document_id}/status")
def update_document_status(document_id: str, status: DocumentStatus, actor: str = "Reviewer"):
    logger.info(f"POST /api/document/{document_id}/status: Transitioning status to '{status.value}' by '{actor}'")
    try:
        doc = document_store.update_status(document_id=document_id, new_status=status, actor=actor)
        return {"document_id": doc.document_id, "status": doc.status, "audit_log": doc.audit_log}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/document/{document_id}/audit-log")
def get_audit_log(document_id: str):
    logger.info(f"GET /api/document/{document_id}/audit-log")
    try:
        doc = document_store.get(document_id)
        return {"document_id": doc.document_id, "status": doc.status, "audit_log": doc.audit_log}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
