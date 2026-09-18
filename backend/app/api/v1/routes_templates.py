from __future__ import annotations

import logging
import os
from typing import Any
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.schemas.dynamic_template_schemas import (
    DynamicGalleryResponse,
    DynamicVisualManifest,
    TemplateCategoryEnum,
)
from app.services.dynamic_template_scanner import (
    DynamicTemplateScanner,
    LOCAL_TEMPLATES_DIR,
)

logger = logging.getLogger("gdocs.routes_templates")
router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/gallery", response_model=DynamicGalleryResponse)
async def get_dynamic_gallery(
    category: TemplateCategoryEnum = Query(default=TemplateCategoryEnum.ALL, description="Active gallery tab filter"),
    search: str | None = Query(default=None, description="Optional search filter"),
) -> DynamicGalleryResponse:
    """
    Returns dynamically parsed visual templates from storage files (.docx, .md) with zero hardcoding.
    """
    logger.info(f"GET /api/v1/templates/gallery - Category: '{category.value}', Search: '{search}'")

    category_tabs = [
        {"id": "my_docs", "label": "My Docs"},
        {"id": "all", "label": "All Templates"},
        {"id": "education", "label": "Education"},
        {"id": "business", "label": "Business"},
        {"id": "reports_analysis", "label": "Reports & Analysis"},
        {"id": "marketing", "label": "Marketing"},
        {"id": "career_portfolio", "label": "Career & Portfolio"},
        {"id": "legal_forms", "label": "Legal & Forms"},
        {"id": "custom", "label": "Custom"},
    ]

    templates = DynamicTemplateScanner.get_filtered_gallery(category=category, search_query=search)

    return DynamicGalleryResponse(
        categories=category_tabs,
        total_count=len(templates),
        templates=templates,
    )


@router.get("/{template_id}/preview")
async def get_template_preview(template_id: str) -> dict[str, Any]:
    """Returns dynamic preview AST and section breakdown for the hover modal."""
    templates = DynamicTemplateScanner.scan_storage_directory()
    for t in templates:
        if t.id == template_id:
            return {
                "template_id": t.id,
                "title": t.title,
                "subtitle": t.subtitle,
                "category": t.category.value,
                "theme": t.theme.model_dump(),
                "sections": [s.model_dump() for s in t.sections],
                "preview_ast": t.preview_ast,
                "is_custom": t.is_custom,
                "source": t.source,
            }
    raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found.")


@router.post("/upload-doc", response_model=DynamicVisualManifest)
async def upload_document_as_template(
    file: UploadFile = File(..., description="Raw .docx or .md template file"),
) -> DynamicVisualManifest:
    """
    Saves a newly dropped or uploaded doc file directly into templates_storage and immediately
    returns its auto-parsed visual manifest for live rendering in the frontend gallery.
    """
    filename = file.filename or "uploaded_template.docx"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".docx", ".md", ".txt"]:
        raise HTTPException(status_code=400, detail="Only .docx, .md, and .txt files are supported.")

    os.makedirs(LOCAL_TEMPLATES_DIR, exist_ok=True)
    target_path = os.path.join(LOCAL_TEMPLATES_DIR, filename)

    content = await file.read()
    with open(target_path, "wb") as f:
        f.write(content)

    logger.info(f"Uploaded and saved new dynamic template file: {target_path}")

    # Trigger hot-scan and return the new manifest
    all_manifests = DynamicTemplateScanner.scan_storage_directory()
    for m in all_manifests:
        if m.file_path == target_path or m.file_name == filename:
            return m

    # Fallback to the latest parsed manifest
    return all_manifests[-1]


@router.get("")
async def list_legacy_templates() -> list[dict[str, Any]]:
    """Legacy compatibility endpoint returning dynamic manifests as dicts."""
    manifests = DynamicTemplateScanner.scan_storage_directory()
    return [m.model_dump() for m in manifests]
