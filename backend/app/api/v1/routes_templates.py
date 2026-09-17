from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.s3_template_service import (
    DynamicTemplateManifest,
    get_template_preview,
    list_all_dynamic_templates,
    register_custom_template,
)

logger = logging.getLogger("gdocs.routes_templates")

router = APIRouter(prefix="/templates", tags=["templates"])


class TemplatePreviewResponse(BaseModel):
    template_id: str
    title: str
    category: str
    tone: str
    tone_description: str
    sections: list[dict[str, Any]]
    preview_image_url: str | None = None
    preview_ast: dict[str, Any] | None = None
    is_custom: bool = False
    source: str = "builtin"


@router.get("", response_model=list[DynamicTemplateManifest])
async def list_templates() -> list[DynamicTemplateManifest]:
    """Returns all available document templates discovered from S3, local storage, and built-in presets."""
    logger.info("GET /api/v1/templates: Listing dynamic templates...")
    return list_all_dynamic_templates()


@router.get("/{template_id}/preview", response_model=TemplatePreviewResponse)
async def fetch_template_preview(template_id: str) -> TemplatePreviewResponse:
    """Returns dynamic preview information and dummy AST nodes for the hover window."""
    logger.info(f"GET /api/v1/templates/{template_id}/preview: Fetching preview...")
    preview = get_template_preview(template_id)
    if not preview:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found.")
    return TemplatePreviewResponse(**preview)


@router.post("/upload", response_model=DynamicTemplateManifest)
async def upload_custom_template(
    title: str = Form(...),
    category: str = Form("RFP"),
    description: str = Form(""),
    tone: str = Form("Formal & Evaluative"),
    file: UploadFile | None = File(None),
) -> DynamicTemplateManifest:
    """
    Upload a custom document template (.docx / .md) into S3 / storage,
    reserving space for enterprise document assets.
    """
    logger.info(f"POST /api/v1/templates/upload: Uploading custom template '{title}'...")
    file_bytes = None
    filename = None
    if file:
        file_bytes = await file.read()
        filename = file.filename

    manifest_data = {
        "title": title,
        "category": category,
        "description": description,
        "tone": tone,
        "sections": [
            {"title": "Executive Summary", "section_type": "prose", "guidance": "High-level background."},
            {"title": "Scope of Work", "section_type": "prose", "guidance": "Deliverables & requirements."},
            {"title": "Pricing & Costs", "section_type": "line_items", "guidance": "Itemized cost breakdown."},
            {"title": "Terms & Conditions", "section_type": "clause", "guidance": "Standard clauses."},
        ],
    }

    return register_custom_template(manifest_data, file_bytes, filename)
