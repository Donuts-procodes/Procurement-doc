from typing import Any, Literal
import logging
import uuid
from pydantic import BaseModel, Field

from langgraph.graph import END, StateGraph

from app.agents.procurement_graph import DocumentSegment
from app.services.llm_providers import get_chat_model
from app.core.session import session_store
from app.services.tiptap_engine import (
    build_tiptap_segment_doc,
    tiptap_heading_node,
    tiptap_paragraph_node,
    tiptap_bullet_list_node,
    tiptap_table_node,
)

logger = logging.getLogger("gdocs.edit_graph")

class RibbonActionCommand(BaseModel):
    action_type: str | None = Field(default=None, description="One of: set_font, set_font_size, set_accent_color, set_watermark, set_page_color, set_page_border, set_paper_size, set_spacing, insert_table, add_page, clear_formatting")
    font_family: str | None = None
    font_size: str | None = None
    accent_color: str | None = None
    watermark: str | None = None
    page_color: str | None = None
    page_border: str | None = None
    paper_size: str | None = None
    spacing: str | None = None
    table_rows: int | None = None
    table_cols: int | None = None


class CoPilotIntentClassification(BaseModel):
    intent: Literal["chat", "edit_segment", "expand_document", "ribbon_command"]
    target_segment_name: str | None = None
    chat_reply: str | None = None
    edit_summary: str | None = None
    ribbon_action: RibbonActionCommand | None = None


class SegmentEditResult(BaseModel):
    heading: str
    paragraphs: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)
    table_headers: list[str] | None = Field(default=None, description="Optional headers for a structured table")
    table_rows: list[list[str]] | None = Field(default=None, description="Optional rows of cell strings for a structured table")


class EditState(BaseModel):
    session_id: str
    document_id: str
    raw_prompt: str
    segments: list[DocumentSegment]
    intent: Literal["chat", "edit_segment", "expand_document", "ribbon_command", "unknown"] = "unknown"
    target_segment_name: str | None = None
    chat_reply: str | None = None
    ribbon_action: dict | None = None


async def classifier_node(state_dict: dict[str, Any]) -> dict[str, Any]:
    state = EditState(**state_dict)
    session = session_store.get(state.session_id)
    model = get_chat_model(session, temperature=0.3)
    
    intent_classifier = model.with_structured_output(CoPilotIntentClassification)
    
    segment_names = [seg.name for seg in state.segments]
    session_history = session.get_formatted_history()
    
    prompt = (
        f"Analyze the user query: '{state.raw_prompt}'\n\n"
        f"Session Chat History:\n{session_history}\n\n"
        f"Document Segments Available: {segment_names}\n\n"
        f"Decide if the user is:\n"
        f"1. 'ribbon_command': Requesting a ribbon/formatting/styling/layout action.\n"
        f"2. 'chat': Asking a question or conversational.\n"
        f"3. 'edit_segment': Requesting a text change to a specific segment (Specify target_segment_name).\n"
        f"4. 'expand_document': Providing broad document changes like adding a new section or rewriting the whole document."
    )
    
    intent_result = await intent_classifier.ainvoke(prompt)
    logger.info(f"Classified intent: {intent_result.intent}")
    
    return {
        "intent": intent_result.intent,
        "target_segment_name": intent_result.target_segment_name,
        "chat_reply": intent_result.chat_reply,
        "ribbon_action": intent_result.ribbon_action.model_dump() if intent_result.ribbon_action else None
    }


async def chat_node(state_dict: dict[str, Any]) -> dict[str, Any]:
    state = EditState(**state_dict)
    reply = state.chat_reply or "I evaluated the document context. Let me know if you would like me to modify any specific section."
    return {"chat_reply": reply}


async def ribbon_node(state_dict: dict[str, Any]) -> dict[str, Any]:
    state = EditState(**state_dict)
    action = state.ribbon_action.get("action_type") if state.ribbon_action else "action"
    reply = state.chat_reply or f"Executed ribbon command '{action}' cleanly!"
    return {"chat_reply": reply}


async def surgical_edit_node(state_dict: dict[str, Any]) -> dict[str, Any]:
    state = EditState(**state_dict)
    
    if not state.target_segment_name:
        return {"chat_reply": "I couldn't identify which segment you wanted to edit. Please specify the section name clearly."}
        
    target_name = state.target_segment_name.lower()
    target_seg = next((s for s in state.segments if target_name in s.name.lower() or s.name.lower() in target_name), None)
    
    if not target_seg:
        return {"chat_reply": f"I couldn't find a segment matching '{state.target_segment_name}'. Please check the section name."}
        
    session = session_store.get(state.session_id)
    model = get_chat_model(session, temperature=0.5)
    editor_model = model.with_structured_output(SegmentEditResult)
    
    outline = ", ".join([s.name for s in state.segments if s.name != target_seg.name])
    
    edit_prompt = (
        f"Surgically edit the single segment '{target_seg.name}'.\n"
        f"User request: {state.raw_prompt}\n"
        f"Session Memory:\n{session.get_formatted_history()}\n\n"
        f"Context - Other document sections include: {outline}\n"
        f"Ensure tonal and logical consistency with the rest of the document.\n\n"
        f"Return updated heading, body paragraphs, and optional bullets."
    )
    
    content = await editor_model.ainvoke(edit_prompt)
    
    nodes = [tiptap_heading_node(content.heading or target_seg.name)]
    for p in content.paragraphs:
        nodes.append(tiptap_paragraph_node(p))
    if content.bullets:
        nodes.append(tiptap_bullet_list_node(content.bullets))
    if content.table_headers and content.table_rows:
        nodes.append(tiptap_table_node(content.table_headers, content.table_rows))
        
    target_seg.content = build_tiptap_segment_doc(nodes)
    
    return {
        "segments": state.segments,
        "chat_reply": f"Surgically updated segment '{target_seg.name}' cleanly!"
    }


async def document_expansion_node(state_dict: dict[str, Any]) -> dict[str, Any]:
    state = EditState(**state_dict)
    
    if "rewrite" in state.raw_prompt.lower() or "regenerate" in state.raw_prompt.lower() or "whole document" in state.raw_prompt.lower():
        return {"chat_reply": "To protect your manual edits, I cannot rewrite the entire document. Please ask me to edit a specific section or add a new one instead."}
        
    session = session_store.get(state.session_id)
    model = get_chat_model(session, temperature=0.7)
    expander_model = model.with_structured_output(SegmentEditResult)
    
    outline = ", ".join([s.name for s in state.segments])
    
    prompt = (
        f"The user wants to add a new section to the document based on: '{state.raw_prompt}'.\n"
        f"Current sections: {outline}\n"
        f"Generate a brand new segment (heading, paragraphs, bullets) that seamlessly fits into this document."
    )
    
    content = await expander_model.ainvoke(prompt)
    
    nodes = [tiptap_heading_node(content.heading)]
    for p in content.paragraphs:
        nodes.append(tiptap_paragraph_node(p))
    if content.bullets:
        nodes.append(tiptap_bullet_list_node(content.bullets))
    if content.table_headers and content.table_rows:
        nodes.append(tiptap_table_node(content.table_headers, content.table_rows))
        
    new_seg = DocumentSegment(
        segment_id=f"seg_{uuid.uuid4().hex[:8]}",
        name=content.heading,
        segment_type="text",
        content=build_tiptap_segment_doc(nodes)
    )
    
    state.segments.append(new_seg)
    
    return {
        "segments": state.segments,
        "chat_reply": f"Added a brand new section: '{content.heading}'!"
    }


def route_intent(state_dict: dict[str, Any]) -> str:
    intent = state_dict.get("intent")
    if intent == "edit_segment":
        return "surgical_edit"
    elif intent == "expand_document":
        return "document_expansion"
    elif intent == "ribbon_command":
        return "ribbon"
    return "chat"


workflow = StateGraph(EditState)

workflow.add_node("classifier", classifier_node)
workflow.add_node("chat", chat_node)
workflow.add_node("ribbon", ribbon_node)
workflow.add_node("surgical_edit", surgical_edit_node)
workflow.add_node("document_expansion", document_expansion_node)

workflow.set_entry_point("classifier")

workflow.add_conditional_edges(
    "classifier",
    route_intent,
    {
        "chat": "chat",
        "ribbon": "ribbon",
        "surgical_edit": "surgical_edit",
        "document_expansion": "document_expansion"
    }
)

workflow.add_edge("chat", END)
workflow.add_edge("ribbon", END)
workflow.add_edge("surgical_edit", END)
workflow.add_edge("document_expansion", END)

edit_graph = workflow.compile()
