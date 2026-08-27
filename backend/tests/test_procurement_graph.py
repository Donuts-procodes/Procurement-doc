import pytest
from app.agents.procurement_graph import ProcurementState

@pytest.mark.asyncio
async def test_procurement_state_initialization():
    state = ProcurementState(
        session_id="test_session",
        raw_prompt="Generate an RFP",
        status="classifying"
    )
    assert state.session_id == "test_session"
    assert state.raw_prompt == "Generate an RFP"
