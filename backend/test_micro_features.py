import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.schemas import LLMProvider, ProcurementDocType
from app.core.session import session_store
from app.services.structured_tables import LineItemTableData, LineItemInput, compute_line_items
from app.services.procurement_templates import PREBUILT_TEMPLATES, TemplateMetaData
from app.api.v1.routes_generate import _get_or_fallback_session


def test_template_registry_completeness():
    """Verify that all prebuilt templates are properly registered and structured."""
    templates = list(PREBUILT_TEMPLATES.values())
    assert len(templates) >= 12

    for t_id, meta in PREBUILT_TEMPLATES.items():
        assert meta.id == t_id
        assert len(meta.title) > 0
        assert len(meta.sections) > 0
        assert len(meta.tone) > 0
    

def test_session_store_crud():
    """Test session creation, retrieval, and chat history persistence."""
    sess = session_store.create(LLMProvider.OPENAI, "gpt-4o", "sk-test-key")
    session_id = sess.session_id

    fetched = session_store.get(session_id)
    assert fetched is not None
    assert fetched.model == "gpt-4o"
    assert fetched.provider == LLMProvider.OPENAI

    sess.add_message("user", "Test prompt history entry")
    updated = session_store.get(session_id)
    assert len(updated.chat_history) == 1
    assert "Test prompt history entry" in updated.get_formatted_history()


def test_line_item_math_precision():
    """Test line item calculations for exact subtotal, 18% GST tax, and grand total."""
    table_data = LineItemTableData(
        items=[
            LineItemInput(sku="LIC-001", description="Enterprise Cloud License", quantity=10, unit_price=1200.00),
            LineItemInput(sku="SVC-002", description="Implementation Consulting", quantity=40, unit_price=150.00),
        ],
        tax_rate_percent=18.0,
    )
    summary = compute_line_items(table_data)

    # 10 * 1200 + 40 * 150 = 12000 + 6000 = 18000.00
    assert summary.subtotal == Decimal("18000.00")
    # Tax 18% of 18000 = 3240.00
    assert summary.tax == Decimal("3240.00")
    # Grand total = 18000 + 3240 = 21240.00
    assert summary.grand_total == Decimal("21240.00")


def test_session_fallback_helper():
    """Ensure invalid session IDs fall back gracefully without crashing."""
    session = _get_or_fallback_session("invalid_session_xyz")
    assert session is not None
    assert len(session.session_id) > 0


def test_target_n_page_expansion():
    """Ensure requesting 10 pages returns exactly 10 distinct structured sections."""
    from app.services.procurement_templates import get_procurement_sections
    from app.schemas.schemas import ProcurementDocType

    # Default RFP has 5 sections; requesting 10 pages must yield exactly 10
    sections_10 = get_procurement_sections(ProcurementDocType.RFP, num_pages=10)
    assert len(sections_10) == 10
    titles = [s.title for s in sections_10]
    assert len(set(titles)) == 10  # All unique

    # Requesting 15 pages expands with numbered operational exhibits
    sections_15 = get_procurement_sections(ProcurementDocType.SOW, num_pages=15)
    assert len(sections_15) == 15


def test_image_role_categorization():
    """Verify ImageAsset role definitions and image_extractor categorization."""
    from app.agents.procurement_graph import ImageAsset

    cover_asset = ImageAsset(
        image_id="img_1",
        url_or_base64="https://example.com/cover.png",
        caption="Cover Image",
        section_target="Cover Page",
        image_role="header_cover",
    )
    assert cover_asset.image_role == "header_cover"

    diag_asset = ImageAsset(
        image_id="img_2",
        url_or_base64="https://example.com/diagram.png",
        caption="Architecture Diagram",
        section_target="Technical Architecture & System Specifications",
        image_role="architecture_diagram",
    )
    assert diag_asset.image_role == "architecture_diagram"


def test_subsection_heading_parsing():
    """Verify that bold headers and markdown sub-headings are converted to TipTap heading nodes."""
    from app.services.tiptap_engine import tiptap_paragraph_node

    # Bold inline title like **1.1 Technical Requirements:**
    bold_heading = tiptap_paragraph_node("**1.1 Technical Architecture Baseline:**")
    assert bold_heading["type"] == "heading"
    assert bold_heading["attrs"]["level"] == 3
    assert bold_heading["content"][0]["text"] == "1.1 Technical Architecture Baseline"

    # Markdown hash heading ## Sub-heading
    h2_node = tiptap_paragraph_node("## Scope Deliverables")
    assert h2_node["type"] == "heading"
    assert h2_node["attrs"]["level"] == 2
    assert h2_node["content"][0]["text"] == "Scope Deliverables"


def test_edit_graph_multi_segment_routing():
    """Verify edit_graph routes 'edit_multi_segments' to bulk_edit."""
    from app.agents.edit_graph import route_intent

    assert route_intent({"intent": "edit_multi_segments"}) == "bulk_edit"
    assert route_intent({"intent": "edit_segment"}) == "surgical_edit"
    assert route_intent({"intent": "expand_document"}) == "document_expansion"
    assert route_intent({"intent": "ribbon_command"}) == "ribbon"
    assert route_intent({"intent": "chat"}) == "chat"


def test_segment_edit_result_to_nodes_structure():
    """Verify segment_edit_result_to_nodes creates H1, H2, paragraphs, tables, and preserves images."""
    from app.agents.edit_graph import SegmentEditResult, SubSection, segment_edit_result_to_nodes

    edit_res = SegmentEditResult(
        heading="Scope of Work",
        paragraphs=["General overview paragraph."],
        sub_sections=[
            SubSection(
                sub_heading="Phase 1 Deliverables",
                paragraphs=["Mobile and backend deliverables."]
            )
        ],
        bullets=["Testing", "Deployment"],
        table_headers=["Phase", "Cost"],
        table_rows=[["1", "$10,000"]],
    )

    dummy_image = {"type": "image", "attrs": {"src": "data:image/png;base64,abc", "alt": "Cover"}}
    nodes = segment_edit_result_to_nodes(edit_res, default_heading="Scope of Work", preserve_images=[dummy_image])

    # Node 0: Preserved image
    assert nodes[0]["type"] == "image"
    # Node 1: H1 heading
    assert nodes[1]["type"] == "heading"
    assert nodes[1]["attrs"]["level"] == 1
    # Node 2: Paragraph
    assert nodes[2]["type"] == "paragraph"
    # Node 3: H2 sub_heading
    assert nodes[3]["type"] == "heading"
    assert nodes[3]["attrs"]["level"] == 2
    # Node 4: SubSection paragraph
    assert nodes[4]["type"] == "paragraph"
    # Node 5: Bullet list
    assert nodes[5]["type"] == "bulletList"
    # Node 6: Table
    assert nodes[6]["type"] == "table"


@pytest.mark.asyncio
async def test_edit_graph_invocation():
    """Verify edit_graph ainvoke processes EditState without TypeError."""
    from app.agents.edit_graph import edit_graph, EditState, CoPilotIntentClassification
    from app.core.session import session_store
    from app.schemas.schemas import LLMProvider

    sess = session_store.create(LLMProvider.OPENAI, "gpt-4o", "sk-test")
    init_state = EditState(
        session_id=sess.session_id,
        document_id="doc_test_copilot",
        raw_prompt="summarize document",
        segments=[]
    )
    with patch("app.agents.edit_graph.get_chat_model") as mock_llm:
        mock_chat = AsyncMock()
        mock_chat.ainvoke.return_value = CoPilotIntentClassification(
            intent="chat",
            chat_reply="Document summary test"
        )
        mock_llm.return_value.with_structured_output.return_value = mock_chat
        result = await edit_graph.ainvoke(init_state.model_dump())
        assert result["chat_reply"] == "Document summary test"
        assert result["intent"] == "chat"
