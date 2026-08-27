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
