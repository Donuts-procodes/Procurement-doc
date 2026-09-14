import ast
import asyncio
import logging
import operator
import re
from typing import Any, Literal
import uuid
from pydantic import BaseModel, Field

from langgraph.graph import END, StateGraph

from app.agents.procurement_graph import DocumentSegment, SubSection, MetricBadge
from app.services.llm_providers import get_chat_model
from app.core.session import session_store
from app.services.tiptap_engine import (
    build_tiptap_segment_doc,
    tiptap_heading_node,
    tiptap_paragraph_node,
    tiptap_bullet_list_node,
    tiptap_table_node,
    tiptap_callout_node,
    tiptap_metric_badge_node,
    tiptap_figure_caption_node,
)

logger = logging.getLogger("gdocs.edit_graph")

COPILOT_ENTERPRISE_EDIT_GUIDELINES = (
    "ENTERPRISE PUBLICATION QUALITY STANDARDS:\n"
    "1. Decisive Active Voice: Avoid introductory throat-clearing (e.g. 'In this section we detail...'). Open immediately with authoritative operational specifications.\n"
    "2. High-Impact Scannability: Use markdown `**bold**` to emphasize critical technical mechanisms, milestone dates, and deliverable names.\n"
    "3. Quantifiable Commitments: State exact metrics, SLA baselines (e.g. 99.99% uptime, < 50ms latency, Net 30 payment terms), and international standards (ISO 27001, SOC 2 Type II, GDPR, AES-256) instead of vague generalities.\n"
    "4. Executive Elements: Provide an executive callout box (callout_title, callout_text) for core operational principles or commitments, and 2-3 key metric badges in `key_metrics` (label, value).\n"
    "5. Tabular Data: When presenting multi-attribute data, pricing, or comparative matrices, populate table_headers and table_rows.\n"
    "6. Strict Decimal Subheading Hierarchy: Keep all subheadings strictly prefixed with decimal numbering matching the section index (e.g. '1.1 System Architecture', '1.2 Security Protocol').\n"
    "7. Domain Grounding: Eliminate generic filler and placeholder names ('John Doe', 'Acme Corp'). Ground all statements in concrete technical deliverables and requirements.\n"
)


class RibbonActionCommand(BaseModel):
    action_type: str | None = Field(
        default=None,
        description="One of: set_font, set_font_size, set_accent_color, set_watermark, set_page_color, set_page_border, set_paper_size, set_spacing, insert_table, add_page, clear_formatting, undo, redo, set_zoom, set_layout_mode, toggle_dark_mode, insert_signature_block, insert_callout_box, insert_date, align_text, text_format, export_document, set_header, set_page_numbers, insert_cover_page, insert_wordart, insert_reviewer_note, insert_image, insert_link, insert_bookmark, insert_horizontal_rule, insert_list"
    )
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
    zoom_level: int | None = Field(default=None, description="Zoom percentage e.g. 100, 125, 75")
    layout_mode: str | None = Field(default=None, description="focus, print, or web")
    export_format: str | None = Field(default=None, description="pdf, doc, or txt")
    alignment: str | None = Field(default=None, description="left, center, right, or justify")
    format_style: str | None = Field(default=None, description="bold, italic, underline, strike, subscript, superscript")
    header_text: str | None = None
    page_number_position: str | None = Field(default=None, description="bottom-right, bottom-center, top-right, or none")
    url: str | None = None
    custom_text: str | None = None
    cover_style: str | None = Field(default=None, description="corporate, minimal, or modern")
    list_type: str | None = Field(default=None, description="bullet or ordered")


class CoPilotTaskAction(BaseModel):
    task_type: Literal[
        "ribbon_command",
        "edit_segment",
        "relocate_image",
        "expand_document",
        "math_calculation",
    ] = Field(description="Granular category of this discrete sub-task")
    target_segment: str | None = Field(
        default=None,
        description="Section title or 1-based index (e.g. '1', 'Scope of Work') to edit, or source section for relocate_image",
    )
    destination_segment: str | None = Field(
        default=None,
        description="Target section title or 1-based index for relocate_image",
    )
    instruction: str = Field(description="Specific surgical sub-instruction for this task")
    ribbon_action: RibbonActionCommand | None = None
    math_expression: str | None = Field(
        default=None,
        description="Mathematical expression if task_type is math_calculation, e.g. '150000 * 0.18'",
    )


class CoPilotMultiTaskPlan(BaseModel):
    is_compound: bool = Field(description="True if prompt contains 2 or more distinct actions or spans multiple domains")
    tasks: list[CoPilotTaskAction] | None = Field(default_factory=list, description="Ordered list of decoupled sub-tasks to execute")
    summary: str = Field(default="Executing compound operations", description="Executive summary of the multitasking plan")


class CoPilotIntentClassification(BaseModel):
    intent: Literal["chat", "edit_segment", "edit_multi_segments", "expand_document", "ribbon_command", "multitask"]
    target_segment_name: str | None = Field(default=None, description="For edit_segment: exact or approximate title/index of the single section to edit")
    target_segment_names: list[str] | None = Field(default=None, description="For edit_multi_segments: list of section titles to edit, or ['all'] if change applies across whole document")
    chat_reply: str | None = None
    edit_summary: str | None = None
    ribbon_action: RibbonActionCommand | None = None
    multi_plan: CoPilotMultiTaskPlan | None = None


class SegmentEditResult(BaseModel):
    heading: str
    key_metrics: list[MetricBadge] | None = Field(default=None, description="Optional 2-3 key quantifiable metrics or KPIs to display as executive badges directly under the heading")
    callout_title: str | None = Field(default=None, description="Optional executive callout box title, e.g. 'ARCHITECTURE PRINCIPLE', 'SLA COMMITMENT', 'COMPLIANCE NOTICE'")
    callout_text: str | None = Field(default=None, description="Optional high-impact callout details emphasizing crucial terms or commitments")
    paragraphs: list[str] | None = Field(default_factory=list, description="Introductory or overview paragraphs")
    sub_sections: list[SubSection] | None = Field(default_factory=list, description="Structured subsections with sub_heading and paragraphs")
    bullets: list[str] | None = Field(default_factory=list)
    table_headers: list[str] | None = Field(default=None, description="Optional headers for a structured table")
    table_rows: list[list[str]] | None = Field(default=None, description="Optional rows of cell strings for a structured table")


def segment_edit_result_to_nodes(
    content: SegmentEditResult,
    default_heading: str,
    preserve_images: list[dict[str, Any]] | None = None,
    seg_index: int | None = None,
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []

    # Wide cover banners remain on top (Page 1 top header)
    cover_images: list[dict[str, Any]] = []
    diagram_images: list[dict[str, Any]] = []
    if preserve_images:
        for img in preserve_images:
            alt = (img.get("attrs", {}).get("alt") or "").lower()
            if "cover" in alt or "banner" in alt:
                cover_images.append(img)
            else:
                diagram_images.append(img)

    for c in cover_images:
        nodes.append(c)

    # Determine section numbering
    h_text = content.heading or default_heading
    sec_match = re.match(r'^(\d+)\.', h_text.strip())
    if not sec_match:
        sec_match = re.match(r'^(\d+)\.', default_heading.strip())
    sec_num = str(seg_index) if seg_index else (sec_match.group(1) if sec_match else None)

    # 1. Primary Section Title (H1)
    clean_h = re.sub(r'^\d+\.\s*', '', h_text).strip()
    final_h1 = f"{sec_num}. {clean_h}" if sec_num else clean_h
    nodes.append(tiptap_heading_node(final_h1, level=1))

    # 2. Executive KPI Metric Badges (directly under H1 for immediate visual scannability)
    if content.key_metrics:
        badge_tuples = [(m.label, m.value) for m in content.key_metrics if getattr(m, "label", None) and getattr(m, "value", None)]
        if badge_tuples:
            nodes.append(tiptap_metric_badge_node(badge_tuples))

    # 3. Introductory Overview Paragraphs
    for p in (content.paragraphs or []):
        cleaned = re.sub(r'\[IMAGE:\s*[^\]]+\]', '', p).strip()
        if cleaned:
            nodes.append(tiptap_paragraph_node(cleaned))

    # 4. Contextual Diagrams (grounded cleanly below intro text with figure caption)
    for d in diagram_images:
        nodes.append(d)
        caption = d.get("attrs", {}).get("title") or d.get("attrs", {}).get("alt")
        if caption and not caption.lower().startswith("image"):
            nodes.append(tiptap_figure_caption_node(caption))

    # 5. Executive Callout Box (if present)
    if content.callout_title and content.callout_text:
        nodes.append(tiptap_callout_node(content.callout_title, content.callout_text, icon="📌"))

    # 6. Structured Subsections (H2 + paragraphs)
    h_text = content.heading or default_heading
    sec_match = re.match(r'^(\d+)\.', h_text.strip())
    sec_num = sec_match.group(1) if sec_match else None

    for sub_idx, sub in enumerate(content.sub_sections or [], start=1):
        if sub.sub_heading:
            cleaned_sub = re.sub(r'^[\d\.\-\s\)]+', '', sub.sub_heading).strip()
            formatted_sub = f"{sec_num}.{sub_idx} {cleaned_sub}" if sec_num else cleaned_sub
            nodes.append(tiptap_heading_node(formatted_sub, level=2))
        for p in (sub.paragraphs or []):
            cleaned = re.sub(r'\[IMAGE:\s*[^\]]+\]', '', p).strip()
            if cleaned:
                nodes.append(tiptap_paragraph_node(cleaned))

    # 7. Bullet List
    if content.bullets:
        clean_bullets = [re.sub(r'\[IMAGE:\s*[^\]]+\]', '', b).strip() for b in content.bullets if b.strip()]
        if clean_bullets:
            nodes.append(tiptap_bullet_list_node(clean_bullets))

    # 8. Structured Table
    if content.table_headers and content.table_rows:
        nodes.append(tiptap_table_node(content.table_headers, content.table_rows))

    return nodes


class EditState(BaseModel):
    session_id: str
    document_id: str
    raw_prompt: str
    segments: list[DocumentSegment]
    intent: Literal["chat", "edit_segment", "edit_multi_segments", "expand_document", "ribbon_command", "multitask", "unknown"] = "unknown"
    target_segment_name: str | None = None
    target_segment_names: list[str] | None = Field(default_factory=list)
    chat_reply: str | None = None
    ribbon_action: dict | None = None
    ribbon_actions: list[dict] = Field(default_factory=list)
    multi_plan: dict | None = None
    executed_tasks: list[str] = Field(default_factory=list)


def _coerce_state(state: EditState | dict[str, Any]) -> EditState:
    if isinstance(state, EditState):
        return state
    return EditState(**state)


def _get_or_fallback_session(session_id: str):
    try:
        return session_store.get(session_id)
    except KeyError:
        from app.core.config import settings
        from app.schemas.schemas import LLMProvider
        return session_store.create(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY or "sk-fallback-placeholder",
            session_id=session_id
        )


_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval_math(expr: str) -> float | int | None:
    try:
        clean_expr = expr.strip().replace("$", "").replace(",", "")
        tree = ast.parse(clean_expr, mode='eval')
        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            elif isinstance(node, ast.BinOp):
                op_type = type(node.op)
                if op_type in _SAFE_OPERATORS:
                    left = _eval(node.left)
                    right = _eval(node.right)
                    return _SAFE_OPERATORS[op_type](left, right)
            elif isinstance(node, ast.UnaryOp):
                op_type = type(node.op)
                if op_type in _SAFE_OPERATORS:
                    return _SAFE_OPERATORS[op_type](_eval(node.operand))
            raise ValueError(f"Unsupported node: {type(node)}")
        return _eval(tree)
    except Exception as e:
        logger.warning(f"Failed safe math evaluation for '{expr}': {e}")
        return None


def _find_segment(identifier: str | None, segments: list[DocumentSegment]) -> DocumentSegment | None:
    if not identifier or not segments:
        return None
    ident = str(identifier).strip().lower()
    for seg in segments:
        s_name = seg.name.lower()
        if ident == s_name or ident in s_name or s_name in ident:
            return seg
    m = re.search(r'(?:section|page)?\s*(\d+)', ident)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(segments):
            return segments[idx]
    ordinals = {
        "first": 0, "1st": 0,
        "second": 1, "2nd": 1,
        "third": 2, "3rd": 2,
        "fourth": 3, "4th": 3,
        "fifth": 4, "5th": 4,
        "last": len(segments) - 1,
    }
    for ord_word, idx in ordinals.items():
        if ord_word in ident and 0 <= idx < len(segments):
            return segments[idx]
    return None


def _detect_ribbon_commands(prompt: str) -> list[RibbonActionCommand]:
    p = prompt.strip().lower()
    results: list[RibbonActionCommand] = []

    # 1. Watermark
    m_wm = re.search(r'(?:watermark)\s*(?:to\s*|:\s*)?["\']?([^,"\';]+)["\']?', p)
    if m_wm:
        wm_text = m_wm.group(1).strip().upper()
        if wm_text in ("NONE", "REMOVE", "CLEAR", "NO"):
            wm_text = ""
        results.append(RibbonActionCommand(action_type="set_watermark", watermark=wm_text))
    elif any(k in p for k in ["remove watermark", "clear watermark", "no watermark"]):
        results.append(RibbonActionCommand(action_type="set_watermark", watermark=""))

    # 2. Font family
    known_fonts = [
        "times new roman", "merriweather", "playfair display", "courier new", "comic sans ms",
        "inter", "roboto", "arial", "georgia"
    ]
    for f in known_fonts:
        if re.search(r'(?:font(?:\s+family)?(?:\s+to)?\s+|family\s+)' + re.escape(f), p) or f"font {f}" in p:
            font_repr = "Times New Roman" if f == "times new roman" else "Courier New" if f == "courier new" else "Playfair Display" if f == "playfair display" else f.title()
            results.append(RibbonActionCommand(action_type="set_font", font_family=font_repr))
            break

    # 3. Font size
    m_sz = re.search(r'(?:font\s*size|size)(?:\s+to)?\s*[:\s]?\s*(\d+(?:px|pt)?)', p)
    if m_sz:
        sz = m_sz.group(1).strip()
        if not sz.endswith("px") and not sz.endswith("pt"):
            sz = f"{sz}px"
        results.append(RibbonActionCommand(action_type="set_font_size", font_size=sz))

    # 4. Page / Background Color
    m_col = re.search(r'(?:page\s+color|background\s+color)(?:\s+to)?\s*[:\s]?\s*(#[0-9a-fA-F]{3,6}|[a-z]+)', p)
    if m_col:
        results.append(RibbonActionCommand(action_type="set_page_color", page_color=m_col.group(1).strip()))

    # 5. Accent Color
    m_acc = re.search(r'accent\s+color(?:\s+to)?\s*[:\s]?\s*(#[0-9a-fA-F]{3,6}|[a-z]+)', p)
    if m_acc:
        results.append(RibbonActionCommand(action_type="set_accent_color", accent_color=m_acc.group(1).strip()))

    # 6. Page Border
    m_bor = re.search(r'(?:page\s+border|border)(?:\s+to)?\s*[:\s]?\s*([a-z0-9\s]+)', p)
    if m_bor:
        results.append(RibbonActionCommand(action_type="set_page_border", page_border=m_bor.group(1).strip()))

    # 7. Paper size
    for ps in ["a4", "letter", "legal", "a3"]:
        if re.search(r'\b(?:paper|page)?\s*size\s+' + ps + r'\b', p) or f"set to {ps}" in p or p == ps:
            results.append(RibbonActionCommand(action_type="set_paper_size", paper_size=ps.upper() if ps in ("a4", "a3") else ps.capitalize()))
            break

    # 8. Tables
    m_tbl = re.search(r'insert\s+(?:a\s+)?table(?:\s+(\d+)\s*[xX*]\s*(\d+))?', p)
    if m_tbl or any(k in p for k in ["add table", "insert table", "create table"]):
        rows = int(m_tbl.group(1)) if m_tbl and m_tbl.group(1) else 3
        cols = int(m_tbl.group(2)) if m_tbl and m_tbl.group(2) else 3
        results.append(RibbonActionCommand(action_type="insert_table", table_rows=rows, table_cols=cols))

    # 9. Zoom
    m_zm = re.search(r'zoom(?:\s+to)?\s*[:\s]?\s*(\d+)', p)
    if m_zm:
        results.append(RibbonActionCommand(action_type="set_zoom", zoom_level=int(m_zm.group(1))))

    # 10. Spacing
    m_sp = re.search(r'(?:line\s+spacing|paragraph\s+spacing|spacing)(?:\s+to)?\s*[:\s]?\s*([0-9\.]+|single|double|1\.5)', p)
    if m_sp:
        results.append(RibbonActionCommand(action_type="set_spacing", spacing=m_sp.group(1).strip()))

    # 11. Basic quick commands
    if "undo" in p or "revert" in p:
        results.append(RibbonActionCommand(action_type="undo"))
    if "redo" in p:
        results.append(RibbonActionCommand(action_type="redo"))
    if any(k in p for k in ["clear formatting", "remove formatting", "strip formatting"]):
        results.append(RibbonActionCommand(action_type="clear_formatting"))
    if any(k in p for k in ["add page", "insert page", "new blank page"]):
        results.append(RibbonActionCommand(action_type="add_page"))

    return results


def _detect_ribbon_command(prompt: str) -> RibbonActionCommand | None:
    cmds = _detect_ribbon_commands(prompt)
    return cmds[0] if cmds else None


async def classifier_node(state_input: EditState | dict[str, Any]) -> dict[str, Any]:
    state = _coerce_state(state_input)
    session = _get_or_fallback_session(state.session_id)
    raw_lower = state.raw_prompt.lower()
    
    detected_ribbons = _detect_ribbon_commands(state.raw_prompt)
    edit_verbs = [
        "edit", "update", "rewrite", "replace", "add section", "new section", 
        "expand", "move image", "move diagram", "move the diagram", "relocate", 
        "calculate", "math", "clause", "paragraph", "appendix", "in section", 
        "to section", "mention", "describe", "summarize", "delete section", "remove section"
    ]
    has_edit_verbs = any(v in raw_lower for v in edit_verbs)
    
    # Pure ribbon formatting fast-path: zero tokens, 0ms latency
    if detected_ribbons and not has_edit_verbs:
        if len(detected_ribbons) == 1:
            r = detected_ribbons[0]
            logger.info(f"Direct ribbon action detected: {r.action_type}")
            return {
                "intent": "ribbon_command",
                "target_segment_name": None,
                "target_segment_names": [],
                "chat_reply": f"Applied {r.action_type.replace('_', ' ')} cleanly.",
                "ribbon_action": r.model_dump(),
                "ribbon_actions": [r.model_dump()],
                "executed_tasks": [f"Formatting: {r.action_type}"],
            }
        else:
            logger.info(f"Direct multi-ribbon actions detected: {len(detected_ribbons)} actions")
            return {
                "intent": "multitask",
                "target_segment_name": None,
                "target_segment_names": [],
                "chat_reply": f"Applied {len(detected_ribbons)} formatting updates cleanly.",
                "ribbon_action": detected_ribbons[0].model_dump(),
                "ribbon_actions": [r.model_dump() for r in detected_ribbons],
                "executed_tasks": [f"Formatting: {r.action_type}" for r in detected_ribbons],
            }

    segment_names = [f"{i+1}. {seg.name}" for i, seg in enumerate(state.segments)]
    session_history = session.get_formatted_history() if hasattr(session, "get_formatted_history") else ""
    
    prompt = (
        f"You are the CoPilot Intent Classifier and Task Decomposer for an enterprise document editor.\n"
        f"Analyze the user query: '{state.raw_prompt}'\n\n"
        f"Session Chat History:\n{session_history}\n\n"
        f"Document Segments Available (in order):\n" + "\n".join(segment_names) + "\n\n"
        f"DECISION RULES:\n"
        f"1. 'multitask': If the user query contains MULTIPLE distinct operations across domains or sections (e.g. styling + editing a section, editing section 1 + moving an image to section 2, editing a section + adding a new section, or multiple separate tasks). You MUST populate multi_plan with the decoupled sub-tasks!\n"
        f"2. 'ribbon_command': Pure styling or page layout change (font, size, watermark, page color, paper size, spacing, zoom, insert table, etc.).\n"
        f"3. 'edit_segment': Targeted edit to ONE specific section (set target_segment_name).\n"
        f"4. 'edit_multi_segments': Global update across MULTIPLE sections or the whole document (e.g. 'update pricing everywhere', 'remake entire document', or target_segment_names=['all']).\n"
        f"5. 'expand_document': Purely adding a single brand new section/appendix.\n"
        f"6. 'chat': Pure conversational question or inquiry about the document without requesting edits.\n\n"
        f"For any compound request, classify intent as 'multitask' and provide each granular task in multi_plan.tasks with its corresponding task_type ('ribbon_command', 'edit_segment', 'relocate_image', 'expand_document', 'math_calculation')."
    )
    
    try:
        model = get_chat_model(session, temperature=0.2)
        intent_classifier = model.with_structured_output(CoPilotIntentClassification)
        intent_result = await intent_classifier.ainvoke(prompt)
        logger.info(f"Classified intent: {intent_result.intent}, target: {intent_result.target_segment_name}, targets: {intent_result.target_segment_names}")
        
        is_multitask = intent_result.intent == "multitask" or (
            intent_result.multi_plan and len(intent_result.multi_plan.tasks) > 1
        )
        
        if is_multitask:
            multi_plan = intent_result.multi_plan
            if not multi_plan:
                multi_plan = CoPilotMultiTaskPlan(is_compound=True, tasks=[])
            
            # Ensure any pre-detected ribbon actions are included
            for r in detected_ribbons:
                if not any(t.task_type == "ribbon_command" and t.ribbon_action and t.ribbon_action.action_type == r.action_type for t in multi_plan.tasks):
                    multi_plan.tasks.insert(0, CoPilotTaskAction(
                        task_type="ribbon_command",
                        instruction=f"Apply {r.action_type}",
                        ribbon_action=r
                    ))
            
            return {
                "intent": "multitask",
                "target_segment_name": intent_result.target_segment_name,
                "target_segment_names": intent_result.target_segment_names or [],
                "chat_reply": intent_result.chat_reply,
                "ribbon_action": detected_ribbons[0].model_dump() if detected_ribbons else (intent_result.ribbon_action.model_dump() if intent_result.ribbon_action else None),
                "ribbon_actions": [r.model_dump() for r in detected_ribbons],
                "multi_plan": multi_plan.model_dump(),
            }
            
        return {
            "intent": intent_result.intent,
            "target_segment_name": intent_result.target_segment_name,
            "target_segment_names": intent_result.target_segment_names or [],
            "chat_reply": intent_result.chat_reply,
            "ribbon_action": intent_result.ribbon_action.model_dump() if intent_result.ribbon_action else (detected_ribbons[0].model_dump() if detected_ribbons else None),
            "ribbon_actions": [detected_ribbons[0].model_dump()] if detected_ribbons else ([]),
        }
    except Exception as e:
        logger.error(f"Error in classifier_node LLM call: {e}", exc_info=True)
        if any(kw in raw_lower for kw in ["rewrite all", "entire document", "whole document", "remake", "all sections"]):
            return {"intent": "edit_multi_segments", "target_segment_name": None, "target_segment_names": ["all"], "chat_reply": "Updating document sections..."}
        if any(kw in raw_lower for kw in ["add section", "new section", "appendix", "insert page", "create section"]):
            return {"intent": "expand_document", "target_segment_name": None, "target_segment_names": [], "chat_reply": "Adding new section..."}
        if any(kw in raw_lower for kw in ["edit", "change", "update", "rewrite", "replace", "fix", "modify"]):
            first_name = state.segments[0].name if state.segments else None
            return {"intent": "edit_segment", "target_segment_name": first_name, "target_segment_names": [], "chat_reply": "Updating section..."}
        return {"intent": "chat", "target_segment_name": None, "target_segment_names": [], "chat_reply": f"I received your request: '{state.raw_prompt}'. You can ask me to reformat, edit sections, or add new content."}


async def chat_node(state_input: EditState | dict[str, Any]) -> dict[str, Any]:
    state = _coerce_state(state_input)
    reply = state.chat_reply or "I evaluated the document context. Let me know if you would like me to modify any specific section or apply global updates."
    return {"chat_reply": reply}


async def ribbon_node(state_input: EditState | dict[str, Any]) -> dict[str, Any]:
    state = _coerce_state(state_input)
    action = "action"
    if isinstance(state.ribbon_action, dict):
        action = state.ribbon_action.get("action_type") or "action"
    elif hasattr(state.ribbon_action, "action_type"):
        action = getattr(state.ribbon_action, "action_type") or "action"
    reply = state.chat_reply or f"Executed ribbon command '{action}' cleanly!"
    return {"chat_reply": reply}


async def surgical_edit_node(state_input: EditState | dict[str, Any]) -> dict[str, Any]:
    state = _coerce_state(state_input)
    
    target_seg = _find_segment(state.target_segment_name or state.raw_prompt, state.segments)
    if not target_seg:
        if len(state.segments) == 1:
            target_seg = state.segments[0]
        else:
            return {"chat_reply": f"I couldn't identify which section you wanted to edit. Available sections: {', '.join([s.name for s in state.segments])}."}
        
    session = _get_or_fallback_session(state.session_id)
    model = get_chat_model(session, temperature=0.4)
    editor_model = model.with_structured_output(SegmentEditResult)
    
    outline = ", ".join([s.name for s in state.segments if s.segment_id != target_seg.segment_id])

    existing_text_parts = []
    preserve_images = []
    if isinstance(target_seg.content, dict):
        for node in target_seg.content.get("content", []):
            if node.get("type") == "image":
                preserve_images.append(node)
            elif "content" in node:
                node_text = "".join(c.get("text", "") for c in node.get("content", []) if isinstance(c, dict))
                if node_text:
                    existing_text_parts.append(node_text)
    existing_segment_text = "\n".join(existing_text_parts) if existing_text_parts else "No previous text."

    edit_prompt = (
        f"Surgically edit the single segment '{target_seg.name}'.\n"
        f"{COPILOT_ENTERPRISE_EDIT_GUIDELINES}\n"
        f"User edit instruction: {state.raw_prompt}\n\n"
        f"Existing Segment Content:\n{existing_segment_text}\n\n"
        f"Session Memory:\n{session.get_formatted_history() if hasattr(session, 'get_formatted_history') else ''}\n\n"
        f"Context - Other document sections include: {outline}\n"
        f"Apply the user's requested edit precisely to the existing content while maintaining tonal, structural, and logical consistency.\n\n"
        f"Return updated heading, 2-3 key_metrics (e.g. Uptime, Latency, RTO), optional callout_title & callout_text, body paragraphs, structured sub-sections (with descriptive sub_heading and paragraphs), bullets, and optional tables."
    )
    
    try:
        content = await editor_model.ainvoke(edit_prompt)
        target_idx = next((i + 1 for i, s in enumerate(state.segments) if s.segment_id == target_seg.segment_id), None)
        nodes = segment_edit_result_to_nodes(content, target_seg.name, preserve_images=preserve_images, seg_index=target_idx)
        if nodes and nodes[0].get("type") == "heading":
            raw_h = "".join(c.get("text", "") for c in nodes[0].get("content", []) if isinstance(c, dict)).strip()
            if raw_h:
                target_seg.name = raw_h
        target_seg.content = build_tiptap_segment_doc(nodes)
        target_seg.compliance_flag = False
        target_seg.compliance_note = None
        reply = f"Surgically updated section '{target_seg.name}' cleanly!"
    except Exception as e:
        logger.error(f"Error in surgical_edit_node: {e}", exc_info=True)
        reply = f"Could not complete section edit: {str(e)[:100]}. Section remains unchanged."
    
    return {
        "segments": state.segments,
        "chat_reply": reply
    }


async def bulk_edit_node(state_input: EditState | dict[str, Any]) -> dict[str, Any]:
    state = _coerce_state(state_input)
    session = _get_or_fallback_session(state.session_id)
    model = get_chat_model(session, temperature=0.3)
    editor_model = model.with_structured_output(SegmentEditResult)

    targets = [t.lower().strip() for t in (state.target_segment_names or [])]
    is_all = "all" in targets or "*" in targets or len(targets) == 0 or any(kw in state.raw_prompt.lower() for kw in ["whole document", "entire document", "remake", "all pages", "all sections"])

    segments_to_edit: list[DocumentSegment] = []
    if is_all:
        segments_to_edit = state.segments
    else:
        for seg in state.segments:
            s_name = seg.name.lower()
            if any(t in s_name or s_name in t for t in targets):
                segments_to_edit.append(seg)
    
    if not segments_to_edit:
        segments_to_edit = state.segments

    semaphore = asyncio.Semaphore(4)

    async def _edit_single_seg(seg: DocumentSegment) -> None:
        async with semaphore:
            existing_text_parts = []
            preserve_images = []
            if isinstance(seg.content, dict):
                for node in seg.content.get("content", []):
                    if node.get("type") == "image":
                        preserve_images.append(node)
                    elif "content" in node:
                        node_text = "".join(c.get("text", "") for c in node.get("content", []) if isinstance(c, dict))
                        if node_text:
                            existing_text_parts.append(node_text)
            existing_segment_text = "\n".join(existing_text_parts) if existing_text_parts else "No previous text."

            edit_prompt = (
                f"You are modifying the section '{seg.name}' as part of a global document update.\n"
                f"{COPILOT_ENTERPRISE_EDIT_GUIDELINES}\n"
                f"Global User Request: {state.raw_prompt}\n\n"
                f"Existing Section Content:\n{existing_segment_text}\n\n"
                f"Session Memory:\n{session.get_formatted_history() if hasattr(session, 'get_formatted_history') else ''}\n\n"
                f"Instructions:\n"
                f"Apply the user's requested change to this section if relevant while preserving all other details intact.\n"
                f"Return updated heading, 2-3 key_metrics (e.g. Uptime, Latency, RTO), optional callout_title & callout_text, body paragraphs, structured sub-sections (with sub_heading and paragraphs), bullets, and optional tables."
            )
            try:
                content = await editor_model.ainvoke(edit_prompt)
                seg_idx = next((i + 1 for i, s in enumerate(state.segments) if s.segment_id == seg.segment_id), None)
                nodes = segment_edit_result_to_nodes(content, seg.name, preserve_images=preserve_images, seg_index=seg_idx)
                if nodes and nodes[0].get("type") == "heading":
                    raw_h = "".join(c.get("text", "") for c in nodes[0].get("content", []) if isinstance(c, dict)).strip()
                    if raw_h:
                        seg.name = raw_h
                seg.content = build_tiptap_segment_doc(nodes)
                seg.compliance_flag = False
                seg.compliance_note = None
            except Exception as e:
                logger.error(f"Error editing segment '{seg.name}' in bulk_edit_node: {e}", exc_info=True)

    await asyncio.gather(*[_edit_single_seg(s) for s in segments_to_edit])

    names_edited = ", ".join([s.name for s in segments_to_edit[:3]])
    if len(segments_to_edit) > 3:
        names_edited += f" and {len(segments_to_edit) - 3} more"

    return {
        "segments": state.segments,
        "chat_reply": f"Applied changes across {len(segments_to_edit)} sections ({names_edited})!"
    }


async def document_expansion_node(state_input: EditState | dict[str, Any]) -> dict[str, Any]:
    state = _coerce_state(state_input)
    session = _get_or_fallback_session(state.session_id)
    model = get_chat_model(session, temperature=0.5)
    expander_model = model.with_structured_output(SegmentEditResult)
    
    outline = ", ".join([s.name for s in state.segments])
    
    prompt = (
        f"The user wants to add a new section to the document based on: '{state.raw_prompt}'.\n"
        f"{COPILOT_ENTERPRISE_EDIT_GUIDELINES}\n"
        f"Current sections: {outline}\n"
        f"Generate a brand new segment with a distinct heading, 2-3 key_metrics (e.g. Uptime, Latency, RTO), optional callout_title & callout_text, structured sub-sections (sub_heading and paragraphs), bullets, and optional tables that seamlessly fits into this document."
    )
    
    try:
        content = await expander_model.ainvoke(prompt)
        nodes = segment_edit_result_to_nodes(content, content.heading or "New Section")
        
        new_seg = DocumentSegment(
            segment_id=f"seg_{uuid.uuid4().hex[:8]}",
            name=content.heading or "New Section",
            segment_type="text",
            content=build_tiptap_segment_doc(nodes)
        )
        
        state.segments.append(new_seg)
        reply = f"Added brand new section: '{new_seg.name}'!"
    except Exception as e:
        logger.error(f"Error in document_expansion_node: {e}", exc_info=True)
        reply = f"Could not create new section: {str(e)[:100]}."
    
    return {
        "segments": state.segments,
        "chat_reply": reply
    }


async def multitask_orchestrator_node(state_input: EditState | dict[str, Any]) -> dict[str, Any]:
    state = _coerce_state(state_input)
    session = _get_or_fallback_session(state.session_id)
    executed_tasks: list[str] = list(state.executed_tasks or [])
    ribbon_actions: list[dict] = list(state.ribbon_actions or [])
    
    plan_dict = state.multi_plan
    tasks: list[CoPilotTaskAction] = []
    if plan_dict and "tasks" in plan_dict:
        for t in plan_dict["tasks"]:
            tasks.append(t if isinstance(t, CoPilotTaskAction) else CoPilotTaskAction(**t))
            
    # 1. Gather all ribbon actions from tasks and detected ribbons
    detected_ribbons = _detect_ribbon_commands(state.raw_prompt)
    for r in detected_ribbons:
        r_dump = r.model_dump()
        if not any(existing.get("action_type") == r.action_type for existing in ribbon_actions):
            ribbon_actions.append(r_dump)
            
    for task in tasks:
        if task.task_type == "ribbon_command" and task.ribbon_action:
            r_dump = task.ribbon_action.model_dump()
            if not any(existing.get("action_type") == task.ribbon_action.action_type for existing in ribbon_actions):
                ribbon_actions.append(r_dump)
            desc = f"Styling: {task.ribbon_action.action_type.replace('_', ' ')}"
            if desc not in executed_tasks:
                executed_tasks.append(desc)

    for r_item in ribbon_actions:
        desc = f"Styling: {r_item.get('action_type', '').replace('_', ' ')}"
        if desc not in executed_tasks:
            executed_tasks.append(desc)

    # 2. Execute Image Relocations
    relocate_tasks = [t for t in tasks if t.task_type == "relocate_image"]
    for rel in relocate_tasks:
        src_seg = _find_segment(rel.target_segment, state.segments)
        dst_seg = _find_segment(rel.destination_segment, state.segments)
        if src_seg and dst_seg and src_seg.segment_id != dst_seg.segment_id:
            moved_images = []
            if isinstance(src_seg.content, dict) and "content" in src_seg.content:
                new_src_content = []
                for node in src_seg.content["content"]:
                    if node.get("type") == "image":
                        moved_images.append(node)
                    else:
                        new_src_content.append(node)
                src_seg.content["content"] = new_src_content
            
            if moved_images and isinstance(dst_seg.content, dict) and "content" in dst_seg.content:
                new_dst_content = []
                inserted = False
                for node in dst_seg.content["content"]:
                    new_dst_content.append(node)
                    if node.get("type") == "heading" and not inserted:
                        new_dst_content.extend(moved_images)
                        inserted = True
                if not inserted:
                    new_dst_content.extend(moved_images)
                dst_seg.content["content"] = new_dst_content
                executed_tasks.append(f"Moved {len(moved_images)} diagram(s) from '{src_seg.name}' to '{dst_seg.name}'")
            elif not moved_images:
                executed_tasks.append(f"No diagram assets found in '{src_seg.name}' to relocate")
        else:
            executed_tasks.append(f"Could not relocate diagram: invalid source ({rel.target_segment}) or destination ({rel.destination_segment})")

    # 3. Deterministic Math REPL Calculations
    math_tasks = [t for t in tasks if t.task_type == "math_calculation"]
    for mtask in math_tasks:
        if mtask.math_expression:
            val = safe_eval_math(mtask.math_expression)
            if val is not None:
                calc_str = f"{val:,.2f}" if isinstance(val, float) else f"{val}"
                executed_tasks.append(f"Calculated: {mtask.math_expression} = {calc_str}")
                target_seg = _find_segment(mtask.target_segment, state.segments)
                if target_seg and isinstance(target_seg.content, dict) and "content" in target_seg.content:
                    target_seg.content["content"].append(tiptap_paragraph_node(f"Calculated Total: {calc_str}"))

    # 4. Surgical Content Edits (Executed in parallel via asyncio.gather)
    edit_tasks = [t for t in tasks if t.task_type == "edit_segment"]
    if edit_tasks:
        model = get_chat_model(session, temperature=0.35)
        editor_model = model.with_structured_output(SegmentEditResult)

        async def _run_single_surgical_edit(task: CoPilotTaskAction) -> str:
            target_seg = _find_segment(task.target_segment, state.segments)
            if not target_seg:
                return f"Could not find section '{task.target_segment}' for edit"
            
            existing_text_parts = []
            preserve_images = []
            if isinstance(target_seg.content, dict):
                for node in target_seg.content.get("content", []):
                    if node.get("type") == "image":
                        preserve_images.append(node)
                    elif "content" in node:
                        node_text = "".join(c.get("text", "") for c in node.get("content", []) if isinstance(c, dict))
                        if node_text:
                            existing_text_parts.append(node_text)
            existing_text = "\n".join(existing_text_parts) if existing_text_parts else "No previous text."

            outline = ", ".join([s.name for s in state.segments if s.segment_id != target_seg.segment_id])
            edit_prompt = (
                f"Surgically edit the document section '{target_seg.name}'.\n"
                f"{COPILOT_ENTERPRISE_EDIT_GUIDELINES}\n"
                f"Specific Task Instruction: {task.instruction}\n\n"
                f"Existing Section Content:\n{existing_text}\n\n"
                f"Session Memory:\n{session.get_formatted_history() if hasattr(session, 'get_formatted_history') else ''}\n\n"
                f"Other sections: {outline}\n"
                f"Apply the specific edit cleanly while keeping all other details intact.\n"
                f"Return updated heading, 2-3 key_metrics (e.g. Uptime, Latency, RTO), optional callout_title & callout_text, body paragraphs, structured sub-sections (with sub_heading and paragraphs), bullets, and optional tables."
            )
            try:
                content = await editor_model.ainvoke(edit_prompt)
                target_idx = next((i + 1 for i, s in enumerate(state.segments) if s.segment_id == target_seg.segment_id), None)
                nodes = segment_edit_result_to_nodes(content, target_seg.name, preserve_images=preserve_images, seg_index=target_idx)
                if nodes and nodes[0].get("type") == "heading":
                    raw_h = "".join(c.get("text", "") for c in nodes[0].get("content", []) if isinstance(c, dict)).strip()
                    if raw_h:
                        target_seg.name = raw_h
                target_seg.content = build_tiptap_segment_doc(nodes)
                target_seg.compliance_flag = False
                target_seg.compliance_note = None
                return f"Updated section '{target_seg.name}'"
            except Exception as e:
                logger.error(f"Error in surgical edit for '{target_seg.name}': {e}", exc_info=True)
                return f"Failed to edit '{target_seg.name}': {str(e)[:50]}"

        edit_results = await asyncio.gather(*[_run_single_surgical_edit(t) for t in edit_tasks])
        for r_text in edit_results:
            executed_tasks.append(r_text)

    # 5. Document Expansions (Executed in parallel via asyncio.gather)
    expand_tasks = [t for t in tasks if t.task_type == "expand_document"]
    if expand_tasks:
        model = get_chat_model(session, temperature=0.5)
        expander_model = model.with_structured_output(SegmentEditResult)

        async def _run_single_expansion(task: CoPilotTaskAction) -> tuple[DocumentSegment | None, str]:
            outline = ", ".join([s.name for s in state.segments])
            prompt = (
                f"The user wants to add a new section based on: '{task.instruction}'.\n"
                f"{COPILOT_ENTERPRISE_EDIT_GUIDELINES}\n"
                f"Current sections: {outline}\n"
                f"Generate a brand new segment with a distinct heading, 2-3 key_metrics, optional callout_title & callout_text, structured sub-sections, bullets, and optional tables."
            )
            try:
                content = await expander_model.ainvoke(prompt)
                new_idx = len(state.segments) + 1
                nodes = segment_edit_result_to_nodes(content, content.heading or "New Section", seg_index=new_idx)
                clean_title = re.sub(r'^\d+\.\s*', '', content.heading or "New Section").strip()
                h1_name = f"{new_idx}. {clean_title}"
                new_seg = DocumentSegment(
                    segment_id=f"seg_{uuid.uuid4().hex[:8]}",
                    name=h1_name,
                    segment_type="text",
                    content=build_tiptap_segment_doc(nodes)
                )
                return new_seg, f"Added new section: '{new_seg.name}'"
            except Exception as e:
                logger.error(f"Error expanding document for '{task.instruction}': {e}", exc_info=True)
                return None, f"Failed to add section: {str(e)[:50]}"

        expansion_results = await asyncio.gather(*[_run_single_expansion(t) for t in expand_tasks])
        for new_seg, msg in expansion_results:
            if new_seg:
                state.segments.append(new_seg)
            executed_tasks.append(msg)

    task_bullets = "\n".join([f"• {t}" for t in executed_tasks])
    reply = f"Successfully orchestrated {len(executed_tasks)} compound operations:\n{task_bullets}"

    return {
        "segments": state.segments,
        "ribbon_actions": ribbon_actions,
        "ribbon_action": ribbon_actions[0] if ribbon_actions else None,
        "executed_tasks": executed_tasks,
        "chat_reply": reply,
    }


def route_intent(state_input: EditState | dict[str, Any]) -> str:
    state = _coerce_state(state_input)
    intent = state.intent
    if intent == "multitask":
        return "multitask_orchestrator"
    elif intent == "edit_segment":
        return "surgical_edit"
    elif intent == "edit_multi_segments":
        return "bulk_edit"
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
workflow.add_node("bulk_edit", bulk_edit_node)
workflow.add_node("document_expansion", document_expansion_node)
workflow.add_node("multitask_orchestrator", multitask_orchestrator_node)

workflow.set_entry_point("classifier")

workflow.add_conditional_edges(
    "classifier",
    route_intent,
    {
        "chat": "chat",
        "ribbon": "ribbon",
        "surgical_edit": "surgical_edit",
        "bulk_edit": "bulk_edit",
        "document_expansion": "document_expansion",
        "multitask_orchestrator": "multitask_orchestrator"
    }
)

workflow.add_edge("chat", END)
workflow.add_edge("ribbon", END)
workflow.add_edge("surgical_edit", END)
workflow.add_edge("bulk_edit", END)
workflow.add_edge("document_expansion", END)
workflow.add_edge("multitask_orchestrator", END)

edit_graph = workflow.compile()
