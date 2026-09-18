from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Sequence
from app.schemas.dynamic_template_schemas import (
    CardAspectRatio,
    DynamicParsedSection,
    DynamicVisualManifest,
    TemplateCategoryEnum,
)
from app.services.doc_analyzer import DocAnalyzer
from app.services.theme_synthesizer import ThemeSynthesizer

logger = logging.getLogger("gdocs.scanner")


def resolve_templates_storage_dir() -> str:
    """Dynamically resolves the storage directory across development and production environments."""
    env_dir = os.environ.get("LOCAL_TEMPLATES_DIR")
    if env_dir and os.path.exists(env_dir):
        return env_dir

    candidates = [
        os.path.abspath("./templates_storage"),
        os.path.abspath("../templates_storage"),
        os.path.abspath("../../templates_storage"),
        os.path.join(Path(__file__).resolve().parent.parent.parent.parent, "templates_storage"),
        r"C:\Users\Lenovo\work\prf\Procurement-doc\templates_storage",
    ]

    for cand in candidates:
        if os.path.exists(cand) and os.path.isdir(cand):
            return cand

    # Fallback to local
    fallback = os.path.abspath("./templates_storage")
    os.makedirs(fallback, exist_ok=True)
    return fallback


LOCAL_TEMPLATES_DIR = resolve_templates_storage_dir()


def generate_tiptap_preview_ast(title: str, sections: Sequence[DynamicParsedSection]) -> dict[str, Any]:
    """Generates a structured ProseMirror/Tiptap compatible dummy preview document."""
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
                    "text": "Automated architectural preview generated dynamically from document analysis.",
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
                            {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Est. Rate"}]}]},
                        ],
                    },
                    {
                        "type": "tableRow",
                        "content": [
                            {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "SRV-01"}]}]},
                            {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Enterprise Implementation"}]}]},
                            {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "1"}]}]},
                            {"type": "tableCell", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "$45,000.00"}]}]},
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
                            {"type": "text", "text": "💳 Milestone Allocation: 30% Mobilization | 40% Delivery | 30% Final Sign-off."}
                        ],
                    }
                ],
            })
        elif sec.section_type == "clause":
            content_nodes.append({
                "type": "paragraph",
                "attrs": {"class": "clause-box"},
                "content": [
                    {"type": "text", "marks": [{"type": "bold"}], "text": "🔒 Standard Regulatory Clause: "},
                    {"type": "text", "text": sec.guidance or "Strict compliance with statutory warranties, confidentiality, and SLAs."},
                ],
            })
        else:
            content_nodes.append({
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": f"{sec.guidance or 'Operational and technical deliverables under this section.'}",
                    }
                ],
            })

    return {"type": "doc", "content": content_nodes}


class DynamicTemplateScanner:
    """
    Scans storage directories and dynamically synthesizes visual template cards.
    Any dropped file (.docx, .md, .txt) immediately becomes a live interactive template.
    """
    _cache: dict[str, tuple[float, DynamicVisualManifest]] = {}

    @classmethod
    def get_starter_presets(cls) -> list[DynamicVisualManifest]:
        """Provides dynamic starter presets matching the rich Canva/Pinterest design."""
        return [
            # Blank Document Canvas Tile
            DynamicVisualManifest(
                id="blank_document",
                title="Blank document",
                subtitle="Start from a clean slate",
                category=TemplateCategoryEnum.ALL,
                aspect_ratio=CardAspectRatio.SQUARE,
                is_blank_doc=True,
                file_name="",
                file_path="",
                source="system",
                theme=ThemeSynthesizer.generate_theme("blank_document", TemplateCategoryEnum.BUSINESS),
                sections=[DynamicParsedSection(title="Section 1", section_type="prose", guidance="Custom draft.")],
                preview_ast=generate_tiptap_preview_ast("Blank Document", []),
            ),
            # Marketing Proposal 2029 (Tall Poster Gradient)
            DynamicVisualManifest(
                id="marketing_proposal_2029",
                title="MARKETING PROPOSAL 2029",
                subtitle="High-impact creative agency outreach",
                category=TemplateCategoryEnum.MARKETING,
                aspect_ratio=CardAspectRatio.TALL_POSTER,
                source="builtin",
                is_custom=False,
                file_name="marketing_proposal_2029.md",
                file_path="presets/marketing_proposal_2029.md",
                theme=ThemeSynthesizer.generate_theme("marketing_proposal_2029", TemplateCategoryEnum.MARKETING),
                sections=[
                    DynamicParsedSection(title="Campaign Vision & Objectives", section_type="prose", guidance="Core messaging and goals."),
                    DynamicParsedSection(title="Audience Segmentation & Reach", section_type="prose", guidance="Target demographics and channels."),
                    DynamicParsedSection(title="Media Spend & Budget Allocation", section_type="line_items", guidance="Itemized budget breakdown."),
                ],
                tags=["Marketing", "Proposal", "Creative"],
                preview_ast=generate_tiptap_preview_ast(
                    "MARKETING PROPOSAL 2029",
                    [
                        DynamicParsedSection(title="Campaign Vision & Objectives", section_type="prose", guidance="Core messaging and goals."),
                        DynamicParsedSection(title="Media Spend & Budget Allocation", section_type="line_items", guidance="Itemized budget breakdown."),
                    ],
                ),
            ),
            # 2025 Business Conference (Blue Corporate Flyer)
            DynamicVisualManifest(
                id="business_conference_2025",
                title="2025 BUSINESS CONFERENCE",
                subtitle="Executive briefing & speaker agenda",
                category=TemplateCategoryEnum.BUSINESS,
                aspect_ratio=CardAspectRatio.PORTRAIT_A4,
                source="builtin",
                is_custom=False,
                file_name="business_conference_2025.md",
                file_path="presets/business_conference_2025.md",
                theme=ThemeSynthesizer.generate_theme("business_conference_2025", TemplateCategoryEnum.BUSINESS),
                sections=[
                    DynamicParsedSection(title="Executive Summary", section_type="prose", guidance="Conference overview."),
                    DynamicParsedSection(title="Discussion & Insight Topics", section_type="prose", guidance="Keynotes and panels."),
                    DynamicParsedSection(title="Exclusive Speakers & Bio", section_type="prose", guidance="Speaker credentials."),
                    DynamicParsedSection(title="Registration & Tier Pricing", section_type="line_items", guidance="Ticket tiers and packages."),
                ],
                tags=["Business", "Conference", "Agenda"],
                preview_ast=generate_tiptap_preview_ast(
                    "2025 BUSINESS CONFERENCE",
                    [
                        DynamicParsedSection(title="Executive Summary", section_type="prose", guidance="Conference overview."),
                        DynamicParsedSection(title="Registration & Tier Pricing", section_type="line_items", guidance="Ticket tiers and packages."),
                    ],
                ),
            ),
            # Work Together (Team Collaboration Card)
            DynamicVisualManifest(
                id="work_together_handbook",
                title="Work Together",
                subtitle="Building Strong Team Relationships",
                category=TemplateCategoryEnum.EDUCATION,
                aspect_ratio=CardAspectRatio.PORTRAIT_A4,
                source="builtin",
                is_custom=False,
                file_name="work_together_handbook.md",
                file_path="presets/work_together_handbook.md",
                theme=ThemeSynthesizer.generate_theme("work_together_handbook", TemplateCategoryEnum.EDUCATION),
                sections=[
                    DynamicParsedSection(title="Foster Communication", section_type="prose", guidance="Establish clear channels and feedback loops."),
                    DynamicParsedSection(title="Listen to Different Perspectives", section_type="prose", guidance="Inclusivity and safe collaboration space."),
                ],
                tags=["Education", "Culture", "Handbook"],
                preview_ast=generate_tiptap_preview_ast(
                    "Work Together",
                    [
                        DynamicParsedSection(title="Foster Communication", section_type="prose", guidance="Establish clear channels."),
                    ],
                ),
            ),
            # The Caseton / Product Release
            DynamicVisualManifest(
                id="the_caseton_product_brief",
                title="The Caseton",
                subtitle="Introducing our latest app",
                category=TemplateCategoryEnum.REPORTS_ANALYSIS,
                aspect_ratio=CardAspectRatio.PORTRAIT_A4,
                source="builtin",
                is_custom=False,
                file_name="the_caseton_product_brief.md",
                file_path="presets/the_caseton_product_brief.md",
                theme=ThemeSynthesizer.generate_theme("the_caseton_product_brief", TemplateCategoryEnum.REPORTS_ANALYSIS),
                sections=[
                    DynamicParsedSection(title="App Capabilities & Overview", section_type="prose", guidance="High-level product features."),
                    DynamicParsedSection(title="Performance Metrics & Adoption", section_type="line_items", guidance="Series chart comparison metrics."),
                ],
                tags=["Report", "Launch", "Product"],
                preview_ast=generate_tiptap_preview_ast(
                    "The Caseton",
                    [
                        DynamicParsedSection(title="App Capabilities & Overview", section_type="prose", guidance="Product features."),
                    ],
                ),
            ),
            # Social Media Analytics
            DynamicVisualManifest(
                id="social_media_analytics",
                title="social media analytics",
                subtitle="Performance Dashboard",
                category=TemplateCategoryEnum.REPORTS_ANALYSIS,
                aspect_ratio=CardAspectRatio.LANDSCAPE_CARD,
                source="builtin",
                is_custom=False,
                file_name="social_media_analytics.md",
                file_path="presets/social_media_analytics.md",
                theme=ThemeSynthesizer.generate_theme("social_media_analytics", TemplateCategoryEnum.REPORTS_ANALYSIS),
                sections=[
                    DynamicParsedSection(title="Executive Summary", section_type="prose", guidance="Measurement and evaluation overview."),
                    DynamicParsedSection(title="Engagement & Conversion KPIs", section_type="line_items", guidance="Key performance indicators."),
                ],
                tags=["Analytics", "Dashboard", "Marketing"],
                preview_ast=generate_tiptap_preview_ast(
                    "social media analytics",
                    [
                        DynamicParsedSection(title="Engagement & Conversion KPIs", section_type="line_items", guidance="Key performance indicators."),
                    ],
                ),
            ),
        ]

    @classmethod
    def scan_storage_directory(cls) -> list[DynamicVisualManifest]:
        """Walks storage directory, parses newly added/updated files, and returns manifests."""
        storage_dir = resolve_templates_storage_dir()
        manifests: list[DynamicVisualManifest] = cls.get_starter_presets()
        seen_ids = {m.id for m in manifests}

        # Recursively scan storage directory for document files and manifest.json files
        for root, _, files in os.walk(storage_dir):
            manifest_json_path = os.path.join(root, "manifest.json")
            dir_metadata: dict[str, Any] = {}
            if os.path.isfile(manifest_json_path):
                try:
                    with open(manifest_json_path, "r", encoding="utf-8") as f:
                        dir_metadata = json.load(f)
                except Exception:
                    pass

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in [".docx", ".md", ".txt"]:
                    continue

                full_path = os.path.join(root, file)
                try:
                    mtime = os.path.getmtime(full_path)
                except OSError:
                    continue

                # Return cached manifest if file has not changed
                if full_path in cls._cache:
                    cached_mtime, cached_manifest = cls._cache[full_path]
                    if cached_mtime == mtime:
                        if cached_manifest.id not in seen_ids:
                            manifests.append(cached_manifest)
                            seen_ids.add(cached_manifest.id)
                        continue

                # Parse newly dropped or modified file
                try:
                    manifest = cls._parse_file_to_manifest(full_path, file, dir_metadata)
                    cls._cache[full_path] = (mtime, manifest)
                    if manifest.id not in seen_ids:
                        manifests.append(manifest)
                        seen_ids.add(manifest.id)
                    logger.info(f"Dynamic Template Loaded: '{manifest.title}' from {file}")
                except Exception as exc:
                    logger.error(f"Error parsing dynamic template file {full_path}: {exc}")

        # 3. Recursively scan S3 bucket if S3_TEMPLATES_BUCKET is configured
        s3_manifests = cls.scan_s3_bucket()
        for sm in s3_manifests:
            if sm.id not in seen_ids:
                manifests.append(sm)
                seen_ids.add(sm.id)

        return manifests

    @classmethod
    def scan_s3_bucket(cls) -> list[DynamicVisualManifest]:
        """Scans S3/MinIO bucket for .docx, .md files and manifests if configured."""
        bucket = os.environ.get("S3_TEMPLATES_BUCKET")
        if not bucket or not os.environ.get("AWS_ACCESS_KEY_ID"):
            return []

        s3_manifests: list[DynamicVisualManifest] = []
        try:
            import boto3
            from botocore.config import Config
            s3 = boto3.client(
                "s3",
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                region_name=os.environ.get("AWS_REGION", "us-east-1"),
                endpoint_url=os.environ.get("S3_ENDPOINT_URL"),  # MinIO compatibility
                config=Config(signature_version="s3v4"),
            )
            prefix = os.environ.get("S3_TEMPLATES_PREFIX", "templates/")
            resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
            for item in resp.get("Contents", []):
                key = item.get("Key", "")
                ext = os.path.splitext(key)[1].lower()
                if ext not in [".docx", ".md", ".txt"]:
                    continue

                filename = os.path.basename(key)
                obj = s3.get_object(Bucket=bucket, Key=key)
                file_bytes = obj["Body"].read()

                doc_id = os.path.splitext(filename)[0].lower().replace(" ", "_").replace("(", "").replace(")", "")
                if ext == ".docx":
                    doc_title, doc_subtitle, sections = DocAnalyzer.parse_docx_bytes(file_bytes)
                else:
                    text = file_bytes.decode("utf-8", errors="ignore")
                    doc_title, doc_subtitle, sections = DocAnalyzer.parse_markdown_text(text)

                category = ThemeSynthesizer.infer_category(doc_title, " ".join(s.guidance for s in sections))
                aspect_ratio = ThemeSynthesizer.infer_aspect_ratio(len(sections), category)
                theme = ThemeSynthesizer.generate_theme(doc_id, category)

                s3_manifests.append(
                    DynamicVisualManifest(
                        id=doc_id,
                        title=doc_title,
                        subtitle=doc_subtitle,
                        category=category,
                        aspect_ratio=aspect_ratio,
                        theme=theme,
                        file_name=filename,
                        file_path=f"s3://{bucket}/{key}",
                        source="s3_bucket",
                        is_custom=True,
                        sections=sections,
                        tags=["S3 Bucket", category.value.replace("_", " ").title(), f"{len(sections)} Sections"],
                        preview_ast=generate_tiptap_preview_ast(doc_title, sections),
                    )
                )
        except Exception as exc:
            logger.warning(f"S3 template bucket scan skipped ({exc})")

        return s3_manifests

    @classmethod
    def _parse_file_to_manifest(cls, full_path: str, filename: str, metadata_override: dict[str, Any] | None = None) -> DynamicVisualManifest:
        """Parses a specific file binary into a complete Visual Template Manifest."""
        meta = metadata_override or {}
        with open(full_path, "rb") as f:
            file_bytes = f.read()

        doc_id = meta.get("id") or os.path.splitext(filename)[0].lower().replace(" ", "_").replace("(", "").replace(")", "")
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".docx":
            parsed_title, parsed_subtitle, parsed_sections = DocAnalyzer.parse_docx_bytes(file_bytes)
        else:
            text = file_bytes.decode("utf-8", errors="ignore")
            parsed_title, parsed_subtitle, parsed_sections = DocAnalyzer.parse_markdown_text(text)

        # Merge with manifest.json if present
        doc_title = meta.get("title") or parsed_title or filename
        doc_subtitle = meta.get("description") or parsed_subtitle or f"Auto-detected {len(parsed_sections)} sections"
        
        # Sections
        sections = parsed_sections
        if meta.get("sections") and not parsed_sections:
            sections = [
                DynamicParsedSection(
                    title=s.get("title", "Section"),
                    section_type=s.get("section_type", "prose"),
                    guidance=s.get("guidance", ""),
                    estimated_pages=s.get("estimated_pages", 1.0),
                )
                for s in meta.get("sections", [])
            ]

        # Category and Theme
        if meta.get("category"):
            try:
                category = TemplateCategoryEnum(meta["category"].lower())
            except ValueError:
                category = ThemeSynthesizer.infer_category(doc_title, " ".join(s.guidance for s in sections))
        else:
            category = ThemeSynthesizer.infer_category(doc_title, " ".join(s.guidance for s in sections))

        aspect_ratio = ThemeSynthesizer.infer_aspect_ratio(len(sections), category)
        theme = ThemeSynthesizer.generate_theme(doc_id, category)

        return DynamicVisualManifest(
            id=doc_id,
            title=doc_title,
            subtitle=doc_subtitle,
            category=category,
            aspect_ratio=aspect_ratio,
            theme=theme,
            file_name=filename,
            file_path=full_path,
            source="file_storage",
            is_custom=True,
            sections=sections,
            tags=[category.value.replace("_", " ").title(), f"{len(sections)} Sections"],
            preview_ast=generate_tiptap_preview_ast(doc_title, sections),
        )

    @classmethod
    def get_filtered_gallery(
        cls,
        category: TemplateCategoryEnum = TemplateCategoryEnum.ALL,
        search_query: str | None = None,
    ) -> Sequence[DynamicVisualManifest]:
        """Filters dynamic templates according to the active UI tab and search box."""
        templates = cls.scan_storage_directory()
        query = (search_query or "").strip().lower()

        filtered: list[DynamicVisualManifest] = []
        for tmpl in templates:
            if category != TemplateCategoryEnum.ALL:
                if category == TemplateCategoryEnum.MY_DOCS and not tmpl.is_custom:
                    continue
                elif category != TemplateCategoryEnum.MY_DOCS and tmpl.category != category and not tmpl.is_blank_doc:
                    continue

            if query:
                corpus = f"{tmpl.title} {tmpl.subtitle} {' '.join(tmpl.tags)}".lower()
                if query not in corpus:
                    continue

            filtered.append(tmpl)

        return filtered
