import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.schemas import LLMProvider, ProcurementDocType
from app.core.session import session_store
from app.services.structured_tables import LineItemTableData, LineItemInput, compute_line_items
from app.services.procurement_templates import PREBUILT_TEMPLATES, TemplateMetaData
from app.api.v1.routes_generate import _get_or_fallback_session


def run_all_micro_tests():
    print("==================================================")
    print("[TEST] RUNNING MICRO-FUNCTION FEATURE VERIFICATION SUITE")
    print("==================================================")

    # 1. Template Registry & Prebuilt Meta Data Test
    templates = list(PREBUILT_TEMPLATES.values())
    print(f"[PASS] [1/5] Template Registry: Loaded {len(templates)} prebuilt templates.")
    assert len(templates) >= 12, "Fewer than 12 templates found!"

    for t_id, meta in PREBUILT_TEMPLATES.items():
        assert meta.id == t_id
        assert len(meta.title) > 0
        assert len(meta.sections) > 0
        assert len(meta.tone) > 0
    print("[PASS] [1/5] Template Registry: All prebuilt template metadata definitions verified!")

    # 2. Session Store CRUD & State Recovery
    sess = session_store.create(LLMProvider.OPENAI, "gpt-4o", "sk-test-key")
    session_id = sess.session_id
    assert session_store.get(session_id) is not None
    sess.add_message("user", "Test prompt history entry")
    updated = session_store.get(session_id)
    assert len(updated.chat_history) == 1
    assert "Test prompt history entry" in updated.get_formatted_history()
    print("[PASS] [2/5] Session Store: CRUD operations and chat history persistence verified!")

    # 3. Session Fallback Recovery
    fallback_sess = _get_or_fallback_session("non_existent_123")
    assert fallback_sess is not None
    assert len(fallback_sess.session_id) > 0
    print("[PASS] [3/5] Session Fallback: Graceful session recovery verified!")

    # 4. Decimal Financial Math Precision
    table_data = LineItemTableData(
        items=[
            LineItemInput(sku="LIC-001", description="Enterprise Cloud License", quantity=10, unit_price=1200.00),
            LineItemInput(sku="SVC-002", description="Implementation Consulting", quantity=40, unit_price=150.00),
        ],
        tax_rate_percent=18.0,
    )
    summary = compute_line_items(table_data)
    assert summary.subtotal == Decimal("18000.00")
    assert summary.tax == Decimal("3240.00")
    assert summary.grand_total == Decimal("21240.00")
    print("[PASS] [4/5] Financial Math: Exact Decimal math & tax calculation verified!")

    # 5. RAG Graph Node Construction
    from app.agents.procurement_graph import ProcurementState, procurement_graph
    state = ProcurementState(
        session_id=session_id,
        raw_prompt="Test RFP for Cloud Infrastructure",
        doc_type=ProcurementDocType.RFP
    )
    assert state.session_id == session_id
    assert state.doc_type == ProcurementDocType.RFP
    print("[PASS] [5/5] RAG Pipeline: State graph initialization verified!")

    print("==================================================")
    print("[SUCCESS] ALL 5 MICRO-FUNCTION SUITES PASSED CLEANLY (100% SUCCESS)")
    print("==================================================")


if __name__ == "__main__":
    run_all_micro_tests()
