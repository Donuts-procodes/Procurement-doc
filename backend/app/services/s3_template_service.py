from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.schemas import ProcurementDocType
from app.services.procurement_templates import PREBUILT_TEMPLATES

logger = logging.getLogger("gdocs.s3_templates")

# S3 Configuration from Environment
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
S3_TEMPLATES_BUCKET = os.environ.get("S3_TEMPLATES_BUCKET")
S3_TEMPLATES_PREFIX = os.environ.get("S3_TEMPLATES_PREFIX", "templates/")

# Local directory fallback storage for templates
LOCAL_TEMPLATES_DIR = os.environ.get("LOCAL_TEMPLATES_DIR", "./templates_storage")


class DynamicSectionModel(BaseModel):
    title: str
    section_type: str = "prose"
    guidance: str = ""
    estimated_pages: float = 1.0


class DynamicTemplateManifest(BaseModel):
    id: str
    category: str = "RFP"
    title: str
    description: str
    tone: str = "Formal & Evaluative"
    tone_description: str = "Professional, structured procurement guidelines."
    icon: str = "📄"
    is_custom: bool = False
    source: str = "builtin"
    sections: list[DynamicSectionModel] = Field(default_factory=list)
    preview_image_url: str | None = None
    preview_ast: dict[str, Any] | None = None
    sample_doc_s3_key: str | None = None


def _get_s3_client():
    """Returns a boto3 S3 client if configured, otherwise None."""
    if not S3_TEMPLATES_BUCKET or not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        return None
    try:
        import boto3
        from botocore.config import Config
        return boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION,
            config=Config(signature_version="s3v4"),
        )
    except Exception as exc:
        logger.warning(f"Failed to initialize S3 client ({exc}). Using local/preset fallback.")
        return None


def generate_dummy_preview_ast(title: str, sections: list[DynamicSectionModel]) -> dict[str, Any]:
    """
    Generates a structured ProseMirror/Tiptap compatible dummy preview document
    to showcase document structure inside the hover window.
    """
    content_nodes: list[dict[str, Any]] = [
        {
            "type": "heading",
            "attrs": {"level": 1},
            "content": [{"type": "text", "text": title}],
        },
        {
            "type": "paragraph",
            "content": [
                {
                    "type": "text",
                    "text": "This is an automated architectural preview generated from the dynamic template manifest. "
                            "Actual document generation will synthesize grounding evidence, primary source citations, and verified calculations.",
                }
            ],
        },
    ]

    for sec in sections:
        content_nodes.append({
            "type": "heading",
            "attrs": {"level": 2},
            "content": [{"type": "text", "text": sec.title}],
        })

        if sec.section_type == "line_items":
            content_nodes.append({
                "type": "table",
                "attrs": {"rows": 3, "cols": 4},
                "content": [
                    {
                        "type": "tableRow",
                        "content": [
                            {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Item / SKU"}]}]},
                            {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Description"}]}]},
                            {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Qty"}]}]},
                            {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Est. Unit Price"}]}]},
                        ],
                    },
                    {
                        "type": "tableRow",
                        "content": [
                            {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "IT-001"}]}]},
                            {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Core Platform License"}]}]},
                            {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "1"}]}]},
                            {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "$25,000.00"}]}]},
                        ],
                    },
                ],
            })
        elif sec.section_type == "payment_schedule":
            content_nodes.append({
                "type": "blockquote",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "💳 Milestone Allocation: 25% Initial Mobilization | 25% Architecture Sign-off | 30% UAT Delivery | 20% Final Acceptance."}
                        ],
                    }
                ],
            })
        elif sec.section_type == "clause":
            content_nodes.append({
                "type": "paragraph",
                "attrs": {"class": "clause-box"},
                "content": [
                    {"type": "text", "marks": [{"type": "bold"}], "text": "🔒 Mandatory Regulatory Clause: "},
                    {"type": "text", "text": sec.guidance or "Strict compliance with statutory warranties, indemnity limitations, and confidentiality."},
                ],
            })
        else:
            content_nodes.append({
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": f"{sec.guidance or 'Detailed technical and operational deliverables under this section.'} "
                                "Drafted with high source fidelity and verifiable provenance citations.",
                    }
                ],
            })

    return {"type": "doc", "content": content_nodes}


def _load_builtin_templates() -> list[DynamicTemplateManifest]:
    """Transforms existing PREBUILT_TEMPLATES into DynamicTemplateManifest models."""
    manifests: list[DynamicTemplateManifest] = []
    for tmpl in PREBUILT_TEMPLATES.values():
        sections = [
            DynamicSectionModel(
                title=s.title,
                section_type=getattr(s, "section_type", "prose"),
                guidance=s.guidance,
                estimated_pages=getattr(s, "page_estimate", 1),
            )
            for s in tmpl.sections
        ]
        manifests.append(
            DynamicTemplateManifest(
                id=tmpl.id,
                category=tmpl.category.value if hasattr(tmpl.category, "value") else str(tmpl.category),
                title=tmpl.title,
                description=tmpl.description,
                tone=tmpl.tone,
                tone_description=tmpl.tone_description,
                icon=tmpl.icon,
                is_custom=False,
                source="builtin",
                sections=sections,
                preview_ast=generate_dummy_preview_ast(tmpl.title, sections),
            )
        )
    return manifests


def _load_local_storage_templates() -> list[DynamicTemplateManifest]:
    """Reads any templates dropped into the local storage folder."""
    manifests: list[DynamicTemplateManifest] = []
    if not os.path.isdir(LOCAL_TEMPLATES_DIR):
        return manifests

    for entry in os.scandir(LOCAL_TEMPLATES_DIR):
        if entry.is_dir():
            manifest_file = os.path.join(entry.path, "manifest.json")
            if os.path.isfile(manifest_file):
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    tmpl = DynamicTemplateManifest(**data)
                    tmpl.source = "local_storage"
                    tmpl.is_custom = True
                    if not tmpl.preview_ast:
                        tmpl.preview_ast = generate_dummy_preview_ast(tmpl.title, tmpl.sections)
                    manifests.append(tmpl)
                except Exception as exc:
                    logger.error(f"Error loading local template manifest from {manifest_file}: {exc}")
    return manifests


def _load_s3_templates() -> list[DynamicTemplateManifest]:
    """Discovers template manifests from configured AWS S3 bucket prefix."""
    s3 = _get_s3_client()
    if not s3:
        return []

    manifests: list[DynamicTemplateManifest] = []
    try:
        response = s3.list_objects_v2(
            Bucket=S3_TEMPLATES_BUCKET,
            Prefix=S3_TEMPLATES_PREFIX,
            Delimiter="/",
        )
        common_prefixes = response.get("CommonPrefixes", [])
        for cp in common_prefixes:
            prefix = cp.get("Prefix", "")
            manifest_key = f"{prefix}manifest.json"
            try:
                obj = s3.get_object(Bucket=S3_TEMPLATES_BUCKET, Key=manifest_key)
                content = obj["Body"].read().decode("utf-8")
                data = json.loads(content)
                tmpl = DynamicTemplateManifest(**data)
                tmpl.source = "s3"
                tmpl.is_custom = True

                # Check if preview image exists in S3, generate presigned URL
                preview_img_key = f"{prefix}preview.png"
                try:
                    s3.head_object(Bucket=S3_TEMPLATES_BUCKET, Key=preview_img_key)
                    tmpl.preview_image_url = s3.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": S3_TEMPLATES_BUCKET, "Key": preview_img_key},
                        ExpiresIn=3600,
                    )
                except Exception:
                    pass

                if not tmpl.preview_ast:
                    tmpl.preview_ast = generate_dummy_preview_ast(tmpl.title, tmpl.sections)
                manifests.append(tmpl)
            except Exception as e:
                logger.warning(f"Could not load S3 manifest at key {manifest_key}: {e}")

    except Exception as exc:
        logger.error(f"Error listing S3 templates from {S3_TEMPLATES_BUCKET}: {exc}")

    return manifests


def list_all_dynamic_templates() -> list[DynamicTemplateManifest]:
    """
    Returns aggregated templates: built-in presets + local storage + S3 dynamic templates.
    Custom/S3 overrides take precedence if IDs match.
    """
    builtin = _load_builtin_templates()
    local = _load_local_storage_templates()
    s3 = _load_s3_templates()

    by_id: dict[str, DynamicTemplateManifest] = {}
    for t in builtin:
        by_id[t.id] = t
    for t in local:
        by_id[t.id] = t
    for t in s3:
        by_id[t.id] = t

    return list(by_id.values())


def get_template_preview(template_id: str) -> dict[str, Any] | None:
    """Returns preview metadata and dummy AST for a specific template."""
    templates = list_all_dynamic_templates()
    for t in templates:
        if t.id == template_id:
            return {
                "template_id": t.id,
                "title": t.title,
                "category": t.category,
                "tone": t.tone,
                "tone_description": t.tone_description,
                "sections": [s.model_dump() for s in t.sections],
                "preview_image_url": t.preview_image_url,
                "preview_ast": t.preview_ast or generate_dummy_preview_ast(t.title, t.sections),
                "is_custom": t.is_custom,
                "source": t.source,
            }
    return None


def register_custom_template(
    manifest_data: dict[str, Any],
    doc_file_bytes: bytes | None = None,
    filename: str | None = None,
) -> DynamicTemplateManifest:
    """
    Stores a new custom doc template and its manifest into S3 (or local storage fallback).
    Leaves dedicated space for the raw document file (.docx / .md).
    """
    template_id = manifest_data.get("id") or f"custom_{uuid.uuid4().hex[:8]}"
    manifest_data["id"] = template_id
    manifest_data["is_custom"] = True

    s3 = _get_s3_client()
    doc_s3_key = None

    if s3 and S3_TEMPLATES_BUCKET:
        prefix = f"{S3_TEMPLATES_PREFIX}{template_id}/"
        if doc_file_bytes and filename:
            doc_s3_key = f"{prefix}{filename}"
            s3.put_object(
                Bucket=S3_TEMPLATES_BUCKET,
                Key=doc_s3_key,
                Body=doc_file_bytes,
            )
            manifest_data["sample_doc_s3_key"] = doc_s3_key

        manifest_data["source"] = "s3"
        s3.put_object(
            Bucket=S3_TEMPLATES_BUCKET,
            Key=f"{prefix}manifest.json",
            Body=json.dumps(manifest_data, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
    else:
        # Local storage fallback
        target_dir = os.path.join(LOCAL_TEMPLATES_DIR, template_id)
        os.makedirs(target_dir, exist_ok=True)

        if doc_file_bytes and filename:
            with open(os.path.join(target_dir, filename), "wb") as f:
                f.write(doc_file_bytes)

        manifest_data["source"] = "local_storage"
        with open(os.path.join(target_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

    return DynamicTemplateManifest(**manifest_data)
