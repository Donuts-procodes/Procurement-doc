import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.schemas import LLMProvider, ProcurementDocType
from app.core.session import session_store
from app.services.structured_tables import LineItemTableData, LineItemInput, compute_line_items
from app.agents.procurement_graph import ProcurementState, procurement_graph, fillup_agent_node


def test_compute_line_items_exact_decimal_math():
    table_data = LineItemTableData(
        items=[
            LineItemInput(sku="SKU-001", description="Mobile App Design", quantity=2, unit_price=2500.00),
            LineItemInput(sku="SKU-002", description="Backend Server Setup", quantity=1, unit_price=5000.00),
        ],
        tax_rate_percent=10.0,
    )
    summary = compute_line_items(table_data)

    assert summary.subtotal == Decimal("10000.00")
    assert summary.tax == Decimal("1000.00")
    assert summary.grand_total == Decimal("11000.00")
    assert len(summary.items) == 2
    assert summary.items[0].total == Decimal("5000.00")


@pytest.mark.asyncio
async def test_session_fallback_recovery():
    from app.api.v1.routes_generate import _get_or_fallback_session
    invalid_session_id = "non_existent_session_12345"
    
    session = _get_or_fallback_session(invalid_session_id)
    assert session is not None
    assert session.provider == LLMProvider.OPENAI
    assert session.model == "gpt-4o"


@pytest.mark.asyncio
@patch("app.agents.procurement_graph.KnowledgeBase")
@patch("app.agents.procurement_graph.get_chat_model")
async def test_fillup_agent_pdf_rag_extraction(mock_get_chat_model, mock_kb_class):
    session = session_store.create(LLMProvider.OPENAI, "gpt-4o", "sk-test-key-12345678")
    
    mock_kb_instance = MagicMock()
    mock_kb_instance.query.return_value = [
        "TechGropse is to build a Mobile Application (iOS & Android) and Web Admin Panel for property match.",
        "Scope includes user registration, property matching, swipe-based browsing, real-time chat, and admin panel."
    ]
    mock_kb_class.return_value = mock_kb_instance

    mock_llm = MagicMock()
    mock_extractor = AsyncMock()
    mock_extractor.ainvoke.return_value = MagicMock(extracted=True, summary="Mobile App & Web Admin Panel for Property Match")
    mock_llm.with_structured_output.return_value = mock_extractor
    mock_get_chat_model.return_value = mock_llm

    state = ProcurementState(
        session_id=session.session_id,
        raw_prompt="Generate RFP for real estate app",
        doc_type=ProcurementDocType.RFP,
        kb_id="test_property_match_kb"
    )

    res = await fillup_agent_node(state)
    assert "scope_summary" in state.collected_fields
    assert "Property Match" in state.collected_fields["scope_summary"]
