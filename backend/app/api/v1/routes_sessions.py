import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger("gdocs.routes_sessions")
router = APIRouter(prefix="/sessions", tags=["sessions"])

from app.db.database import get_db
from app.db.models import WorkspaceSessionModel


class SessionDocPayload(BaseModel):
    id: str = Field(alias="_id", default="")
    id_number: int = Field(default=101)
    display_id: str = Field(default="#101")
    session_id: str
    document_id: str
    title: str
    created_at: str
    updated_at: str
    provider: str | None = None
    model: str | None = None
    kb_id: str | None = None
    kb_files: list[dict[str, Any]] = Field(default_factory=list)
    procurement_doc_type: str = "RFP"
    prompt: str = ""
    segments: list[dict[str, Any]] = Field(default_factory=list)
    prompt_log: list[dict[str, Any]] = Field(default_factory=list)
    style_config: dict[str, Any] = Field(default_factory=dict)
    page_layout_size: str = "A4"
    doc_status: str = "DRAFT"

    class Config:
        populate_by_name = True


@router.get("")
async def list_sessions(db: Session = Depends(get_db)):
    """Retrieve all saved workspace sessions from PostgreSQL."""
    rows = db.query(WorkspaceSessionModel).all()
    sessions = []
    for row in rows:
        doc = dict(row.payload) if row.payload else {}
        doc.setdefault("session_id", row.session_id)
        doc.setdefault("updated_at", row.updated_at or "")
        sessions.append(doc)
    sessions.sort(key=lambda s: s.get("updated_at", ""), reverse=True)
    return {"sessions": sessions, "count": len(sessions)}


@router.post("")
async def save_session(payload: SessionDocPayload, db: Session = Depends(get_db)):
    """Save or update a workspace session in PostgreSQL."""
    doc_dict = payload.model_dump(by_alias=True)
    if not doc_dict.get("_id"):
        doc_dict["_id"] = f"session_{payload.id_number}"

    existing = db.query(WorkspaceSessionModel).filter(
        WorkspaceSessionModel.session_id == payload.session_id
    ).first()

    if existing:
        existing.document_id = payload.document_id
        existing.id_number = str(payload.id_number)
        existing.display_id = payload.display_id
        existing.title = payload.title
        existing.updated_at = payload.updated_at
        existing.payload = doc_dict
    else:
        db_session = WorkspaceSessionModel(
            session_id=payload.session_id,
            document_id=payload.document_id,
            id_number=str(payload.id_number),
            display_id=payload.display_id,
            title=payload.title,
            created_at=payload.created_at,
            updated_at=payload.updated_at,
            payload=doc_dict,
        )
        db.add(db_session)

    db.commit()
    logger.info(f"Saved session '{payload.display_id}' ({payload.title}) to PostgreSQL.")
    return {"status": "saved", "session": doc_dict}


@router.get("/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Fetch a specific workspace session by ID from PostgreSQL."""
    row = db.query(WorkspaceSessionModel).filter(
        WorkspaceSessionModel.session_id == session_id
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    doc = dict(row.payload) if row.payload else {}
    doc.setdefault("session_id", row.session_id)
    return doc


@router.delete("/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a workspace session by ID from PostgreSQL."""
    row = db.query(WorkspaceSessionModel).filter(
        WorkspaceSessionModel.session_id == session_id
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    db.delete(row)
    db.commit()
    return {"status": "deleted", "session_id": session_id}
