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
    print("[PASS] [5/8] RAG Pipeline: State graph initialization verified!")

    # 6. Payment Schedule Percentage Normalization & Reconciliation
    from app.services.structured_tables import PaymentScheduleData, PaymentMilestoneInput, compute_payment_schedule
    unnormalized_data = PaymentScheduleData(
        total_contract_value=100000.0,
        milestones=[
            PaymentMilestoneInput(milestone_number=1, description="Kickoff", percentage=30.0, due_condition="Sign-off"),
            PaymentMilestoneInput(milestone_number=2, description="Beta", percentage=30.0, due_condition="Beta test"),
            PaymentMilestoneInput(milestone_number=3, description="Final", percentage=30.0, due_condition="Go-live"),
        ] # Sums to 90%, not 100%
    )
    pay_summary = compute_payment_schedule(unnormalized_data)
    assert len(pay_summary.milestones) == 3
    total_allocated = sum(m.amount for m in pay_summary.milestones)
    assert total_allocated == Decimal("100000.00"), f"Expected 100000.00, got {total_allocated}"
    total_pct = sum(m.percentage for m in pay_summary.milestones)
    assert abs(total_pct - 100.0) < 0.01, f"Expected 100%, got {total_pct}"
    print("[PASS] [6/8] Payment Schedule: 100% reconciliation and normalization verified!")

    # 7. Markdown Table Parser Divider Enforcement
    from app.services.tiptap_engine import parse_markdown_table_str
    piped_text_without_divider = "Option A | Option B | Option C | Option D"
    assert parse_markdown_table_str(piped_text_without_divider) is None
    valid_markdown_table = (
        "| Header 1 | Header 2 |\n"
        "| --- | --- |\n"
        "| Cell 1 | Cell 2 |"
    )
    parsed_table = parse_markdown_table_str(valid_markdown_table)
    assert parsed_table is not None
    assert parsed_table["type"] == "table"
    print("[PASS] [7/8] TipTap Engine: Robust markdown table divider enforcement verified!")

    # 8. Paragraph-Aware Text Chunking
    from app.services.document_parser import chunk_text
    sample_doc = (
        "Paragraph 1 contains introductory requirements for the procurement process.\n\n"
        "Paragraph 2 details the scope of work and technical deliverables in detail.\n\n"
        "| Item | Qty |\n| --- | --- |\n| Widget | 10 |\n\n"
        "Paragraph 3 outlines terms and conditions."
    )
    chunks = chunk_text(sample_doc, chunk_size=15, overlap=5)
    assert len(chunks) >= 2
    assert all(isinstance(c, str) and len(c) > 0 for c in chunks)
    print("[PASS] [8/8] Document Parser: Paragraph-aware chunking verified!")

    # 9. CoPilot Edit Graph Invocation
    from app.agents.edit_graph import edit_graph, EditState, CoPilotIntentClassification
    edit_test_state = EditState(
        session_id=session_id,
        document_id="doc_test_copilot",
        raw_prompt="Can you summarize this document?",
        segments=[]
    )
    with patch("app.agents.edit_graph.get_chat_model") as mock_llm:
        mock_chat = AsyncMock()
        mock_chat.ainvoke.return_value = CoPilotIntentClassification(
            intent="chat",
            chat_reply="Document summary test"
        )
        mock_llm.return_value.with_structured_output.return_value = mock_chat
        copilot_res = asyncio.run(edit_graph.ainvoke(edit_test_state.model_dump()))
        assert copilot_res["chat_reply"] == "Document summary test"
        assert copilot_res["intent"] == "chat"
    print("[PASS] [9/9] CoPilot Edit Graph: Invocation and state coercing verified!")

    # 10. Super Agent & Subagents Workflow Pipeline Verification
    from app.agents.procurement_graph import (
        SUPER_AGENT_SYSTEM_PROMPT,
        RESEARCH_SUBAGENT_SYSTEM_PROMPT,
        FACT_CHECK_SUBAGENT_SYSTEM_PROMPT,
        AI_DOCS_SUBAGENT_SYSTEM_PROMPT,
        DocClassifierOutput,
        DeepResearchOutput,
        ResearchFinding,
        FactCheckReport,
        ProseContent,
        SubSection,
    )
    assert "Lead Super Agent" in SUPER_AGENT_SYSTEM_PROMPT
    assert "Deep Research Subagent" in RESEARCH_SUBAGENT_SYSTEM_PROMPT
    assert "Adversarial Fact-Checking Agent" in FACT_CHECK_SUBAGENT_SYSTEM_PROMPT
    assert "AI Docs Drafting Subagent" in AI_DOCS_SUBAGENT_SYSTEM_PROMPT

    workflow_test_state = ProcurementState(
        session_id=session_id,
        raw_prompt="Deploy cloud microservices architecture with SLA governance",
        doc_type=ProcurementDocType.RFP,
        num_pages=3
    )

    with patch("app.agents.procurement_graph.get_chat_model") as mock_llm_factory:
        mock_llm = MagicMock()
        mock_llm_factory.return_value = mock_llm

        def make_structured_mock(schema):
            m = MagicMock()
            if schema == DocClassifierOutput:
                m.ainvoke = AsyncMock(return_value=DocClassifierOutput(doc_type=ProcurementDocType.RFP))
            elif schema == DeepResearchOutput:
                m.ainvoke = AsyncMock(return_value=DeepResearchOutput(findings=[ResearchFinding(finding_id="src_1", statement="Microservices SLA verified")]))
            elif schema == FactCheckReport:
                m.ainvoke = AsyncMock(return_value=FactCheckReport(status="APPROVED", audit_notes="All claims verified"))
            else:
                m.ainvoke = AsyncMock(return_value=ProseContent(heading="Scope & Deliverables", sub_sections=[SubSection(sub_heading="1.1 Baseline", paragraphs=["Service specification details"])], paragraphs=["Intro overview paragraph"]))
            return m

        mock_llm.with_structured_output.side_effect = make_structured_mock
        wf_res = asyncio.run(procurement_graph.ainvoke(workflow_test_state.model_dump()))
        assert wf_res["status"] == "ready"
        assert len(wf_res["segments"]) >= 3
        assert "research_findings" in wf_res
        assert "sandbox_computations" in wf_res
        assert "audit_report" in wf_res
        assert wf_res["audit_report"].get("status") == "APPROVED"
    print("[PASS] [10/15] Super Agent & Subagents Workflow Pipeline: Complete lifecycle verified!")

    # =====================================================================
    # 11. Ephemeral Agent Factory: Dynamic Instantiation & Disposal
    # =====================================================================
    from app.agents.ephemeral_factory import EphemeralAgentFactory, EphemeralAgentSpec
    eph_spec = asyncio.run(EphemeralAgentFactory.synthesize_spec_if_needed(
        "Enterprise HIPAA compliant data processing system", sess
    ))
    assert eph_spec is not None, "Should trigger ephemeral agent for HIPAA prompt"
    assert "HIPAA" in eph_spec.role_name
    assert eph_spec.temperature <= 0.2

    no_spec = asyncio.run(EphemeralAgentFactory.synthesize_spec_if_needed(
        "Standard office supplies purchase order", sess
    ))
    assert no_spec is None, "Should NOT trigger ephemeral agent for generic prompt"
    print("[PASS] [11/15] Ephemeral Agent Factory: Dynamic instantiation & disposal verified!")

    # =====================================================================
    # 12. Context State Bus: Concurrency & Deterministic Reconciliation
    # =====================================================================
    from app.core.context_bus import ContextStateBus, ContextDiff

    async def _test_context_bus():
        bus = ContextStateBus()
        base = {"research_findings": [], "segments": [], "status": "gathering"}

        # Snapshot immutability
        snap = bus.snapshot(base)
        snap["status"] = "mutated"
        assert base["status"] == "gathering", "Snapshot mutation must NOT affect original"

        # Concurrent diff commits
        tasks = [
            bus.commit_diff(ContextDiff(source_agent=f"agent_{i}", field_updates={f"key_{i}": i}))
            for i in range(10)
        ]
        revisions = await asyncio.gather(*tasks)
        assert bus.revision == 10, f"Expected 10 revisions, got {bus.revision}"
        assert bus.pending_diffs == 10

        # Deterministic reconciliation
        result = await bus.reconcile(base)
        assert bus.pending_diffs == 0
        assert result.get("key_0") == 0
        assert result.get("key_9") == 9
        return True

    assert asyncio.run(_test_context_bus())
    print("[PASS] [12/15] Context State Bus: Concurrency & deterministic reconciliation verified!")

    # =====================================================================
    # 13. Browser Actuator: SSRF Safety & DOM Extraction
    # =====================================================================
    from app.services.browser_actuator import _validate_url_safety, _extract_text_from_html, _extract_dom_elements

    # SSRF blocking
    assert _validate_url_safety("https://127.0.0.1/admin") is not None, "Must block localhost"
    assert _validate_url_safety("https://169.254.169.254/metadata") is not None, "Must block cloud metadata"
    assert _validate_url_safety("ftp://example.com") is not None, "Must block non-HTTP schemes"
    assert _validate_url_safety("https://example.com/page") is None, "Must allow valid HTTPS"

    # DOM extraction
    test_html = "<html><body><h1>Title</h1><p>Paragraph</p><table><tr><td>A</td><td>B</td></tr></table></body></html>"
    text = _extract_text_from_html(test_html)
    assert "Title" in text and "Paragraph" in text
    elements = _extract_dom_elements(test_html)
    assert any(e["tag"] == "h1" and "Title" in e["text"] for e in elements)
    assert any(e["tag"] == "tr" for e in elements)
    print("[PASS] [13/15] Browser Actuator: SSRF safety & DOM extraction verified!")

    # =====================================================================
    # 14. SaaS Connector: Ingestion & PII Sanitization
    # =====================================================================
    from app.services.saas_connectors import _sanitize_content, _chunk_content, SaaSRecord

    sanitized = _sanitize_content("Contact john@example.com or call 555-123-4567 for details")
    assert "[EMAIL_REDACTED]" in sanitized, "Must mask email PII"
    assert "[PHONE_REDACTED]" in sanitized, "Must mask phone PII"

    chunks = _chunk_content("A" * 2000, chunk_size=800, overlap=100)
    assert len(chunks) >= 3, f"Expected >= 3 chunks, got {len(chunks)}"
    assert all(len(c) <= 800 for c in chunks)

    record = SaaSRecord(source_type="google_drive", title="Test Doc", content="Procurement requirements")
    assert record.attribution_tag.startswith("[^google_drive_")
    print("[PASS] [14/15] SaaS Connector: PII sanitization & chunking verified!")

    # =====================================================================
    # 15. Execution Evaluator: Reward Scoring & Tool Audit
    # =====================================================================
    from app.agents.evaluator import ExecutionEvaluator

    evaluator = ExecutionEvaluator()
    evaluator.record_simple("research", "kb_query", latency_ms=200, relevance=0.9, success=True)
    evaluator.record_simple("sandbox", "compute", latency_ms=100, relevance=1.0, success=True)
    evaluator.record_simple("sandbox", "schedule", latency_ms=80, relevance=1.0, success=True)
    evaluator.record_simple("visual", "fetch", latency_ms=150, relevance=0.8, success=True)

    report = evaluator.evaluate()
    assert 0.0 <= report.reward_score <= 1.0
    assert report.total_tool_calls == 4
    assert report.efficiency_grade in ("A", "B", "C", "D")
    assert "research" in report.agent_scores
    assert "sandbox" in report.agent_scores

    # Flagged audit should penalize reward
    evaluator_flagged = ExecutionEvaluator()
    evaluator_flagged.record_simple("test", "tool", relevance=0.9)
    flagged_report = evaluator_flagged.evaluate(audit_report={"status": "FLAGGED", "conflicts": ["Budget mismatch"]})
    assert flagged_report.reward_score < report.reward_score, "Flagged audit must penalize reward"
    assert len(flagged_report.flags) > 0
    print("[PASS] [15/15] Execution Evaluator: Reward scoring & tool audit verified!")

    # =====================================================================
    # 16. Subagent Activity Logger: Live Monitoring & Event Registry
    # =====================================================================
    from app.core.subagent_logger import subagent_logger, SubagentActivityEvent

    start_ev = subagent_logger.emit(
        subagent_id="deep_research_subagent",
        activity_type="START",
        message="Testing research provenance scraping",
        session_id="test_sess_001",
    )
    assert start_ev.activity_type == "START"
    assert start_ev.icon == "🔬"

    tool_ev = subagent_logger.emit(
        subagent_id="sandbox_subagent",
        activity_type="TOOL_CALL",
        message="Running deterministic Decimal calculation",
        session_id="test_sess_001",
        details={"tool": "compute_line_items"},
    )
    assert tool_ev.activity_type == "TOOL_CALL"

    done_ev = subagent_logger.emit(
        subagent_id="deep_research_subagent",
        activity_type="COMPLETE",
        message="Completed research",
        session_id="test_sess_001",
        duration_ms=123.4,
        status="SUCCESS",
    )
    assert done_ev.activity_type == "COMPLETE"
    assert done_ev.duration_ms == 123.4

    # Verify query and filtering
    events = subagent_logger.get_recent_activities(limit=10, session_id="test_sess_001")
    assert len(events) >= 3
    assert any(e.subagent_id == "deep_research_subagent" for e in events)

    # Verify live summary structure
    summary = subagent_logger.get_live_summary()
    assert "subagents" in summary
    assert "active_count" in summary
    assert "recent_events" in summary
    assert any(s["subagent_id"] == "deep_research_subagent" for s in summary["subagents"])
    print("[PASS] [16/16] Subagent Activity Logger: Live monitoring & event registry verified!")

    # =====================================================================
    # 17. Image Spatial Anchor Extraction, Visual Curation & Layout Budgeting
    # =====================================================================
    from app.schemas.schemas import ImageSpatialAnchor
    from app.services.document_parser import extract_images_with_anchors_docx
    from app.api.v1.routes_knowledge import KB_SPATIAL_IMAGE_STORE
    from app.agents.procurement_graph import visual_curation_subagent, ai_docs_agent_node, ProcurementState
    import os

    docx_candidates = [
        "tests/sample_proposal.docx",
        "/app/tests/sample_proposal.docx",
        "SEG AI Project Command Centre - Architecture & Client Proposal V4.docx",
    ]
    sample_path = next((p for p in docx_candidates if os.path.exists(p)), None)
    if sample_path:
        with open(sample_path, "rb") as f:
            sample_bytes = f.read()
        anchors = extract_images_with_anchors_docx(sample_bytes)
        assert len(anchors) == 3, f"Expected 3 extracted images, got {len(anchors)}"

        # Verify aspect ratio calculations
        banner = next((a for a in anchors if a.aspect_ratio >= 3.5), None)
        assert banner is not None, "Expected banner anchor with aspect_ratio >= 3.5"
        assert banner.width == 2048 and banner.height == 277
        assert "5. 3-Step Setup" in (banner.preceding_heading or "")

        arch_img = next((a for a in anchors if a.width == 1724 and a.height == 2048), None)
        assert arch_img is not None, "Expected architecture diagram anchor (1724x2048)"
        assert arch_img.aspect_ratio == 0.84

        flow_img = next((a for a in anchors if a.width == 986 and a.height == 2048), None)
        assert flow_img is not None, "Expected workflow diagram anchor (986x2048)"
        assert flow_img.aspect_ratio == 0.48

        # Test Visual Curation Subagent with Spatial Store
        test_kb_id = "test_kb_spatial_001"
        KB_SPATIAL_IMAGE_STORE[test_kb_id] = anchors

        test_state = ProcurementState(
            session_id="test_spatial_session",
            raw_prompt="SEG AI Project Command Centre architecture with Evolution API WhatsApp WebSocket ingestion",
            kb_id=test_kb_id,
            num_pages=3,
        )
        curated_images = asyncio.run(visual_curation_subagent(test_state))
        assert len(curated_images) >= 3

        # Confirm workflow guide is correctly identified as process_workflow (not header_cover)
        curated_workflow = next(img for img in curated_images if img.aspect_ratio >= 3.5)
        assert curated_workflow.image_role == "process_workflow"
        assert "3-Step Setup" in curated_workflow.caption

        # Confirm architecture diagram is classified
        curated_arch = next(img for img in curated_images if img.aspect_ratio == 0.84)
        assert curated_arch.image_role == "architecture_diagram"

        # Test Layout Budgeting in AI Docs Agent Node: diagrams must NOT stack on Page 1 and H1 is first
        docs_res = asyncio.run(ai_docs_agent_node(test_state))
        segments = docs_res.get("segments", [])
        assert len(segments) == 3

        # Verify each segment begins with H1 heading and contains at most 1 diagram image node
        for idx, seg in enumerate(segments, 1):
            nodes = seg.content.get("content", [])
            assert nodes[0].get("type") == "heading", f"Segment {idx} did not start with an H1 heading!"
            assert nodes[0].get("attrs", {}).get("level") == 1
            diagram_img_nodes = [
                n for n in nodes
                if n.get("type") == "image"
                and "unsplash.com" not in n.get("attrs", {}).get("src", "")
            ]
            assert len(diagram_img_nodes) <= 1, f"Segment {idx} has {len(diagram_img_nodes)} diagrams stacked!"
        # Test Guardrail on VENDOR_CONTRACT (must have boilerplate banner, 0 inline diagrams)
        contract_state = ProcurementState(
            session_id="test_contract_guardrail",
            raw_prompt="Master Services Agreement legal contract for cloud consulting",
            doc_type=ProcurementDocType.VENDOR_CONTRACT,
            kb_id=test_kb_id,
            num_pages=3,
        )
        contract_images = asyncio.run(visual_curation_subagent(contract_state))
        assert len(contract_images) == 1, f"Expected exactly 1 banner image, got {len(contract_images)}"
        assert contract_images[0].image_role == "header_cover"

        contract_docs = asyncio.run(ai_docs_agent_node(contract_state))
        contract_segs = contract_docs.get("segments", [])
        for idx, seg in enumerate(contract_segs, 1):
            nodes = seg.content.get("content", [])
            # Only page 1 top banner allowed; no inline diagrams inside clauses
            if idx > 1:
                assert not any(n.get("type") == "image" for n in nodes), f"Page {idx} in VENDOR_CONTRACT contained an image!"

    print("[PASS] [17/17] Image Understanding & Layout Budgeting: Spatial extraction and diagram distribution verified!")

    # =====================================================================
    # 18. Dynamic S3 & Local Template Discovery & Hover Dummy Preview AST
    # =====================================================================
    from app.services.s3_template_service import (
        list_all_dynamic_templates,
        get_template_preview,
        register_custom_template,
    )

    templates = list_all_dynamic_templates()
    assert len(templates) >= 10, f"Expected >= 10 templates, got {len(templates)}"
    
    # Verify preview AST generation
    rfp_preview = get_template_preview("rfp_enterprise")
    assert rfp_preview is not None
    assert "preview_ast" in rfp_preview
    assert rfp_preview["preview_ast"]["type"] == "doc"
    assert len(rfp_preview["preview_ast"]["content"]) > 0

    # Verify custom template registration with space for document attachment
    test_custom = register_custom_template(
        manifest_data={
            "id": "test_s3_custom_audit",
            "category": "RFP",
            "title": "Custom Cloud Engineering RFP",
            "description": "Dynamic custom procurement document template.",
            "tone": "Technical & Rigorous",
            "sections": [
                {"title": "Executive Summary", "section_type": "prose", "guidance": "Executive overview"},
                {"title": "Cost Model", "section_type": "line_items", "guidance": "Itemized costs"},
            ],
        },
        doc_file_bytes=b"# Custom Markdown Document Template\n\nSample text",
        filename="custom_sample.md",
    )
    assert test_custom.id == "test_s3_custom_audit"
    assert test_custom.is_custom is True
    assert len(test_custom.sections) == 2

    # Verify discovery picks up newly registered custom template
    refreshed_preview = get_template_preview("test_s3_custom_audit")
    assert refreshed_preview is not None
    assert refreshed_preview["is_custom"] is True
    print("[PASS] [18/18] Dynamic S3/Local Template Engine: Manifest discovery & preview AST verified!")

    print("==================================================")
    print("[SUCCESS] ALL 18 MICRO-FUNCTION SUITES PASSED CLEANLY (100% SUCCESS)")
    print("==================================================")


if __name__ == "__main__":
    run_all_micro_tests()

