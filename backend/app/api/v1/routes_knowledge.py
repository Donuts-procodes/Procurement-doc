from __future__ import annotations

import logging
import uuid
from fastapi import APIRouter, HTTPException, UploadFile

from app.db.clause_store import clause_store
from app.db.document_store import DocumentStatus, document_store
from app.schemas.schemas import KnowledgeFileSummary, KnowledgeUploadResponse, ProcurementDocType
from app.services.document_parser import chunk_text, extract_images_from_docx, extract_images_from_pdf, extract_text
from app.services.vector_store import KnowledgeBase

logger = logging.getLogger("gdocs.routes_knowledge")
router = APIRouter(tags=["procurement"])

# Global cache for extracted PDF base64 images per kb_id
KB_IMAGE_STORE: dict[str, list[str]] = {}


@router.post("/knowledge/upload", response_model=KnowledgeUploadResponse)
async def upload_knowledge_files(files: list[UploadFile]) -> KnowledgeUploadResponse:
    logger.info(f"POST /api/knowledge/upload: Ingesting {len(files)} files into Knowledge Base...")
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    kb_id = uuid.uuid4().hex
    kb = KnowledgeBase(kb_id=kb_id, collection_type="general")

    summaries: list[KnowledgeFileSummary] = []
    total_chunks = 0
    extracted_pdf_images: list[str] = []

    for upload in files:
        content = await upload.read()
        filename = upload.filename or "unnamed"
        logger.info(f"Parsing uploaded file '{filename}' ({len(content)} bytes)...")
        try:
            text = extract_text(filename, content)
        except ValueError as exc:
            logger.error(f"Failed to extract text from file '{filename}': {exc}")
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        # Extract images & diagrams from PDF and DOCX files
        if filename.lower().endswith(".pdf"):
            images = extract_images_from_pdf(content, max_pages=10)
            logger.info(f"🖼️ Extracted {len(images)} images/diagrams from PDF '{filename}'.")
            extracted_pdf_images.extend(images)
        elif filename.lower().endswith(".docx"):
            images = extract_images_from_docx(content)
            logger.info(f"🖼️ Extracted {len(images)} images/diagrams from DOCX '{filename}'.")
            extracted_pdf_images.extend(images)

        chunks = chunk_text(text)
        added = kb.add_chunks(chunks, source=filename)
        logger.info(f"File '{filename}' chunked into {added} vectors in ChromaDB collection '{kb.collection_name}'.")
        total_chunks += added
        summaries.append(KnowledgeFileSummary(filename=filename, chunk_count=added))

    if extracted_pdf_images:
        KB_IMAGE_STORE[kb_id] = extracted_pdf_images

    logger.info(f"Knowledge Base ingestion complete: kb_id='{kb_id}', total_chunks={total_chunks}, extracted_images={len(extracted_pdf_images)}")
    return KnowledgeUploadResponse(kb_id=kb_id, files=summaries, total_chunks=total_chunks)


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
