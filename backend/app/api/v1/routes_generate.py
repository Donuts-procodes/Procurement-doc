from __future__ import annotations

import logging
from typing import Any, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.procurement_graph import ProcurementState, procurement_graph, SegmentEditResult
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

logger = logging.getLogger("gdocs.routes_generate")
router = APIRouter(prefix="/generate", tags=["generate"])


from pydantic import BaseModel, Field, field_validator

class InitialGenerateRequest(BaseModel):
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

    initial_state = ProcurementState(
        session_id=session.session_id,
        raw_prompt=payload.prompt,
        doc_type=payload.procurement_doc_type,
        template_id=payload.template_id,
        kb_id=payload.kb_id,
        num_pages=payload.num_pages,
        page_layout_size=payload.page_layout_size,
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
    final_edit_state = EditState(**final_state_dict)

    state.segments = final_edit_state.segments
    
    # Persist Ribbon Formatting changes to the Document State
    if final_edit_state.ribbon_action:
        action = final_edit_state.ribbon_action
        act_type = action.get("action_type")
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
        "status": "ready" if final_edit_state.intent in ["edit_segment", "expand_document"] else "chat_reply",
        "document_id": doc_id,
        "chat_reply": reply_msg,
        "ribbon_action": final_edit_state.ribbon_action,
        "segments": [seg.model_dump() for seg in state.segments],
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
    instruction = (
        f"You are editing a specific document segment '{payload.segment_id}'.\n"
        f"Session Chat History Memory:\n{session_memory_str}\n\n"
        f"User edit instruction: {payload.instruction}\n"
        f"Apply the user's requested edit precisely. Return updated heading, body paragraphs, and optional bullets."
    )
    content = await structured_model.ainvoke(instruction)

    nodes = [tiptap_heading_node(content.heading or payload.segment_id)]
    for p in content.paragraphs:
        nodes.append(tiptap_paragraph_node(p))
    if content.bullets:
        nodes.append(tiptap_bullet_list_node(content.bullets))
    if content.table_headers and content.table_rows:
        nodes.append(tiptap_table_node(content.table_headers, content.table_rows))

    updated_segment = {
        "segment_id": payload.segment_id,
        "name": content.heading or payload.segment_id,
        "segment_type": "text",
        "content": build_tiptap_segment_doc(nodes),
    }

    state = session_store.get_graph_state(payload.document_id)
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
    return updated_segment

class RefineSelectionRequest(BaseModel):
    session_id: str
    selection_text: str
    instruction: str
    content_density: Literal["min", "med", "max"] | None = "med"


@router.post("/refine-selection")
async def refine_selection(payload: RefineSelectionRequest):
    logger.info(f"POST /api/generate/refine-selection for text snippet: '{payload.selection_text[:30]}...'")
    session = _get_or_fallback_session(payload.session_id)
    
    temperature_map = {"min": 0.1, "med": 0.3, "max": 0.7}
    dyn_temp = temperature_map.get(payload.content_density, 0.2)
    model = get_chat_model(session, temperature=dyn_temp)
    prompt = (
        f"You are a surgical text co-pilot. Modify ONLY the text snippet provided according to the instruction.\n"
        f"Do NOT output meta descriptions or explanations. Output ONLY the refined replacement text.\n\n"
        f"Original Snippet:\n\"{payload.selection_text}\"\n\n"
        f"Instruction:\n{payload.instruction}"
    )
    res = await model.ainvoke(prompt)
    replacement = res.content if isinstance(res.content, str) else str(res.content)
    cleaned_replacement = replacement.strip().strip('"')
    session.add_message("assistant", f"Surgically replaced selection '{payload.selection_text[:20]}...' with '{cleaned_replacement[:20]}...'")
    return {"replacement_text": cleaned_replacement}
