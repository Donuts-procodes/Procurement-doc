import pytest
from app.agents.conversational_agent import ProcurementAgent


def test_procurement_agent_defaults():
    agent = ProcurementAgent()
    req = agent._required("rfq")
    assert len(req) == 6
    assert req[0]["key"] == "organization_name"

    collected = {"organization_name": "Acme", "requirement_summary": "Cloud Storage"}
    missing = agent._missing_fields(req, collected)
    missing_keys = {m["key"] for m in missing}
    assert missing_keys == {"budget_range", "delivery_timeline", "submission_deadline", "contact_person.name"}

    all_filled = {f["key"]: "filled" for f in req}
    assert agent._missing_fields(req, all_filled) == []


def test_procurement_agent_custom_mandatory_fields():
    agent = ProcurementAgent()
    agent.set_mandatory_fields(["org_name", "target_budget"])
    req = agent._required("rfq")
    assert len(req) == 2
    assert req[0]["key"] == "org_name"
    assert req[1]["key"] == "target_budget"

    agent.set_mandatory_fields({
        "rfq": ["budget_only"],
        "rfp": [{"key": "scope", "label": "Project Scope", "example": "Full revamp"}]
    })
    assert [f["key"] for f in agent._required("rfq")] == ["budget_only"]
    assert [f["key"] for f in agent._required("rfp")] == ["scope"]
    assert agent._required("rfp")[0]["label"] == "Project Scope"


@pytest.mark.asyncio
async def test_session_lifecycle():
    agent = ProcurementAgent()
    sid, greeting = agent.create_session()
    assert sid in agent._sessions
    assert "Procurement" in greeting or "RFQ" in greeting

    agent.end_session(sid)
    assert sid not in agent._sessions

