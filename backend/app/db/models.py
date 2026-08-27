from sqlalchemy import Column, String, JSON, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import time
import uuid

from app.db.database import Base

class DocumentModel(Base):
    __tablename__ = "documents"

    document_id = Column(String, primary_key=True, index=True)
    status = Column(String, default="DRAFT")
    lexical_state = Column(JSON, nullable=False)
    page_titles = Column(JSON, nullable=False)
    approvers = Column(JSON, default=[])

    audit_logs = relationship("AuditLogModel", back_populates="document", cascade="all, delete-orphan")


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: uuid.uuid4().hex[:8])
    document_id = Column(String, ForeignKey("documents.document_id"))
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    timestamp = Column(Float, default=time.time)
    section_id = Column(String, nullable=True)

    document = relationship("DocumentModel", back_populates="audit_logs")


class WorkspaceSessionModel(Base):
    __tablename__ = "workspace_sessions"

    session_id = Column(String, primary_key=True, index=True)
    document_id = Column(String, nullable=True)
    id_number = Column(String, default="101")
    display_id = Column(String, default="#101")
    title = Column(String, default="Untitled")
    created_at = Column(String, nullable=True)
    updated_at = Column(String, nullable=True)
    payload = Column(JSON, nullable=False, default={})
