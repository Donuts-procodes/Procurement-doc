from __future__ import annotations

import logging
from typing import Any, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.procurement_graph import ProcurementState, procurement_graph
from app.agents.edit_graph import SegmentEditResult, segment_edit_result_to_nodes
from app.db.document_store import document_store
from app.core.session import SessionConfig, session_store
from app.schemas.schemas import LLMProvider, ProcurementDocType
from app.services.llm_providers import get_chat_model
from app.services.rag_pipeline import GeneratedDocument
from app.services.tiptap_engine import (
    build_tiptap_segment_doc,
    tiptap_heading_node,
    tiptap_paragraph_node,
    tiptap_bullet_list_node,
    tiptap_table_node,
)
from app.services.vector_store import KnowledgeBase

from app.schemas.preflight_schemas import (
    PreflightBlueprintRequest,
    PreflightBlueprintResponse,
)
from app.services.preflight_service import compute_preflight_blueprint

logger = logging.getLogger("gdocs.routes_generate")
router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("/blueprint", response_model=PreflightBlueprintResponse)
@router.post("/preflight/blueprint", response_model=PreflightBlueprintResponse)
async def get_preflight_blueprint(payload: PreflightBlueprintRequest) -> PreflightBlueprintResponse:
    logger.info(f"POST /api/generate/blueprint: Analyzing intent for prompt='{payload.prompt[:40]}...'")
    blueprint = compute_preflight_blueprint(payload)
    logger.info(
        f"GenSpark Blueprint computed: template='{blueprint.recommended_template_id}' "
        f"doc_type='{blueprint.recommended_doc_type}' confidence={blueprint.confidence_score}"
    )
    return blueprint


from pydantic import BaseModel, Field, field_validator

class InitialGenerateRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    session_id: str | None = Field(default=None)
    kb_id: str | None = Field(default=None)
    procurement_doc_type: Any = Field(default=ProcurementDocType.RFP)
    template_id: str | None = Field(default="rfp_enterprise")
    num_pages: Any = Field(default=5)
    page_layout_size: str | None = Field(default="A4")
    prompt: Any = Field(default="Generate procurement proposal document")
    content_density: Literal["min", "med", "max"] | None = Field(default="med")
    provider: LLMProvider | None = Field(default=None)
    model_name: str | None = Field(default=None, alias="model")
    api_key: str | None = Field(default=None)

    # Guided procurement input parameters (direct ground-truth)
    buyer_name: str | None = Field(default=None)
    vendor_name: str | None = Field(default=None)
    budget_estimate: str | None = Field(default=None)
    delivery_timeline: str | None = Field(default=None)
    compliance_frameworks: list[str] | None = Field(default=None)
    primary_tech: str | None = Field(default=None)
    sla_target: str | None = Field(default=None)

    @field_validator("procurement_doc_type", mode="before")
    def parse_procurement_doc_type(cls, v):
        if not v:
            return ProcurementDocType.RFP
        if isinstance(v, ProcurementDocType):
            return v
        v_str = str(v).upper()
        for doc_enum in ProcurementDocType:
            if doc_enum.value in v_str or doc_enum.name in v_str:
                return doc_enum
        return ProcurementDocType.RFP

    @field_validator("num_pages", mode="before")
    def parse_num_pages(cls, v):
        try:
            val = int(v)
            return max(1, min(50, val))
        except (ValueError, TypeError):
            return 5

    @field_validator("prompt", mode="before")
    def parse_prompt(cls, v):
        if not v or not str(v).strip():
            return "Generate procurement proposal document"
        return str(v).strip()


class AnswerQuestionRequest(BaseModel):
    session_id: str
    document_id: str | None = None
    answer: str
    content_density: Literal["min", "med", "max"] | None = "med"


class RefineSegmentRequest(BaseModel):
    session_id: str
    document_id: str
    segment_id: str
    instruction: str
    content_density: Literal["min", "med", "max"] | None = "med"


# Classes moved to app.agents.edit_graph


# Graph states are managed in session_store

def _get_or_fallback_session(session_id: str) -> SessionConfig:
    try:
        return session_store.get(session_id)
    except KeyError:
        logger.warning(f"Session '{session_id}' not found in in-memory session store (backend restarted). Re-creating fallback session.")
        from app.core.config import settings
        api_key = settings.OPENAI_API_KEY or "sk-fallback-session-key-placeholder"
        return session_store.create(provider=LLMProvider.OPENAI, model="gpt-4o", api_key=api_key)


@router.post("")
async def generate(payload: InitialGenerateRequest):
    import uuid
    eff_session_id = payload.session_id or f"session_{uuid.uuid4().hex[:8]}"
    logger.info(f"POST /api/generate received: session_id='{eff_session_id}' prompt='{payload.prompt[:40]}...'")
    
    try:
        session = session_store.get(eff_session_id)
    except KeyError:
        if payload.api_key and payload.provider and payload.model_name:
            session = session_store.create(
                provider=payload.provider,
                model=payload.model_name,
                api_key=payload.api_key,
                session_id=eff_session_id
            )
        else:
            session = _get_or_fallback_session(eff_session_id)
            
    session.add_message("user", payload.prompt)

    guided_collected: dict[str, str] = {}
    if payload.buyer_name and payload.buyer_name.strip():
        guided_collected["buyer_name"] = payload.buyer_name.strip()
    if payload.vendor_name and payload.vendor_name.strip():
        guided_collected["vendor_name"] = payload.vendor_name.strip()
    if payload.budget_estimate and payload.budget_estimate.strip():
        guided_collected["budget_estimate"] = payload.budget_estimate.strip()
    if payload.delivery_timeline and payload.delivery_timeline.strip():
        guided_collected["submission_deadline"] = payload.delivery_timeline.strip()
        guided_collected["target_delivery_date"] = payload.delivery_timeline.strip()
    if payload.compliance_frameworks:
        guided_collected["compliance_frameworks"] = ", ".join(payload.compliance_frameworks)
    if payload.primary_tech and payload.primary_tech.strip():
        guided_collected["primary_tech"] = payload.primary_tech.strip()
    if payload.sla_target and payload.sla_target.strip():
        guided_collected["sla_target"] = payload.sla_target.strip()

    initial_state = ProcurementState(
        session_id=session.session_id,
        raw_prompt=payload.prompt,
        doc_type=payload.procurement_doc_type,
        template_id=payload.template_id,
        kb_id=payload.kb_id,
        num_pages=payload.num_pages,
        page_layout_size=payload.page_layout_size,
        collected_fields=guided_collected,
        status="classifying",
    )

    final_state_dict = await procurement_graph.ainvoke(initial_state.model_dump())
    state = ProcurementState(**final_state_dict)

    if state.status == "collecting" and state.pending_question:
        doc_id = f"doc_{state.session_id[:8]}"
        session_store.save_graph_state(doc_id, state)
        session.add_message("assistant", state.pending_question)
        return {
            "status": "collecting",
            "document_id": doc_id,
            "pending_question": state.pending_question,
            "session_id": state.session_id,
            "missing_fields": state.missing_fields,
        }

    # Robust density filter: discard any accidentally empty or placeholder segments
    sanitized_segments = []
    for seg in state.segments:
        if isinstance(seg.content, dict) and "content" in seg.content:
            nodes = seg.content.get("content", [])
            has_table = any(n.get("type") == "table" for n in nodes)
            has_image = any(n.get("type") == "image" for n in nodes)
            has_text = any(
                len("".join(c.get("text", "") for c in n.get("content", []) if isinstance(c, dict)).strip()) > 0
                for n in nodes if n.get("type") in ("paragraph", "heading")
            )
            if has_table or has_image or has_text:
                sanitized_segments.append(seg)
        else:
            sanitized_segments.append(seg)

    state.segments = sanitized_segments
    page_titles = [seg.name for seg in state.segments]
    all_content = []
    for seg in state.segments:
        if isinstance(seg.content, dict) and "content" in seg.content:
            all_content.extend(seg.content["content"])

    full_tiptap_doc = {"type": "doc", "content": all_content}
    generated_doc = GeneratedDocument(
        document_id=f"doc_{state.session_id[:8]}",
        lexical_state=full_tiptap_doc,
        page_titles=page_titles,
    )
    document_store.save(generated_doc)
    session_store.save_graph_state(generated_doc.document_id, state)
    session.add_message("assistant", f"Generated document '{generated_doc.document_id}' with {len(state.segments)} segments.")

    style_config = {
        "fontFamily": state.design_config.font_family,
        "fontSize": state.design_config.font_size,
        "accentColor": state.design_config.accent_color,
        "theme": state.design_config.theme,
        "formatStyle": state.design_config.format_style,
        "colorPalette": state.design_config.color_palette,
        "fontPairing": state.design_config.font_pairing,
        "paragraphSpacing": state.design_config.paragraph_spacing,
        "watermark": state.design_config.watermark,
        "pageColor": state.design_config.page_color,
        "pageBorder": state.design_config.page_border,
    }

    return {
        "status": "ready",
        "document_id": generated_doc.document_id,
        "segments": [seg.model_dump() for seg in state.segments],
        "style_config": style_config,
        "page_layout_size": state.page_layout_size,
        "lexical_state": full_tiptap_doc,
        "page_titles": page_titles,
        "pending_question": state.pending_question,
        "research_findings": [f.model_dump() for f in getattr(state, "research_findings", [])],
        "audit_report": getattr(state, "audit_report", {}),
        "document_audit_report": getattr(state, "document_audit_report", {}),
        "sandbox_computations": getattr(state, "sandbox_computations", {}),
    }


@router.post("/answer")
async def answer_question(payload: AnswerQuestionRequest):
    logger.info(f"POST /api/generate/answer received for document_id='{payload.document_id}' query='{payload.answer}'")
    session = _get_or_fallback_session(payload.session_id)
    session.add_message("user", payload.answer)

    doc_id = payload.document_id or f"doc_{session.session_id[:8]}"
    state = session_store.get_graph_state(doc_id)
    if not state or not state.segments:
        reply_msg = "Session expired or document state lost. Please generate a new document to use the Co-Pilot safely."
        session.add_message("assistant", reply_msg)
        return {
            "status": "chat_reply",
            "document_id": doc_id,
            "chat_reply": reply_msg,
            "segments": [],
        }

    from app.agents.edit_graph import edit_graph, EditState

    initial_edit_state = EditState(
        session_id=session.session_id,
        document_id=doc_id,
        raw_prompt=payload.answer,
        segments=state.segments,
    )

    final_state_dict = await edit_graph.ainvoke(initial_edit_state.model_dump())
    final_edit_state = final_state_dict if isinstance(final_state_dict, EditState) else EditState(**final_state_dict)

    state.segments = final_edit_state.segments
    
    if not getattr(state, "design_config", None):
        from app.agents.procurement_graph import DocumentDesignConfig
        state.design_config = DocumentDesignConfig()

    # Persist Ribbon Formatting changes to the Document State
    actions_to_apply = []
    if getattr(final_edit_state, "ribbon_actions", None):
        actions_to_apply.extend(final_edit_state.ribbon_actions)
    elif final_edit_state.ribbon_action:
        actions_to_apply.append(final_edit_state.ribbon_action)

    for action in actions_to_apply:
        act_type = action.get("action_type") if isinstance(action, dict) else getattr(action, "action_type", None)
        if act_type == "set_font" and action.get("font_family"):
            state.design_config.font_family = action.get("font_family")
        elif act_type == "set_font_size" and action.get("font_size"):
            state.design_config.font_size = action.get("font_size")
        elif act_type == "set_accent_color" and action.get("accent_color"):
            state.design_config.accent_color = action.get("accent_color")
        elif act_type == "set_watermark":
            state.design_config.watermark = action.get("watermark") or ""
        elif act_type == "set_page_color" and action.get("page_color"):
            state.design_config.page_color = action.get("page_color")
        elif act_type == "set_page_border" and action.get("page_border"):
            state.design_config.page_border = action.get("page_border")
        elif act_type == "set_paper_size" and action.get("paper_size"):
            state.page_layout_size = action.get("paper_size")
        elif act_type == "set_spacing" and action.get("spacing"):
            state.design_config.paragraph_spacing = action.get("spacing")

    session_store.save_graph_state(doc_id, state)
    
    page_titles = [seg.name for seg in state.segments]
    all_content = []
    for seg in state.segments:
        if isinstance(seg.content, dict) and "content" in seg.content:
            all_content.extend(seg.content["content"])
    
    full_tiptap_doc = {"type": "doc", "content": all_content}
    from app.db.document_store import document_store
    document_store.save(GeneratedDocument(
        document_id=doc_id,
        lexical_state=full_tiptap_doc,
        page_titles=page_titles,
    ))

    reply_msg = final_edit_state.chat_reply or "Done!"
    session.add_message("assistant", reply_msg)

    return {
        "status": "ready" if final_edit_state.intent in ["edit_segment", "edit_multi_segments", "expand_document", "multitask"] else "chat_reply",
        "document_id": doc_id,
        "chat_reply": reply_msg,
        "ribbon_action": final_edit_state.ribbon_action,
        "ribbon_actions": getattr(final_edit_state, "ribbon_actions", []) or ([final_edit_state.ribbon_action] if final_edit_state.ribbon_action else []),
        "executed_tasks": getattr(final_edit_state, "executed_tasks", []),
        "segments": [seg.model_dump() for seg in state.segments],
        "lexical_state": full_tiptap_doc,
        "page_titles": page_titles,
        "style_config": {
            "fontFamily": state.design_config.font_family,
            "fontSize": state.design_config.font_size,
            "accentColor": state.design_config.accent_color,
            "theme": state.design_config.theme,
            "formatStyle": state.design_config.format_style,
            "colorPalette": state.design_config.color_palette,
            "fontPairing": state.design_config.font_pairing,
            "paragraphSpacing": state.design_config.paragraph_spacing,
            "watermark": state.design_config.watermark,
            "pageColor": state.design_config.page_color,
            "pageBorder": state.design_config.page_border,
        },
        "page_layout_size": state.page_layout_size,
    }


@router.post("/refine-segment")
async def refine_segment(payload: RefineSegmentRequest):
    logger.info(f"POST /api/generate/refine-segment for segment_id='{payload.segment_id}' instruction='{payload.instruction}'")
    session = _get_or_fallback_session(payload.session_id)
    session.add_message("user", f"Refine segment '{payload.segment_id}': {payload.instruction}")

    temperature_map = {"min": 0.1, "med": 0.3, "max": 0.7}
    dyn_temp = temperature_map.get(payload.content_density, 0.3)
    if "detail" in payload.instruction.lower() or "more" in payload.instruction.lower():
        dyn_temp = min(1.0, dyn_temp + 0.3)

    model = get_chat_model(session, temperature=dyn_temp)
    structured_model = model.with_structured_output(SegmentEditResult)

    session_memory_str = session.get_formatted_history()

    state = session_store.get_graph_state(payload.document_id)
    if not state:
        state = session_store.get_graph_state(f"doc_{session.session_id[:8]}")

    existing_text_parts = []
    preserve_images = []
    target_seg_name = payload.segment_id
    if state and state.segments:
        found_seg = next((s for s in state.segments if s.segment_id == payload.segment_id), None)
        if found_seg:
            target_seg_name = found_seg.name
            if isinstance(found_seg.content, dict):
                for node in found_seg.content.get("content", []):
                    if node.get("type") == "image":
                        preserve_images.append(node)
                    elif "content" in node:
                        node_text = "".join(c.get("text", "") for c in node.get("content", []) if isinstance(c, dict))
                        if node_text:
                            existing_text_parts.append(node_text)
    existing_segment_text = "\n".join(existing_text_parts) if existing_text_parts else "No previous text recorded."

    # Extract active document constraints to prevent CoPilot drift
    constraints_guide = ""
    if state and hasattr(state, "constraints") and state.constraints:
        c = state.constraints
        c_lines = []
        if c.buyer_organization: c_lines.append(f"Buyer Organization: {c.buyer_organization}")
        if c.vendor_organization: c_lines.append(f"Vendor Organization: {c.vendor_organization}")
        if c.budget_ceiling: c_lines.append(f"Budget Ceiling: ${c.budget_ceiling:,.2f}")
        if c.delivery_deadline: c_lines.append(f"Delivery Deadline: {c.delivery_deadline}")
        if c.compliance_frameworks: c_lines.append(f"Compliance Frameworks: {', '.join(c.compliance_frameworks)}")
        if c.primary_objective: c_lines.append(f"Primary Objective: {c.primary_objective}")
        if c.technical_stack: c_lines.append(f"Tech Stack: {', '.join(c.technical_stack)}")
        if c.sla_availability_target: c_lines.append(f"SLA Target: {c.sla_availability_target}")
        if c.explicit_exclusions: c_lines.append(f"Out of Scope / Exclusions: {', '.join(c.explicit_exclusions)}")
        if c_lines:
            constraints_guide = "MANDATORY DOCUMENT CONSTRAINTS (Never violate these established boundaries):\n" + "\n".join(c_lines) + "\n\n"

    instruction = (
        f"You are surgically editing the document segment '{target_seg_name}' ({payload.segment_id}).\n\n"
        f"{constraints_guide}"
        f"Existing Segment Content:\n{existing_segment_text}\n\n"
        f"User edit instruction: {payload.instruction}\n\n"
        f"Session Chat History Memory:\n{session_memory_str}\n\n"
        f"Apply the user's requested edit precisely to the existing content while preserving unaffected details, images, and tone.\n"
        f"Adhere strictly to the established document constraints.\n"
        f"Return updated heading, body paragraphs, structured sub-sections (with descriptive sub_heading and paragraphs), bullets, and optional tables."
    )
    content = await structured_model.ainvoke(instruction)

    nodes = segment_edit_result_to_nodes(content, content.heading or payload.segment_id, preserve_images=preserve_images)

    updated_segment = {
        "segment_id": payload.segment_id,
        "name": content.heading or payload.segment_id,
        "segment_type": "text",
        "content": build_tiptap_segment_doc(nodes),
        "compliance_flag": False,
        "compliance_note": None,
    }

    if state:
        from app.agents.procurement_graph import DocumentSegment
        for idx, seg in enumerate(state.segments):
            if seg.segment_id == payload.segment_id:
                state.segments[idx] = DocumentSegment(**updated_segment)
                break
        
        session_store.save_graph_state(payload.document_id, state)
        
        page_titles = [seg.name for seg in state.segments]
        all_content = []
        for seg in state.segments:
            if isinstance(seg.content, dict) and "content" in seg.content:
                all_content.extend(seg.content["content"])
        
        full_tiptap_doc = {"type": "doc", "content": all_content}
        document_store.save(GeneratedDocument(
            document_id=payload.document_id,
            lexical_state=full_tiptap_doc,
            page_titles=page_titles,
        ))

    session.add_message("assistant", f"Refined segment {payload.segment_id}")
    return {"segment": updated_segment, **updated_segment}

class RefineSelectionRequest(BaseModel):
    session_id: str
    selection_text: str
    instruction: str
    content_density: Literal["min", "med", "max"] | None = "med"


@router.post("/refine-selection")
async def refine_selection(payload: RefineSelectionRequest):
    logger.info(f"POST /api/generate/refine-selection for text snippet: '{payload.selection_text[:30]}...'")
    session = _get_or_fallback_session(payload.session_id)
    
    # Retrieve constraints for snippet refinement
    state = session_store.get_graph_state(f"doc_{session.session_id[:8]}")
    constraints_guide = ""
    if state and hasattr(state, "constraints") and state.constraints:
        c = state.constraints
        c_lines = []
        if c.buyer_organization: c_lines.append(f"Buyer: {c.buyer_organization}")
        if c.vendor_organization: c_lines.append(f"Vendor: {c.vendor_organization}")
        if c.budget_ceiling: c_lines.append(f"Budget: ${c.budget_ceiling:,.2f}")
        if c.delivery_deadline: c_lines.append(f"Deadline: {c.delivery_deadline}")
        if c.compliance_frameworks: c_lines.append(f"Compliance: {', '.join(c.compliance_frameworks)}")
        if c_lines:
            constraints_guide = f"Document Constraints: {', '.join(c_lines)}\n"

    temperature_map = {"min": 0.1, "med": 0.3, "max": 0.7}
    dyn_temp = temperature_map.get(payload.content_density, 0.2)
    model = get_chat_model(session, temperature=dyn_temp)
    prompt = (
        f"You are a surgical text co-pilot. Modify ONLY the text snippet provided according to the instruction.\n"
        f"{constraints_guide}"
        f"Do NOT output meta descriptions or explanations. Output ONLY the refined replacement text.\n\n"
        f"Original Snippet:\n\"{payload.selection_text}\"\n\n"
        f"Instruction:\n{payload.instruction}"
    )
    res = await model.ainvoke(prompt)
    replacement = res.content if isinstance(res.content, str) else str(res.content)
    cleaned_replacement = replacement.strip().strip('"')
    
    refusal_indicators = ["sorry", "cannot fulfill", "can't assist", "unable to assist", "as an ai"]
    if any(ind in cleaned_replacement.lower() for ind in refusal_indicators):
        logger.warning(f"Refine-selection refused instruction '{payload.instruction}', preserving original text.")
        return {"replacement_text": payload.selection_text}

    session.add_message("assistant", f"Surgically replaced selection '{payload.selection_text[:20]}...' with '{cleaned_replacement[:20]}...'")
    return {"replacement_text": cleaned_replacement}


class TargetedInlineRefineRequest(BaseModel):
    session_id: str
    prompt: str
    target_node_id: str | None = None
    selection_text: str
    context_window: str | None = None


import json
import time
import asyncio
from starlette.responses import StreamingResponse


@router.post("/stream")
async def generate_document_stream(payload: InitialGenerateRequest):
    logger.info(f"POST /api/v1/generate/stream started for prompt='{str(payload.prompt)[:60]}...'")
    session = _get_or_fallback_session(payload.session_id)
    if payload.provider and payload.api_key:
        session.provider = payload.provider
        session.api_key = payload.api_key
    if payload.model_name:
        session.model = payload.model_name

    async def event_generator():
        try:
            # 1. Lead Super Agent thought & tool execution
            yield f"data: {json.dumps({'type': 'agent_thought', 'step': 'Lead Super Agent analyzing document blueprint and decomposing intent...', 'status': 'running'})}\n\n"
            await asyncio.sleep(0.05)

            guided_collected: dict[str, str] = {}
            if payload.buyer_name and payload.buyer_name.strip():
                guided_collected["buyer_name"] = payload.buyer_name.strip()
            if payload.vendor_name and payload.vendor_name.strip():
                guided_collected["vendor_name"] = payload.vendor_name.strip()
            if payload.budget_estimate and payload.budget_estimate.strip():
                guided_collected["budget_estimate"] = payload.budget_estimate.strip()
            if payload.delivery_timeline and payload.delivery_timeline.strip():
                guided_collected["submission_deadline"] = payload.delivery_timeline.strip()
                guided_collected["target_delivery_date"] = payload.delivery_timeline.strip()
            if payload.compliance_frameworks:
                guided_collected["compliance_frameworks"] = ", ".join(payload.compliance_frameworks)
            if payload.primary_tech and payload.primary_tech.strip():
                guided_collected["primary_tech"] = payload.primary_tech.strip()
            if payload.sla_target and payload.sla_target.strip():
                guided_collected["sla_target"] = payload.sla_target.strip()

            initial_state = ProcurementState(
                session_id=session.session_id,
                raw_prompt=str(payload.prompt),
                doc_type=payload.procurement_doc_type,
                template_id=payload.template_id,
                kb_id=payload.kb_id,
                num_pages=int(payload.num_pages),
                page_layout_size=payload.page_layout_size,
                collected_fields=guided_collected,
                status="classifying",
            )

            from app.agents.procurement_graph import (
                super_agent_node,
                deep_research_subagent,
                sandbox_subagent,
                visual_curation_subagent,
                fact_check_agent_node,
                ai_docs_agent_node,
                canvas_checkpoint_agent_node,
            )

            super_result = await super_agent_node(initial_state)
            for k, v in super_result.items():
                setattr(initial_state, k, v)

            doc_type_val = initial_state.doc_type.value if initial_state.doc_type else "RFP"
            yield f"data: {json.dumps({'type': 'tool_execution', 'tool_name': 'super_agent', 'input': {'prompt': str(payload.prompt)[:80], 'doc_type': doc_type_val}, 'output': f'Document skeleton blueprinted for {initial_state.num_pages} target pages.'})}\n\n"
            yield f"data: {json.dumps({'type': 'agent_thought', 'step': 'Super Agent blueprint decomposed. Spawning parallel workers.', 'status': 'completed'})}\n\n"
            await asyncio.sleep(0.05)

            # 2. Parallel Workers Gathering
            yield f"data: {json.dumps({'type': 'agent_thought', 'step': 'Launching parallel subagents: Deep Research, Sandbox REPL, and Media Visual Curation...', 'status': 'running'})}\n\n"

            findings, computations, images = await asyncio.gather(
                deep_research_subagent(initial_state, session),
                sandbox_subagent(initial_state, session),
                visual_curation_subagent(initial_state),
            )
            initial_state.research_findings = findings
            initial_state.sandbox_computations = computations
            initial_state.extracted_images = images

            yield f"data: {json.dumps({'type': 'tool_execution', 'tool_name': 'deep_research_subagent', 'input': {'kb_id': payload.kb_id, 'scope': str(payload.prompt)[:60]}, 'output': f'Extracted {len(findings)} primary source quotes with provenance.'})}\n\n"
            li = computations.get("line_items", {})
            subtot = li.get("subtotal", 0)
            grndtot = li.get("grand_total", 0)
            sb_msg = f"Subtotal ${subtot:,.2f}, Grand total ${grndtot:,.2f}, 100% normalized payment schedule."
            yield f"data: {json.dumps({'type': 'tool_execution', 'tool_name': 'sandbox_subagent', 'input': {'math_engine': 'Deterministic Python Decimal REPL'}, 'output': sb_msg})}\n\n"
            yield f"data: {json.dumps({'type': 'tool_execution', 'tool_name': 'visual_curation_subagent', 'input': {'assets': 'Diagrams & Cover Banners'}, 'output': f'Prepared {len(images)} diagrams & visual assets.'})}\n\n"
            yield f"data: {json.dumps({'type': 'agent_thought', 'step': 'Parallel evidence gathering complete. Resolved to shared context ledger.', 'status': 'completed'})}\n\n"
            await asyncio.sleep(0.05)

            # 3. Fact-Check Agent (AI Judge)
            yield f"data: {json.dumps({'type': 'agent_thought', 'step': 'Adversarial Fact-Checking Agent (AI Judge) auditing numbers against sandbox runs and validating citations...', 'status': 'running'})}\n\n"
            judge_res = await fact_check_agent_node(initial_state)
            for k, v in judge_res.items():
                setattr(initial_state, k, v)

            audit = initial_state.audit_report
            aud_status = audit.get("status", "APPROVED")
            aud_notes = audit.get("audit_notes", "Verified")
            yield f"data: {json.dumps({'type': 'tool_execution', 'tool_name': 'fact_check_agent', 'input': {'ground_truth_claims': len(findings), 'math_verification': 'Python Sandbox'}, 'output': f'Status: {aud_status} - {aud_notes}'})}\n\n"
            yield f"data: {json.dumps({'type': 'agent_thought', 'step': 'Adversarial audit completed. Immutable citation handles attached.', 'status': 'completed'})}\n\n"
            await asyncio.sleep(0.05)

            # 4. AI Docs Canvas Synthesizer & Canvas Patches
            yield f"data: {json.dumps({'type': 'agent_thought', 'step': 'AI Docs Drafting Subagent synthesizing verified context into AST canvas nodes...', 'status': 'running'})}\n\n"
            docs_res = await ai_docs_agent_node(initial_state)
            initial_state.segments = docs_res.get("segments", [])

            for seg in initial_state.segments:
                yield f"data: {json.dumps({'type': 'canvas_patch', 'operation': 'append', 'target_id': seg.segment_id, 'content': seg.content})}\n\n"
                await asyncio.sleep(0.02)

            yield f"data: {json.dumps({'type': 'agent_thought', 'step': 'Canvas synthesis complete. Rich-text AST synchronized.', 'status': 'completed'})}\n\n"

            # 5. Canvas Checkpoint Agent
            checkpoint_res = await canvas_checkpoint_agent_node(initial_state)
            for k, v in checkpoint_res.items():
                setattr(initial_state, k, v)

            doc_id = f"doc_{initial_state.session_id[:8]}"
            all_content = []
            for seg in initial_state.segments:
                if isinstance(seg.content, dict) and "content" in seg.content:
                    all_content.extend(seg.content["content"])
            full_tiptap_doc = {"type": "doc", "content": all_content}
            page_titles = [seg.name for seg in initial_state.segments]

            document_store.save(GeneratedDocument(
                document_id=doc_id,
                lexical_state=full_tiptap_doc,
                page_titles=page_titles,
            ))
            session_store.save_graph_state(doc_id, initial_state)

            version_id = f"v_{int(time.time() * 1000)}"
            style_config = {
                "fontFamily": initial_state.design_config.font_family,
                "fontSize": initial_state.design_config.font_size,
                "accentColor": initial_state.design_config.accent_color,
                "theme": initial_state.design_config.theme,
                "formatStyle": initial_state.design_config.format_style,
                "colorPalette": initial_state.design_config.color_palette,
                "fontPairing": initial_state.design_config.font_pairing,
                "paragraphSpacing": initial_state.design_config.paragraph_spacing,
                "watermark": initial_state.design_config.watermark,
                "pageColor": initial_state.design_config.page_color,
                "pageBorder": initial_state.design_config.page_border,
            }
            yield f"data: {json.dumps({'type': 'checkpoint', 'version_id': version_id, 'timestamp': int(time.time() * 1000), 'document_id': doc_id, 'segments': [s.model_dump() for s in initial_state.segments], 'page_titles': page_titles, 'style_config': style_config, 'page_layout_size': initial_state.page_layout_size, 'missing_fields': initial_state.missing_fields})}\n\n"

        except Exception as e:
            logger.error(f"Streaming generation error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'agent_thought', 'step': f'Error during pipeline execution: {str(e)}', 'status': 'completed'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/stream-selection")
async def targeted_selection_stream(payload: TargetedInlineRefineRequest):
    logger.info(f"POST /api/v1/generate/stream-selection for node='{payload.target_node_id}' prompt='{payload.prompt}'")
    session = _get_or_fallback_session(payload.session_id)

    async def event_generator():
        try:
            step_prompt = f"Surgically refining target selection: '{payload.prompt}'..."
            yield f"data: {json.dumps({'type': 'agent_thought', 'step': step_prompt, 'status': 'running'})}\n\n"
            await asyncio.sleep(0.05)

            model = get_chat_model(session, temperature=0.25)
            context_snippet = f"Context:\n{payload.context_window}\n\n" if payload.context_window else ""
            instruction = (
                f"You are a surgical document co-pilot. Refine ONLY the selected text according to the instruction.\n"
                f"{context_snippet}"
                f"Selected Text to replace:\n\"{payload.selection_text}\"\n\n"
                f"Instruction:\n{payload.prompt}\n\n"
                f"Output ONLY the final replacement text without explanation."
            )
            res = await model.ainvoke(instruction)
            replacement = str(res.content).strip().strip('"')

            summary_out = f"Replaced: {replacement[:60]}..." if len(replacement) > 60 else f"Replaced: {replacement}"
            yield f"data: {json.dumps({'type': 'tool_execution', 'tool_name': 'targeted_inline_refiner', 'input': {'prompt': payload.prompt, 'target_node_id': payload.target_node_id}, 'output': summary_out})}\n\n"
            await asyncio.sleep(0.05)

            yield f"data: {json.dumps({'type': 'canvas_patch', 'operation': 'replace_range', 'target_id': payload.target_node_id, 'content': replacement})}\n\n"
            await asyncio.sleep(0.05)

            version_id = f"v_inline_{int(time.time() * 1000)}"
            yield f"data: {json.dumps({'type': 'checkpoint', 'version_id': version_id, 'timestamp': int(time.time() * 1000)})}\n\n"
            yield f"data: {json.dumps({'type': 'agent_thought', 'step': 'Targeted inline modification applied successfully.', 'status': 'completed'})}\n\n"
        except Exception as e:
            logger.error(f"Stream-selection error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'agent_thought', 'step': f'Refinement error: {str(e)}', 'status': 'completed'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

