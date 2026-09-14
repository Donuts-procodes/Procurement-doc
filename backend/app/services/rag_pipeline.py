from __future__ import annotations

import logging
import os
import uuid
from typing import Any
from pydantic import BaseModel, Field

from app.db.clause_store import clause_store
from app.core.session import SessionConfig
from app.schemas.schemas import ProcurementDocType
from app.services.llm_providers import get_chat_model
from app.services.procurement_templates import SectionSchema, get_procurement_sections
from app.services.structured_tables import (
    LineItemTableData,
    PaymentScheduleData,
    compute_line_items,
    compute_payment_schedule,
)
from app.services.template_engine import (
    approved_clause_node,
    bullet_list_node,
    build_document_root,
    compliance_warning_node,
    heading_node,
    paragraph_node,
    table_node,
)
from app.services.vector_store import KnowledgeBase

logger = logging.getLogger("gdocs.rag_pipeline")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class PageOutlineItem(BaseModel):
    title: str = Field(description="Heading for this section")
    section_type: str = Field(default="prose")
    guidance: str = Field(default="")


class DocumentOutline(BaseModel):
    pages: list[PageOutlineItem]


class ProseContent(BaseModel):
    heading: str
    paragraphs: list[str] | None = Field(default_factory=list)
    bullets: list[str] | None = Field(default_factory=list)


class ClauseValidation(BaseModel):
    has_conflict: bool = Field(description="True if clause contradicts retrieved policy guidelines")
    explanation: str = Field(description="Explanation of policy grounding or conflict")


class GeneratedDocument(BaseModel):
    document_id: str
    lexical_state: dict
    page_titles: list[str]


def generate_outline(procurement_doc_type: ProcurementDocType, num_pages: int | None = None) -> DocumentOutline:
    logger.info(f"Generating section outline for ProcurementDocType='{procurement_doc_type.value}' (target num_pages={num_pages})...")
    sections = get_procurement_sections(procurement_doc_type, num_pages=num_pages)
    outline = DocumentOutline(
        pages=[
            PageOutlineItem(title=sec.title, section_type=sec.section_type, guidance=sec.guidance)
            for sec in sections
        ]
    )
    logger.info(f"Generated outline with {len(outline.pages)} sections: {[p.title for p in outline.pages]}")
    return outline


async def generate_line_items_section(
    session: SessionConfig,
    section_title: str,
    user_prompt: str,
) -> list[dict[str, Any]]:
    logger.info(f"Generating line items table section '{section_title}' via LLM + Python calculator...")
    model = get_chat_model(session, temperature=0.3)
    structured_model = model.with_structured_output(LineItemTableData)
    instruction = (
        f"Generate line items for section '{section_title}'.\n"
        f"Context: {user_prompt}\n"
        f"Produce a list of realistic line items (sku, description, quantity, unit_price) "
        f"and tax percentage."
    )
    raw_data = await structured_model.ainvoke(instruction)
    logger.info(f"LLM generated {len(raw_data.items)} raw line items with tax rate {raw_data.tax_rate_percent}%. Computing exact totals...")
    summary = compute_line_items(raw_data)
    logger.info(f"Line items computed: Subtotal=${summary.subtotal}, Tax=${summary.tax}, Grand Total=${summary.grand_total}")

    headers = ["SKU", "Description", "Qty", "Unit Price", "Total"]
    rows = [
        [item.sku, item.description, str(item.quantity), f"${item.unit_price:.2f}", f"${item.total:.2f}"]
        for item in summary.items
    ]
    rows.append(["", "Subtotal", "", "", f"${summary.subtotal:.2f}"])
    rows.append(["", f"Tax ({raw_data.tax_rate_percent}%)", "", "", f"${summary.tax:.2f}"])
    rows.append(["", "Grand Total", "", "", f"${summary.grand_total:.2f}"])

    return [heading_node(section_title), table_node(headers, rows)]


async def generate_payment_schedule_section(
    session: SessionConfig,
    section_title: str,
    user_prompt: str,
) -> list[dict[str, Any]]:
    logger.info(f"Generating payment schedule table section '{section_title}'...")
    model = get_chat_model(session, temperature=0.3)
    structured_model = model.with_structured_output(PaymentScheduleData)
    instruction = (
        f"Generate payment milestone schedule for section '{section_title}'.\n"
        f"Context: {user_prompt}\n"
        f"Produce milestones (milestone_number, description, percentage, due_condition) "
        f"totaling 100% and total contract value."
    )
    raw_data = await structured_model.ainvoke(instruction)
    logger.info(f"LLM generated {len(raw_data.milestones)} payment milestones for Total Contract Value=${raw_data.total_contract_value}. Computing milestone allocations...")
    summary = compute_payment_schedule(raw_data)
    logger.info(f"Payment schedule computed cleanly for total contract value ${summary.total_contract_value}")

    headers = ["#", "Milestone Deliverable", "Allocation %", "Amount", "Due Condition"]
    rows = [
        [
            str(m.milestone_number),
            m.description,
            f"{m.percentage}%",
            f"${m.amount:.2f}",
            m.due_condition,
        ]
        for m in summary.milestones
    ]
    rows.append(["", "Total Contract Value", "100%", f"${summary.total_contract_value:.2f}", ""])

    return [heading_node(section_title), table_node(headers, rows)]


async def generate_clause_section(
    session: SessionConfig,
    procurement_doc_type: ProcurementDocType,
    section_title: str,
    user_prompt: str,
    policy_kb: KnowledgeBase | None,
) -> list[dict[str, Any]]:
    logger.info(f"Processing clause section '{section_title}' for '{procurement_doc_type.value}'...")
    # Check if approved clause exists in library
    approved = clause_store.get_clause(procurement_doc_type, section_title)
    if approved:
        logger.info(f"Found pre-approved legal clause in library: id='{approved.id}', title='{approved.title}'. Inserting verbatim approved text.")
        return [
            heading_node(section_title),
            approved_clause_node(approved.body, approved.title),
        ]

    logger.info(f"No pre-approved clause found for '{section_title}'. Retrieval-grounding against Policy KB...")
    context_chunks = policy_kb.query(f"{section_title} {user_prompt}", limit=5) if policy_kb else []
    logger.info(f"Retrieved {len(context_chunks)} policy chunks for compliance grounding.")
    policy_context = "\n---\n".join(context_chunks) if context_chunks else "Standard internal procurement guidelines."

    model = get_chat_model(session, temperature=0.4)
    structured_prose = model.with_structured_output(ProseContent)

    draft_instruction = (
        f"Draft legal/compliance clause for section '{section_title}'.\n"
        f"Doc Type: {procurement_doc_type.value}\n"
        f"User Requirement: {user_prompt}\n"
        f"Binding Policy Constraints:\n{policy_context}\n"
        f"Write formal clause text. Do NOT contradict binding policy constraints."
    )
    content = await structured_prose.ainvoke(draft_instruction)

    # Compliance check pass
    logger.info(f"Running secondary LLM compliance check pass on drafted clause...")
    validator = model.with_structured_output(ClauseValidation)
    clause_text = "\n".join(content.paragraphs)
    check_instruction = (
        f"Check this drafted clause against policy constraints.\n"
        f"Clause text:\n{clause_text}\n\n"
        f"Policy constraints:\n{policy_context}\n"
        f"Evaluate if there is any conflict, risk, or ungrounded claim."
    )
    val_result = await validator.ainvoke(check_instruction)
    logger.info(f"Compliance check result: conflict={val_result.has_conflict}, note='{val_result.explanation}'")

    nodes = [heading_node(section_title)]
    if val_result.has_conflict:
        nodes.append(compliance_warning_node(clause_text, val_result.explanation))
    else:
        for p in content.paragraphs:
            nodes.append(paragraph_node(p))

    return nodes


async def generate_prose_section(
    session: SessionConfig,
    procurement_doc_type: ProcurementDocType,
    section: PageOutlineItem,
    user_prompt: str,
    general_kb: KnowledgeBase | None,
) -> list[dict[str, Any]]:
    logger.info(f"Drafting prose section '{section.title}'...")
    context_chunks = general_kb.query(f"{section.title} {user_prompt}", limit=5) if general_kb else []
    logger.info(f"Retrieved {len(context_chunks)} knowledge base chunks for section '{section.title}'.")
    context_block = "\n---\n".join(context_chunks) if context_chunks else "No additional source material available."

    model = get_chat_model(session, temperature=0.5)
    structured_model = model.with_structured_output(ProseContent)
    instruction = (
        f"Draft section '{section.title}' for a procurement {procurement_doc_type.value}.\n"
        f"Guidance: {section.guidance}\n"
        f"User details: {user_prompt}\n"
        f"Knowledge context:\n{context_block}\n"
        f"Write structured prose paragraphs and concise bullets if appropriate."
    )
    content = await structured_model.ainvoke(instruction)
    logger.info(f"Drafted prose section '{section.title}' with {len(content.paragraphs)} paragraphs and {len(content.bullets)} bullets.")

    nodes = [heading_node(content.heading or section.title)]
    for p in content.paragraphs:
        nodes.append(paragraph_node(p))
    if content.bullets:
        nodes.append(bullet_list_node(content.bullets))
    return nodes


async def generate_document(
    session: SessionConfig,
    kb_id: str | None,
    procurement_doc_type: ProcurementDocType,
    num_pages: int,
    prompt: str,
) -> GeneratedDocument:
    doc_id = uuid.uuid4().hex
    logger.info(f"=== Starting document generation task: id='{doc_id}', type='{procurement_doc_type.value}', provider='{session.provider.value}', model='{session.model}' ===")

    outline = generate_outline(procurement_doc_type)

    general_kb = KnowledgeBase(kb_id=kb_id, collection_type="general") if kb_id else None
    policy_kb = KnowledgeBase(kb_id=f"{kb_id}_policy", collection_type="policy") if kb_id else None

    page_node_groups: list[list[dict]] = []
    page_titles: list[str] = []

    for index, section in enumerate(outline.pages, start=1):
        logger.info(f"Step {index}/{len(outline.pages)}: Generating section '{section.title}' (type: {section.section_type})")
        page_titles.append(section.title)

        if section.section_type == "line_items":
            nodes = await generate_line_items_section(session, section.title, prompt)
        elif section.section_type == "payment_schedule":
            nodes = await generate_payment_schedule_section(session, section.title, prompt)
        elif section.section_type == "clause":
            nodes = await generate_clause_section(session, procurement_doc_type, section.title, prompt, policy_kb)
        else:
            nodes = await generate_prose_section(session, procurement_doc_type, section, prompt, general_kb)

        page_node_groups.append(nodes)

    logger.info("Assembling Lexical AST document root...")
    lexical_state = build_document_root(page_node_groups)
    logger.info(f"=== Document generation task completed successfully: id='{doc_id}' ===")

    return GeneratedDocument(
        document_id=doc_id,
        lexical_state=lexical_state,
        page_titles=page_titles,
    )
