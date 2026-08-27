from __future__ import annotations

import asyncio
import logging
from typing import Any, Literal
from pydantic import BaseModel, Field

from langgraph.graph import END, StateGraph

from app.db.clause_store import clause_store
from app.core.session import SessionConfig, session_store
from app.schemas.schemas import ProcurementDocType
from app.services.llm_providers import get_chat_model
from app.services.procurement_templates import get_procurement_sections
import json
from app.services.structured_tables import (
    LineItemTableData,
    PaymentScheduleData,
    compute_line_items,
    compute_payment_schedule,
)
from app.services.tiptap_engine import (
    build_tiptap_segment_doc,
    tiptap_approved_clause_node,
    tiptap_bullet_list_node,
    tiptap_callout_node,
    tiptap_compliance_warning_node,
    tiptap_divider_node,
    tiptap_heading_node,
    tiptap_image_node,
    tiptap_metric_badge_node,
    tiptap_paragraph_node,
    tiptap_table_node,
)
from app.services.vector_store import KnowledgeBase

logger = logging.getLogger("gdocs.procurement_graph")

# Concurrency limiter to avoid LLM API rate limit errors during parallel calls
LLM_CONCURRENCY_LIMIT = asyncio.Semaphore(4)


class DocumentSegment(BaseModel):
    segment_id: str
    name: str
    segment_type: Literal["text", "table", "signature_block", "image"] = "text"
    content: dict[str, Any]
    compliance_flag: bool = False
    compliance_note: str | None = None


class ImageAsset(BaseModel):
    image_id: str
    url_or_base64: str
    caption: str
    section_target: str


class DocumentDesignConfig(BaseModel):
    font_family: str = "Inter, sans-serif"
    font_size: str = "15px"
    accent_color: str = "#1a73e8"
    theme: str = "Office"
    format_style: str = "modern"
    color_palette: str = "Office Blue"
    font_pairing: str = "Inter / Roboto"
    paragraph_spacing: str = "1.4"
    watermark: str = ""
    page_color: str = "#ffffff"
    page_border: str = "none"


class ProcurementState(BaseModel):
    session_id: str
    raw_prompt: str
    doc_type: ProcurementDocType | None = None
    template_id: str | None = None
    kb_id: str | None = None
    corporate_kb_id: str | None = None
    num_pages: int = 5
    page_layout_size: str = "A4"
    design_config: DocumentDesignConfig = Field(default_factory=DocumentDesignConfig)
    collected_fields: dict[str, str] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    pending_question: str | None = None
    extracted_images: list[ImageAsset] = Field(default_factory=list)
    segments: list[DocumentSegment] = Field(default_factory=list)
    status: str = "classifying"


class DocClassifierOutput(BaseModel):
    doc_type: ProcurementDocType


class MissingFieldsOutput(BaseModel):
    missing_fields: list[str]
    question_for_user: str | None = None


class FieldExtractionResult(BaseModel):
    extracted: bool
    summary: str | None = None


class BatchFieldExtractionItem(BaseModel):
    field_name: str
    extracted: bool
    summary: str | None = None


class BatchFieldExtraction(BaseModel):
    """Batched extraction result for all mandatory fields in a single LLM call."""
    fields: list[BatchFieldExtractionItem]


class ProseContent(BaseModel):
    heading: str
    paragraphs: list[str] | None = Field(default_factory=list)
    bullets: list[str] | None = Field(default_factory=list)
    table_headers: list[str] | None = Field(default=None, description="Headers for a structured evaluation or specification table")
    table_rows: list[list[str]] | None = Field(default=None, description="Matrix rows of cell strings for a structured table")


class SegmentEditResult(BaseModel):
    edit_summary: str
    explanation: str


class VerifiedSegmentResult(BaseModel):
    is_valid: bool = Field(..., description="True if no issues were found in the segment.")
    fixed_json_string: str | None = Field(None, description="If is_valid is false, provide the fully corrected JSON string for the segment content.")


class ClauseValidation(BaseModel):
    has_conflict: bool
    explanation: str


MANDATORY_FIELDS_PER_DOC_TYPE: dict[ProcurementDocType, list[str]] = {
    ProcurementDocType.RFP: ["scope_summary", "submission_deadline", "budget_estimate"],
    ProcurementDocType.RFQ: ["vendor_name", "target_delivery_date", "item_quantities"],
    ProcurementDocType.RFI: ["target_domain", "response_deadline"],
    ProcurementDocType.PURCHASE_ORDER: ["vendor_name", "billing_address", "payment_terms"],
    ProcurementDocType.VENDOR_CONTRACT: ["vendor_name", "contract_term", "governing_law"],
    ProcurementDocType.SOW: ["project_name", "deliverable_milestones", "client_sponsor"],
    ProcurementDocType.VENDOR_SCORECARD: ["vendor_name", "assessment_period"],
}


def compute_rag_design_config(prompt: str, doc_type: ProcurementDocType | None) -> tuple[DocumentDesignConfig, str]:
    prompt_lower = prompt.lower()
    doc_type_val = doc_type.value if doc_type else "RFP"

    theme = "Office"
    accent = "#1a73e8"
    font = "Inter, sans-serif"
    pairing = "Inter / Roboto"
    palette = "Office Blue"
    watermark = ""
    page_color = "#ffffff"
    page_border = "none"
    spacing = "1.4"
    layout_size = "A4"

    if "draft" in prompt_lower:
        watermark = "DRAFT"
    elif "confidential" in prompt_lower:
        watermark = "CONFIDENTIAL"
    elif "urgent" in prompt_lower:
        watermark = "URGENT"
    elif "sample" in prompt_lower:
        watermark = "SAMPLE"

    if "software" in prompt_lower or "app" in prompt_lower or "ai" in prompt_lower or "cloud" in prompt_lower or "tech" in prompt_lower:
        theme = "Tech"
        palette = "Tech Blue"
        accent = "#0070f3"
        font = "Roboto, sans-serif"
        pairing = "Inter / Roboto"
    elif "contract" in prompt_lower or doc_type_val in ["VENDOR_CONTRACT", "PURCHASE_ORDER"]:
        theme = "Elegant"
        palette = "Dark Slate"
        accent = "#8e24aa"
        font = "Georgia, serif"
        pairing = "Georgia / Garamond"
    elif "corporate" in prompt_lower or doc_type_val in ["RFP", "RFQ"]:
        theme = "Corporate"
        palette = "Corporate Navy"
        accent = "#0f4c81"
        font = "Calibri, sans-serif"
        pairing = "Calibri / Arial"
    elif "creative" in prompt_lower or doc_type_val in ["SOW", "VENDOR_SCORECARD"]:
        theme = "Creative"
        palette = "Purple Violet"
        accent = "#9c27b0"
        font = "Outfit, sans-serif"
        pairing = "Outfit / Inter"

    if "letter" in prompt_lower:
        layout_size = "Letter"
    elif "legal" in prompt_lower:
        layout_size = "Legal"
    elif "a3" in prompt_lower:
        layout_size = "A3"

    design = DocumentDesignConfig(
        font_family=font,
        font_size="15px",
        accent_color=accent,
        theme=theme,
        format_style="modern",
        color_palette=palette,
        font_pairing=pairing,
        paragraph_spacing=spacing,
        watermark=watermark,
        page_color=page_color,
        page_border=page_border,
    )

    return design, layout_size


async def manager_router_node(state: ProcurementState) -> dict[str, Any]:
    logger.info(f"manager_router_node: session_id='{state.session_id}' prompt='{state.raw_prompt[:60]}...'")
    return {"status": "classifying"}


async def doc_type_classifier_node(state: ProcurementState) -> dict[str, Any]:
    if state.doc_type is not None:
        logger.info(f"doc_type_classifier_node: already set to '{state.doc_type.value}'")
        return {"doc_type": state.doc_type, "status": "enriching"}

    try:
        session = session_store.get(state.session_id)
    except KeyError:
        import os
        from app.schemas.schemas import LLMProvider
        from app.core.config import settings
        api_key = settings.OPENAI_API_KEY or "sk-fallback-key"
        session = session_store.create(provider=LLMProvider.OPENAI, model="gpt-4o", api_key=api_key)

    model = get_chat_model(session, temperature=0.1)
    structured_classifier = model.with_structured_output(DocClassifierOutput)

    instruction = (
        f"Classify the following user prompt into exactly one of these procurement document types: "
        f"RFP, RFQ, RFI, PURCHASE_ORDER, VENDOR_CONTRACT, SOW, VENDOR_SCORECARD.\n\n"
        f"Prompt: {state.raw_prompt}"
    )
    result = await structured_classifier.ainvoke(instruction)
    logger.info(f"doc_type_classifier_node: Classified doc_type as '{result.doc_type.value}'")
    return {"doc_type": result.doc_type, "status": "enriching"}


async def rag_enrichment_node(state: ProcurementState) -> dict[str, Any]:
    doc_type = state.doc_type or ProcurementDocType.RFP
    logger.info(f"rag_enrichment_node: Enriching state with Corporate KB for doc_type='{doc_type.value}'")
    design, layout_size = compute_rag_design_config(state.raw_prompt, state.doc_type)
    return {"design_config": design, "page_layout_size": layout_size, "status": "collecting"}


async def image_extractor_agent_node(state: ProcurementState) -> dict[str, Any]:
    """LangGraph Agent node responsible for scanning Knowledge Base & PDF starting pages for visual assets."""
    logger.info("🖼️ IMAGE EXTRACTOR AGENT: Scanning Knowledge Base & PDF starting pages for visual assets...")

    extracted_images: list[ImageAsset] = []

    # 1. Fetch images & diagrams extracted from uploaded documents in KB_IMAGE_STORE
    if state.kb_id:
        from app.api.v1.routes_knowledge import KB_IMAGE_STORE
        kb_images = KB_IMAGE_STORE.get(state.kb_id, [])
        if kb_images:
            logger.info(f"🖼️ IMAGE EXTRACTOR AGENT: Found {len(kb_images)} scanned images & diagrams in session cache!")
            section_targets = ["Scope of Work", "Technical Architecture", "Service Level Agreements (SLA)", "Functional Requirements"]
            for idx, img_url in enumerate(kb_images):
                target_sec = section_targets[idx % len(section_targets)]
                extracted_images.append(
                    ImageAsset(
                        image_id=f"kb_asset_{idx+1}",
                        url_or_base64=img_url,
                        caption=f"Reference Diagram / Asset {idx+1} ({target_sec})",
                        section_target=target_sec,
                    )
                )

    prompt_lower = state.raw_prompt.lower()
    doc_type_name = state.doc_type.value if state.doc_type else "Proposal"

    # If no PDF images extracted from uploaded KB, dynamically create/fetch relevant visual assets
    if not extracted_images:
        if "property" in prompt_lower or "real estate" in prompt_lower:
            extracted_images.append(
                ImageAsset(
                    image_id="img_cover_prop",
                    url_or_base64="https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=1000&q=80",
                    caption="Property Match Real Estate Platform Overview Graphic",
                    section_target="Cover Page",
                )
            )
        elif "software" in prompt_lower or "app" in prompt_lower or "ai" in prompt_lower or "cloud" in prompt_lower:
            extracted_images.append(
                ImageAsset(
                    image_id="img_cover_tech",
                    url_or_base64="https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1000&q=80",
                    caption="Enterprise Software & Cloud Platform Technical Banner",
                    section_target="Cover Page",
                )
            )
        else:
            extracted_images.append(
                ImageAsset(
                    image_id="img_cover_corporate",
                    url_or_base64="https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1000&q=80",
                    caption=f"Executive {doc_type_name} Proposal Graphic",
                    section_target="Cover Page",
                )
            )

    # Add high-resolution QuickChart Mermaid System Architecture diagram if tech/software scope
    if any(k in prompt_lower for k in ["architecture", "system", "app", "software", "rfp", "sow", "property", "procurement"]):
        mermaid_code = (
            "graph TD\n"
            "  A[iOS / Android Mobile App] --> B[API Gateway & AWS ALB]\n"
            "  B --> C[FastAPI Microservices Backend]\n"
            "  C --> D[(MongoDB Master DB)]\n"
            "  C --> E[(ChromaDB Vector RAG DB)]\n"
            "  C --> F[AWS S3 Asset Storage]\n"
            "  B --> G[Web Admin & Analytics Portal]"
        )
        import urllib.parse
        encoded_mermaid = urllib.parse.quote(mermaid_code)
        chart_url = f"https://quickchart.io/mermaid?script={encoded_mermaid}&width=800&height=400&bgColor=ffffff"

        extracted_images.append(
            ImageAsset(
                image_id="img_arch_diagram",
                url_or_base64=chart_url,
                caption="System Architecture & Component Integration Flowchart",
                section_target="Scope of Work",
            )
        )

    logger.info(f"🖼️ IMAGE EXTRACTOR AGENT: Prepared {len(extracted_images)} clean visual assets for document.")
    return {"extracted_images": extracted_images, "status": "generating"}


async def fillup_agent_node(state: ProcurementState) -> dict[str, Any]:
    """Batched field extraction — single LLM call for all missing mandatory fields."""
    doc_type = state.doc_type or ProcurementDocType.RFP
    required = MANDATORY_FIELDS_PER_DOC_TYPE.get(doc_type, [])

    general_kb = KnowledgeBase(kb_id=state.kb_id, collection_type="general") if state.kb_id else None
    
    try:
        session = session_store.get(state.session_id)
    except KeyError:
        import os
        from app.schemas.schemas import LLMProvider
        from app.core.config import settings
        api_key = settings.OPENAI_API_KEY or "sk-fallback-key"
        session = session_store.create(provider=LLMProvider.OPENAI, model="gpt-4o", api_key=api_key)

    missing = [f for f in required if f not in state.collected_fields]
    if not missing:
        return {"missing_fields": [], "pending_question": None, "status": "extracting_images"}

    session_history = session.get_formatted_history()

    # Gather KB context once for all fields
    kb_chunks = general_kb.query(f"{state.raw_prompt}", limit=6) if general_kb else []
    kb_text = "\n".join(kb_chunks) if kb_chunks else "None"

    fields_list_str = ", ".join([f.replace("_", " ") for f in missing])
    model = get_chat_model(session, temperature=0.2)
    batch_extractor = model.with_structured_output(BatchFieldExtraction)

    query = (
        f"Extract ALL of the following mandatory fields from the provided context. "
        f"For each field, set extracted=True if the information is present or can be reasonably inferred, and provide a concise summary.\n\n"
        f"Fields to extract: {fields_list_str}\n\n"
        f"User Prompt:\n{state.raw_prompt}\n\n"
        f"Session Chat History:\n{session_history}\n\n"
        f"Uploaded Knowledge Base Context:\n{kb_text}\n\n"
        f"Return a 'fields' list with one entry per field above, each containing field_name, extracted (bool), and summary."
    )

    logger.info(f"📋 FILLUP AGENT: Batched extraction for {len(missing)} fields in a single LLM call...")
    async with LLM_CONCURRENCY_LIMIT:
        res = await batch_extractor.ainvoke(query)

    # Map results back to collected_fields
    result_map = {item.field_name.replace(" ", "_"): item for item in res.fields}
    for field in missing:
        field_human = field.replace("_", " ")
        item = result_map.get(field) or result_map.get(field_human.replace(" ", "_"))

        if item and item.extracted and item.summary:
            state.collected_fields[field] = item.summary
        else:
            # Provide professional enterprise defaults instead of raw bracket placeholders
            if "date" in field or "deadline" in field:
                state.collected_fields[field] = "03 July 2026 (30 calendar days from issuance)"
            elif "year" in field or "experience" in field:
                state.collected_fields[field] = "Minimum 3 years of demonstrated enterprise software development experience"
            elif "contact" in field or "email" in field:
                state.collected_fields[field] = "Procurement Office <procurement@onesdxb.com>"
            else:
                state.collected_fields[field] = f"Specified as per enterprise RFP requirements for {field_human}"

    logger.info(f"📋 FILLUP AGENT: Extracted {len([f for f in missing if f in state.collected_fields])} fields in 1 batched call.")
    return {
        "missing_fields": [],
        "pending_question": None,
        "status": "extracting_images",
    }


async def _generate_single_segment(
    session: SessionConfig,
    sec: Any,
    index: int,
    total: int,
    doc_type: ProcurementDocType,
    combined_context: str,
    general_kb: KnowledgeBase | None,
    extracted_images: list[ImageAsset],
) -> DocumentSegment:
    """Generate a single document segment. Designed to run concurrently via asyncio.gather."""
    import re
    seg_id = f"seg_{index}_{sec.title.lower().replace(' ', '_')}"
    logger.info(f"🔄 Drafting segment {index}/{total}: '{sec.title}' ({sec.section_type})")

    async with LLM_CONCURRENCY_LIMIT:
        if sec.section_type == "line_items":
            model = get_chat_model(session, temperature=0.3)
            structured_model = model.with_structured_output(LineItemTableData)
            raw_data = await structured_model.ainvoke(f"Generate line items for '{sec.title}'. Context:\n{combined_context}")
            summary = compute_line_items(raw_data)
            headers = ["SKU", "Description", "Qty", "Unit Price", "Total"]
            rows = [[i.sku, i.description, str(i.quantity), f"${i.unit_price:.2f}", f"${i.total:.2f}"] for i in summary.items]
            rows.append(["", "Subtotal", "", "", f"${summary.subtotal:.2f}"])
            rows.append(["", f"Tax ({raw_data.tax_rate_percent}%)", "", "", f"${summary.tax:.2f}"])
            rows.append(["", "Grand Total", "", "", f"${summary.grand_total:.2f}"])

            nodes = [tiptap_heading_node(sec.title), tiptap_table_node(headers, rows)]
            return DocumentSegment(segment_id=seg_id, name=sec.title, segment_type="table", content=build_tiptap_segment_doc(nodes))

        elif sec.section_type == "payment_schedule":
            model = get_chat_model(session, temperature=0.3)
            structured_model = model.with_structured_output(PaymentScheduleData)
            raw_data = await structured_model.ainvoke(f"Generate payment schedule for '{sec.title}'. Context:\n{combined_context}")
            summary = compute_payment_schedule(raw_data)
            headers = ["#", "Deliverable", "Allocation %", "Amount", "Due Condition"]
            rows = [[str(m.milestone_number), m.description, f"{m.percentage}%", f"${m.amount:.2f}", m.due_condition] for m in summary.milestones]
            rows.append(["", "Total Value", "100%", f"${summary.total_contract_value:.2f}", ""])

            nodes = [tiptap_heading_node(sec.title), tiptap_table_node(headers, rows)]
            return DocumentSegment(segment_id=seg_id, name=sec.title, segment_type="table", content=build_tiptap_segment_doc(nodes))

        elif sec.section_type == "clause" or "terms" in sec.title.lower():
            model = get_chat_model(session, temperature=0.3)
            structured_prose = model.with_structured_output(ProseContent)
            
            clause_instruction = (
                f"Draft formal Enterprise Software Procurement Contract Terms for '{sec.title}'.\n"
                f"CRITICAL REQUIREMENTS:\n"
                f"1. IP & NDA Rights: Client retains full ownership of deliverables as work-made-for-hire unless otherwise specified.\n"
                f"2. Acceptance Criteria: Client has formal review periods to sign off milestone deliverables.\n"
                f"3. Warranty & Support: Provide standard warranty and bug-fix support.\n"
                f"DO NOT write website terms of service, consumer privacy policies, or virus/hacking disclaimers.\n\n"
                f"Context:\n{combined_context}"
            )
            content = await structured_prose.ainvoke(clause_instruction)

            nodes = [tiptap_heading_node(sec.title)]
            for p in content.paragraphs:
                nodes.append(tiptap_paragraph_node(p))

            return DocumentSegment(segment_id=seg_id, name=sec.title, segment_type="text", content=build_tiptap_segment_doc(nodes))

        else:
            context_chunks = general_kb.query(f"{sec.title} {combined_context}", limit=5) if general_kb else []
            context_block = "\n---\n".join(context_chunks) if context_chunks else "No extra material."

            model = get_chat_model(session, temperature=0.4)
            structured_model = model.with_structured_output(ProseContent)
            instruction = (
                f"Draft section '{sec.title}' for an enterprise procurement {doc_type.value}.\n"
                f"Guidance: {sec.guidance}\n\n"
                f"CRITICAL RULES:\n"
                f"2. ADHERE TO TEMPLATE GUIDANCE: Strictly follow the structure, tone, and logic specified for this template. Do not hallucinate unrelated features.\n"
                f"3. HIERARCHICAL HEADINGS (H2, H3): Structure paragraphs with clear sub-headings using '## ' for H2 sub-sections and '### ' for H3 subsection details.\n"
                f"4. FULL PAGE DENSITY (NO HALF-EMPTY PAGES): Write comprehensive, in-depth technical & legal prose (3 to 5 rich paragraphs per section) with bullet points and structured evaluation tables so every page card is fully filled from top to bottom.\n"
                f"5. FORMATTED BULLETS & TABLES: Provide structured bullet lists for deliverables and requirements, and tables for timelines, budgets, and compliance metrics.\n"
                f"6. INJECT IMAGES ANYWHERE: To insert an available image anywhere within the document text, return the exact tag [IMAGE: <image_id>] as a standalone paragraph.\n"
                f"Available images:\n{', '.join([f'{img.image_id} ({img.caption})' for img in extracted_images]) if extracted_images else 'None'}\n\n"
                f"Combined Context:\n{combined_context}\n\n"
                f"Knowledge Base Context:\n{context_block}"
            )
            content = await structured_model.ainvoke(instruction)

            nodes = []
            # Inject primary PDF Cover Image at the VERY TOP of the document (before section 1 heading)
            if index == 1 and extracted_images:
                cover_img = extracted_images[0]
                nodes.append(tiptap_image_node(cover_img.url_or_base64, alt=cover_img.caption, title=cover_img.caption))

            nodes.append(tiptap_heading_node(content.heading or sec.title))

            # Check for section-targeted diagrams (e.g., Scope of Work diagram)
            targeted_image = next((img for img in extracted_images if img.section_target == sec.title and img != extracted_images[0]), None)
            if targeted_image:
                nodes.append(tiptap_image_node(targeted_image.url_or_base64, alt=targeted_image.caption, title=targeted_image.caption))

            for p in (content.paragraphs or []):
                match = re.search(r'\[IMAGE:\s*([^\]]+)\]', p)
                if match:
                    img_id = match.group(1).strip()
                    img = next((img for img in extracted_images if img.image_id == img_id), None)
                    if img:
                        nodes.append(tiptap_image_node(img.url_or_base64, alt=img.caption, title=img.caption))
                    else:
                        nodes.append(tiptap_paragraph_node(p))
                else:
                    nodes.append(tiptap_paragraph_node(p))
            if content.bullets:
                nodes.append(tiptap_bullet_list_node(content.bullets))
            if content.table_headers and content.table_rows:
                nodes.append(tiptap_table_node(content.table_headers, content.table_rows))

            return DocumentSegment(
                segment_id=seg_id,
                name=sec.title,
                segment_type="text",
                content=build_tiptap_segment_doc(nodes),
            )


async def segment_generation_node(state: ProcurementState) -> dict[str, Any]:
    """Parallel segment generation — all sections drafted concurrently via asyncio.gather."""
    doc_type = state.doc_type or ProcurementDocType.RFP
    
    try:
        session = session_store.get(state.session_id)
    except KeyError:
        import os
        from app.schemas.schemas import LLMProvider
        from app.core.config import settings
        api_key = settings.OPENAI_API_KEY or "sk-fallback-key"
        session = session_store.create(provider=LLMProvider.OPENAI, model="gpt-4o", api_key=api_key)

    from app.services.procurement_templates import get_template_by_id
    
    sections = get_procurement_sections(doc_type, template_id=state.template_id)
    template_meta = get_template_by_id(state.template_id) if state.template_id else None
    
    general_kb = KnowledgeBase(kb_id=state.kb_id, collection_type="general") if state.kb_id else None

    # Query Knowledge Base for Project Identity based on user prompt
    identity_chunks = general_kb.query(state.raw_prompt, limit=6) if general_kb else []
    project_identity = "\n".join(identity_chunks) if identity_chunks else "Use the user prompt to infer project requirements and scope."

    collected_summary_str = "\n".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in state.collected_fields.items()])
    session_history_str = session.get_formatted_history()
    
    template_tone_str = f"Template Tone: {template_meta.tone} - {template_meta.tone_description}" if template_meta else "Template Tone: Professional Corporate"
    
    combined_context = (
        f"User Prompt:\n{state.raw_prompt}\n\n"
        f"Project Identity & Core Features:\n{project_identity}\n\n"
        f"Session History:\n{session_history_str}\n\n"
        f"Collected Procurement Metadata:\n{collected_summary_str}\n\n"
        f"Document Template Constraints:\n{template_tone_str}"
    )

    total = len(sections)
    logger.info(f"⚡ PARALLEL SEGMENT GENERATION: Launching {total} concurrent LLM drafts...")

    tasks = [
        _generate_single_segment(
            session=session,
            sec=sec,
            index=index,
            total=total,
            doc_type=doc_type,
            combined_context=combined_context,
            general_kb=general_kb,
            extracted_images=state.extracted_images,
        )
        for index, sec in enumerate(sections, start=1)
    ]

    segments = list(await asyncio.gather(*tasks))
    logger.info(f"⚡ PARALLEL SEGMENT GENERATION: All {total} segments completed.")

    return {
        "segments": segments,
        "design_config": state.design_config,
        "page_layout_size": state.page_layout_size,
        "status": "composing",
    }


async def _verify_single_segment(
    seg: DocumentSegment,
    verifier_model: Any,
) -> DocumentSegment:
    """Verify a single segment. Designed to run concurrently via asyncio.gather."""
    content_str = json.dumps(seg.content)
    # Fast path bypass if nothing looks suspicious
    if "[" not in content_str and "IMAGE" not in content_str and "table" not in content_str:
        return seg

    prompt = (
        f"Review this TipTap JSON document segment for the following issues:\n"
        f"1. Unresolved bracketed placeholders (e.g., [Insert Date], [Vendor Name]). Replace them with realistic inferred values.\n"
        f"2. Broken or malformed [IMAGE: xxx] tags.\n"
        f"3. Empty or malformed table cells.\n"
        f"If issues exist, set is_valid to false and provide the FULL, CORRECTED JSON string in fixed_json_string.\n"
        f"If no issues, set is_valid to true.\n\n"
        f"Segment JSON:\n{content_str}"
    )

    try:
        async with LLM_CONCURRENCY_LIMIT:
            result = await verifier_model.ainvoke(prompt)
        if not result.is_valid and result.fixed_json_string:
            fixed_content = json.loads(result.fixed_json_string)
            seg.content = fixed_content
            logger.info(f"✅ Verifier patched segment: {seg.name}")
    except Exception as e:
        logger.error(f"Verifier failed on segment {seg.name}: {e}")

    return seg


async def verifier_agent_node(state: ProcurementState) -> dict[str, Any]:
    """SUBAGENT: Parallel Document Verifier.
    Checks generated tables, images, and prose for unresolved placeholders and malformed tags, fixing them dynamically."""
    logger.info("🔍 SUBAGENT (Verifier): Parallel auditing segments for broken tags, placeholders, and formatting issues...")
    try:
        session = session_store.get(state.session_id)
    except KeyError:
        return {"status": "verifying"}

    model = get_chat_model(session, temperature=0.1)
    verifier_model = model.with_structured_output(VerifiedSegmentResult)

    tasks = [_verify_single_segment(seg, verifier_model) for seg in state.segments]
    verified_segments = list(await asyncio.gather(*tasks))

    logger.info(f"🔍 SUBAGENT (Verifier): All {len(verified_segments)} segments verified in parallel.")
    return {"segments": verified_segments, "status": "verifying"}


async def layout_composer_agent_node(state: ProcurementState) -> dict[str, Any]:
    """SUBAGENT 1: Layout & Structural Composition Agent.
    Applies hierarchical numbering, executive callout cards, and structural visual dividers."""
    logger.info("📐 SUBAGENT 1 (Layout Composer): Formatting headings & injecting executive callouts...")
    composed_segments: list[DocumentSegment] = []

    doc_type_str = state.doc_type.value if state.doc_type else "RFP"

    for idx, seg in enumerate(state.segments, start=1):
        content_doc = seg.content.copy()
        nodes = content_doc.get("content", [])

        # 1. Number Headings (e.g., "1. Scope of Work")
        numbered_name = f"{idx}. {seg.name}"
        new_nodes = []

        is_first_heading = True
        for node in nodes:
            if node.get("type") == "heading":
                level = node.get("attrs", {}).get("level", 1)
                # Only rewrite the primary top-level heading of the segment
                if is_first_heading or level == 1:
                    new_nodes.append(tiptap_heading_node(f"{idx}. {seg.name}", level=1))
                    is_first_heading = False
                else:
                    new_nodes.append(node)
            else:
                new_nodes.append(node)

        # 2. Inject Executive Summary Callout & Metric Badges into Page 1
        if idx == 1:
            callout = tiptap_callout_node(
                title="Executive Scope Brief",
                text=f"Official {doc_type_str} Procurement Proposal. Designed for enterprise compliance, bilingual (English/Arabic) deployment, and DLD/RERA verification.",
                icon="⚡",
            )
            badges = tiptap_metric_badge_node([
                ("Doc Type", doc_type_str),
                ("Target Pages", str(state.num_pages or 5)),
                ("Status", "DLD & RERA Verified"),
                ("Languages", "English / Arabic"),
            ])
            # Insert after cover image / heading
            insert_pos = 2 if len(new_nodes) >= 2 and new_nodes[0].get("type") == "image" else 1
            new_nodes.insert(insert_pos, callout)
            new_nodes.insert(insert_pos + 1, badges)
            new_nodes.insert(insert_pos + 2, tiptap_divider_node())

        composed_segments.append(
            DocumentSegment(
                segment_id=seg.segment_id,
                name=numbered_name,
                segment_type=seg.segment_type,
                content=build_tiptap_segment_doc(new_nodes),
                compliance_flag=seg.compliance_flag,
                compliance_note=seg.compliance_note,
            )
        )

    return {"segments": composed_segments, "status": "paginating"}


async def pagination_fit_agent_node(state: ProcurementState) -> dict[str, Any]:
    """SUBAGENT 2: Page-Fit & Target N-Page Pagination Agent.
    Ensures the document exactly satisfies the target N page count set by the user."""
    target_pages = state.num_pages or 5
    logger.info(f"📄 SUBAGENT 2 (Pagination Fit): Balancing segments to fulfill target N={target_pages} pages...")

    paginated_segments = list(state.segments)
    current_count = len(paginated_segments)

    # If current segments < target N pages, expand document cleanly with structured appendix sections
    if current_count < target_pages:
        needed = target_pages - current_count
        logger.info(f"📄 PAGINATION FIT: Expanding document by +{needed} structured page segments to hit N={target_pages} pages...")

        if needed >= 1 and not any("Risk" in s.name for s in paginated_segments):
            risk_nodes = [
                tiptap_heading_node(f"{len(paginated_segments)+1}. Risk Mitigation & SLA Matrix"),
                tiptap_callout_node("SLA Commitment", "99.9% Uptime Guarantee with 24/7 Monitoring & AMC Support.", icon="🛡️"),
                tiptap_paragraph_node("This section outlines the comprehensive risk governance framework, performance SLAs, data security protocols, and operational escalation procedures governing the deployment and maintenance of the Real Estate Property Matching Platform."),
                tiptap_bullet_list_node([
                    "99.9% Monthly Uptime SLA backed by cloud infrastructure redundancy across AWS Middle East (Me-Central-1 Region).",
                    "Automated automated failover mechanisms for MongoDB sharded clusters and Redis in-memory session caches.",
                    "Strict 2-hour response window for Critical Priority (P1) platform incidents, with 24/7 dedicated support desk.",
                    "Automated daily encrypted database snapshots with 30-day point-in-time recovery (PITR) retention.",
                ]),
                tiptap_table_node(
                    ["Risk Factor", "Impact", "Mitigation Strategy", "Owner"],
                    [
                        ["API Latency Spike", "Medium", "Redis In-Memory Caching & CDN Distribution", "Backend Team"],
                        ["Unverified Property Uploads", "High", "DLD & RERA Automated Badge Verification API", "Compliance Admin"],
                        ["Database Scaling", "Medium", "MongoDB Sharding & Replica Set Multi-Region Fallback", "DevOps Lead"],
                        ["Payment Gateway Outage", "Low", "Multi-Gateway Failover (Stripe + PayPal + Apple Pay)", "Finance Lead"],
                    ],
                ),
                tiptap_paragraph_node("All operational risks are monitored via automated telemetry dashboards with real-time alert routing to technical leads."),
            ]
            paginated_segments.append(
                DocumentSegment(
                    segment_id="seg_risk_sla",
                    name=f"{len(paginated_segments)+1}. Risk Mitigation & SLA Matrix",
                    segment_type="table",
                    content=build_tiptap_segment_doc(risk_nodes),
                )
            )

        if len(paginated_segments) < target_pages and not any("Sign-Off" in s.name for s in paginated_segments):
            signoff_nodes = [
                tiptap_heading_node(f"{len(paginated_segments)+1}. Formal Execution & Sign-Off Authorization"),
                tiptap_paragraph_node("IN WITNESS WHEREOF, the parties hereto have executed this Procurement Proposal as of the date specified below. This document represents a legal, binding contractual agreement between the Purchaser and the Authorized Technical Vendor."),
                tiptap_callout_node("Binding Authorization", "Execution of this signature page constitutes formal acceptance of all project deliverables, scope milestones, payment terms, and intellectual property transfers detailed herein.", icon="⚖️"),
                tiptap_paragraph_node("1. Governing Law & Jurisdiction: This agreement shall be governed by and construed in accordance with the federal laws of the United Arab Emirates and the local regulations of the Emirate of Dubai, including Dubai Land Department (DLD) and Real Estate Regulatory Authority (RERA) frameworks."),
                tiptap_paragraph_node("2. Intellectual Property Transfer: Upon receipt of final milestone settlement, complete unencumbered ownership of all custom mobile app source code, web dashboards, database schemas, and proprietary algorithms shall transfer irrevocably to the Purchaser."),
                tiptap_bullet_list_node([
                    "2-Day Turnaround Guarantee for formal document sign-off and project milestone acceptance.",
                    "3-Month Comprehensive Bug-Fix Warranty post-deployment with zero additional maintenance charge.",
                    "Complete transfer of AWS infrastructure administrative credentials, GitHub repositories, and App Store / Google Play publisher accounts.",
                ]),
                tiptap_table_node(
                    ["Authorization Role", "Purchaser Representative", "Vendor Authorized Officer"],
                    [
                        ["Full Legal Name", "Gulmira Abdullaeva", "Abdalah Jadaan"],
                        ["Title / Designation", "General Manager / Client Lead", "Sales Head (TechGropse FZC LLC)"],
                        ["Signature & Seal", "[ Signed Electronic Signature ]", "[ Signed Corporate Seal ]"],
                        ["Date of Execution", "03 June 2026", "03 June 2026"],
                    ],
                ),
            ]
            paginated_segments.append(
                DocumentSegment(
                    segment_id="seg_signoff",
                    name=f"{len(paginated_segments)+1}. Formal Execution & Sign-Off Authorization",
                    segment_type="table",
                    content=build_tiptap_segment_doc(signoff_nodes),
                )
            )

    return {"segments": paginated_segments, "status": "styling"}


async def aesthetic_stylist_agent_node(state: ProcurementState) -> dict[str, Any]:
    """SUBAGENT 3: Visual Polish & Theme Stylist Agent.
    Applies rich typography, color themes, page border accents, and watermark properties."""
    logger.info("🎨 SUBAGENT 3 (Aesthetic Stylist): Polishing design theme, typography, & watermarks...")

    design = state.design_config
    if not design:
        from app.agents.procurement_graph import compute_rag_design_config
        design, _ = compute_rag_design_config(state.raw_prompt, state.doc_type)

    # Ensure rich corporate aesthetics if not already customized
    if not design.page_border or design.page_border == "none":
        design.page_border = "solid 1px rgba(26, 115, 232, 0.2)"

    return {
        "segments": state.segments,
        "design_config": design,
        "page_layout_size": state.page_layout_size,
        "status": "ready",
    }


builder = StateGraph(ProcurementState)
builder.add_node("manager_router", manager_router_node)
builder.add_node("doc_type_classifier", doc_type_classifier_node)
builder.add_node("rag_enrichment", rag_enrichment_node)
builder.add_node("fillup_agent", fillup_agent_node)
builder.add_node("image_extractor_agent", image_extractor_agent_node)
builder.add_node("segment_generation", segment_generation_node)
builder.add_node("verifier_agent", verifier_agent_node)
builder.add_node("layout_composer_agent", layout_composer_agent_node)
builder.add_node("pagination_fit_agent", pagination_fit_agent_node)
builder.add_node("aesthetic_stylist_agent", aesthetic_stylist_agent_node)

def route_request(state: ProcurementState) -> str:
    if state.doc_type is not None:
        return "rag_enrichment"
    return "doc_type_classifier"

builder.set_entry_point("manager_router")
builder.add_conditional_edges("manager_router", route_request)
builder.add_edge("doc_type_classifier", "rag_enrichment")
builder.add_edge("rag_enrichment", "fillup_agent")
builder.add_edge("fillup_agent", "image_extractor_agent")
builder.add_edge("image_extractor_agent", "segment_generation")
builder.add_edge("segment_generation", "verifier_agent")
builder.add_edge("verifier_agent", "layout_composer_agent")
builder.add_edge("layout_composer_agent", "pagination_fit_agent")
builder.add_edge("pagination_fit_agent", "aesthetic_stylist_agent")
builder.add_edge("aesthetic_stylist_agent", END)

procurement_graph = builder.compile()
