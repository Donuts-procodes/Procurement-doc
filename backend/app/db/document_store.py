from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

from app.services.rag_pipeline import GeneratedDocument
from app.db.database import SessionLocal
from app.db.models import DocumentModel, AuditLogModel


class DocumentStatus(str, Enum):
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    SENT = "SENT"


class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    actor: str = "AI Assistant"
    action: str
    timestamp: float = Field(default_factory=time.time)
    section_id: str | None = None


class ExtendedDocument(GeneratedDocument):
    status: DocumentStatus = DocumentStatus.DRAFT
    approvers: list[str] = Field(default_factory=list)
    audit_log: list[AuditEntry] = Field(default_factory=list)


class DocumentStore:
    def save(self, document: GeneratedDocument | ExtendedDocument) -> ExtendedDocument:
        db = SessionLocal()
        try:
            db_doc = db.query(DocumentModel).filter(DocumentModel.document_id == document.document_id).first()
            if not db_doc:
                db_doc = DocumentModel(
                    document_id=document.document_id,
                    status=DocumentStatus.DRAFT.value if not isinstance(document, ExtendedDocument) else document.status.value,
                    lexical_state=document.lexical_state,
                    page_titles=document.page_titles,
                    approvers=[] if not isinstance(document, ExtendedDocument) else document.approvers,
                )
                audit_log = AuditLogModel(
                    actor="System",
                    action="Document created"
                )
                db_doc.audit_logs.append(audit_log)
                db.add(db_doc)
            else:
                db_doc.lexical_state = document.lexical_state
                db_doc.page_titles = document.page_titles
                if isinstance(document, ExtendedDocument):
                    db_doc.status = document.status.value
                    db_doc.approvers = document.approvers

            db.commit()
            db.refresh(db_doc)
            
            return self._to_pydantic(db_doc)
        finally:
            db.close()

    def get(self, document_id: str) -> ExtendedDocument:
        db = SessionLocal()
        try:
            db_doc = db.query(DocumentModel).filter(DocumentModel.document_id == document_id).first()
            if not db_doc:
                raise KeyError(f"Unknown document_id: {document_id}")
            return self._to_pydantic(db_doc)
        finally:
            db.close()

    def update_status(self, document_id: str, new_status: DocumentStatus, actor: str = "User") -> ExtendedDocument:
        db = SessionLocal()
        try:
            db_doc = db.query(DocumentModel).filter(DocumentModel.document_id == document_id).first()
            if not db_doc:
                raise KeyError(f"Unknown document_id: {document_id}")
            
            old_status = db_doc.status
            db_doc.status = new_status.value
            
            audit_log = AuditLogModel(
                actor=actor,
                action=f"Status changed from {old_status} to {new_status.value}"
            )
            db_doc.audit_logs.append(audit_log)
            db.commit()
            db.refresh(db_doc)
            
            return self._to_pydantic(db_doc)
        finally:
            db.close()

    def _to_pydantic(self, db_doc: DocumentModel) -> ExtendedDocument:
        return ExtendedDocument(
            document_id=db_doc.document_id,
            lexical_state=db_doc.lexical_state,
            page_titles=db_doc.page_titles,
            status=DocumentStatus(db_doc.status),
            approvers=db_doc.approvers,
            audit_log=[
                AuditEntry(
                    id=log.id,
                    actor=log.actor,
                    action=log.action,
                    timestamp=log.timestamp,
                    section_id=log.section_id
                ) for log in db_doc.audit_logs
            ]
        )


document_store = DocumentStore()
