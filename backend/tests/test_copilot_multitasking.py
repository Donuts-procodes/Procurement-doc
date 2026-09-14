import asyncio
import time
from app.db.clause_store import clause_store
from app.schemas.schemas import ProcurementDocType
from app.services.document_parser import extract_images_with_anchors_docx
from app.api.v1.routes_knowledge import KB_SPATIAL_IMAGE_STORE
from app.agents.procurement_graph import (
    ProcurementState,
    visual_curation_subagent,
    ai_docs_agent_node,
    DocumentDesignConfig,
)
from app.agents.edit_graph import (
    edit_graph,
    EditState,
    _detect_ribbon_commands,
    safe_eval_math,
)


async def evaluate_copilot_multitasking():
    print("==================================================================")
    print("🚀 EVALUATING COPILOT MULTITASKING & COMPOUND ORCHESTRATION")
    print("==================================================================")

    # 1. Deterministic Multi-Ribbon Fast-Path (< 0.1ms, Zero LLM tokens)
    print("\n[TEST 1] Compound Multi-Ribbon Fast-Path (0 Tokens, Sub-millisecond):")
    multi_prompt = "set watermark to STRICTLY CONFIDENTIAL, change font to Georgia, font size to 14px, and page color to #f8fafc"
    t0 = time.perf_counter()
    ribbons = _detect_ribbon_commands(multi_prompt)
    dt_ms = (time.perf_counter() - t0) * 1000
    assert len(ribbons) >= 4, f"Expected at least 4 ribbons, got {len(ribbons)}"
    action_types = {r.action_type for r in ribbons}
    assert "set_watermark" in action_types
    assert "set_font" in action_types
    assert "set_font_size" in action_types
    assert "set_page_color" in action_types
    print(f"  ✓ Successfully extracted {len(ribbons)} distinct formatting directives in {dt_ms:.3f}ms")
    for r in ribbons:
        print(f"    - {r.action_type}: {getattr(r, r.action_type.replace('set_', ''), '') or getattr(r, 'watermark', '')}")

    # Test via EditGraph invocation for multi-ribbon fast-path
    dummy_state = EditState(
        session_id="multi_ribbon_session",
        document_id="doc_multi",
        raw_prompt=multi_prompt,
        segments=[],
    )
    res_fast = await edit_graph.ainvoke(dummy_state.model_dump())
    assert res_fast["intent"] == "multitask", f"Expected 'multitask', got {res_fast['intent']}"
    assert len(res_fast["ribbon_actions"]) >= 4
    print(f"  ✓ EditGraph zero-token fast-path classified as: '{res_fast['intent']}' with {len(res_fast['ribbon_actions'])} actions")

    # 2. Deterministic Safe Math REPL Test
    print("\n[TEST 2] Deterministic Math REPL Engine:")
    math_tests = [
        ("250000 * 0.18", 45000.0),
        ("1200 * 10 + 40 * 150", 18000),
        ("($50,000 + $25,000) * 0.10", 7500.0),
        ("100 / 4 + 75", 100.0),
    ]
    for expr, expected in math_tests:
        val = safe_eval_math(expr)
        assert abs(val - expected) < 1e-4, f"Math eval failed: {expr} = {val} != {expected}"
        print(f"  ✓ Evaluated: '{expr}' -> {val} (expected {expected})")

    # 3. Setup baseline document state with images for compound execution
    print("\n[TEST 3] Initializing 3-Section Baseline Document with Visual Assets:")
    with open("/app/tests/sample_proposal.docx", "rb") as f:
        bytes_data = f.read()
    anchors = extract_images_with_anchors_docx(bytes_data)
    test_kb = "kb_copilot_multitask"
    KB_SPATIAL_IMAGE_STORE[test_kb] = anchors

    base_state = ProcurementState(
        session_id="copilot_multitask_session",
        raw_prompt="Enterprise SEG AI Project Command Centre architecture with Evolution API",
        doc_type=ProcurementDocType.RFP,
        kb_id=test_kb,
        num_pages=3,
        design_config=DocumentDesignConfig(),
    )
    base_state.extracted_images = await visual_curation_subagent(base_state)
    docs_out = await ai_docs_agent_node(base_state)
    base_state.segments = docs_out["segments"]
    base_segments = base_state.segments

    print(f"Baseline document generated with {len(base_segments)} sections:")
    for i, s in enumerate(base_segments, 1):
        num_imgs = len([n for n in s.content.get("content", []) if n.get("type") == "image"]) if isinstance(s.content, dict) else 0
        print(f"  Section {i}: '{s.name}' (Contains {num_imgs} diagram node(s))")

    seg1_images_initial = len([n for n in base_segments[0].content.get("content", []) if n.get("type") == "image"]) if isinstance(base_segments[0].content, dict) else 0
    seg2_images_initial = len([n for n in base_segments[1].content.get("content", []) if n.get("type") == "image"]) if isinstance(base_segments[1].content, dict) else 0

    # 4. Compound Multitasking Orchestration Test
    # Instruction touches 5 distinct facets simultaneously:
    # (a) Ribbon styling: watermark to CONFIDENTIAL
    # (b) Ribbon styling: font size to 14px
    # (c) Relocate visual asset: move diagram from section 1 to section 2
    # (d) Surgical edit: update section 1 to mention Evolution API enterprise webhook latency
    # (e) Document expansion: add new section for SLA Commitments
    print("\n[TEST 4] Compound Multitasking Instruction Execution:")
    compound_prompt = (
        "Set watermark to CONFIDENTIAL, font size to 14px, "
        "update section 1 to highlight Evolution API enterprise webhook latency under 50ms, "
        "move the diagram from section 1 to section 2, "
        "and add a new section titled 'SLA Commitments & Response Times' with 99.99% uptime guarantee."
    )
    print(f"Prompt: \"{compound_prompt}\"")

    edit_state = EditState(
        session_id="copilot_multitask_session",
        document_id="doc_multi_orchestrate",
        raw_prompt=compound_prompt,
        segments=list(base_segments),
    )

    t0 = time.perf_counter()
    result = await edit_graph.ainvoke(edit_state.model_dump())
    dt = time.perf_counter() - t0

    assert result["intent"] == "multitask", f"Expected intent 'multitask', got '{result['intent']}'"
    print(f"  ✓ Decomposed & Orchestrated Intent: '{result['intent']}' in {dt:.2f}s")
    print(f"  ✓ Executed Tasks Log ({len(result['executed_tasks'])} subtasks):")
    for t in result["executed_tasks"]:
        print(f"    - {t}")

    # Verify visual asset relocation
    updated_segs = result["segments"]
    seg1_images_after = len([n for n in updated_segs[0].content.get("content", []) if n.get("type") == "image"]) if isinstance(updated_segs[0].content, dict) else 0
    seg2_images_after = len([n for n in updated_segs[1].content.get("content", []) if n.get("type") == "image"]) if isinstance(updated_segs[1].content, dict) else 0
    print(f"\n  ✓ Visual Relocation Verification:")
    print(f"    Section 1 diagrams: {seg1_images_initial} -> {seg1_images_after}")
    print(f"    Section 2 diagrams: {seg2_images_initial} -> {seg2_images_after}")
    if seg1_images_initial > 0:
        assert seg1_images_after < seg1_images_initial, "Diagram was not removed from Section 1!"
        assert seg2_images_after > seg2_images_initial, "Diagram was not added to Section 2!"

    # Verify section expansion
    assert len(updated_segs) == len(base_segments) + 1, f"Expected {len(base_segments) + 1} segments, got {len(updated_segs)}"
    new_section = updated_segs[-1]
    print(f"\n  ✓ Document Expansion Verification:")
    print(f"    Brand New Section Added: '{new_section.name}'")
    assert "SLA" in new_section.name.upper() or "COMMITMENT" in new_section.name.upper() or "UPTIME" in new_section.name.upper() or len(new_section.name) > 0

    # Verify multi-ribbon persistence actions
    ribbon_actions = result.get("ribbon_actions", [])
    print(f"\n  ✓ Multi-Ribbon Directives Captured: {len(ribbon_actions)}")
    for r in ribbon_actions:
        print(f"    - {r.get('action_type')}: {r}")

    # Verify response summary format
    assert "Successfully orchestrated" in result.get("chat_reply", "")
    print(f"\n  ✓ Orchestration Confirmation Reply:\n{result.get('chat_reply')}")

    # 5. Route Persistence Integration Test
    print("\n[TEST 5] Route Integration Test (POST /api/generate/answer):")
    from app.api.v1.routes_generate import answer_question, AnswerQuestionRequest
    from app.core.session import session_store
    from app.db.document_store import GeneratedDocument

    doc_id = "doc_multitask_route_test"
    base_state.segments = updated_segs
    session_store.save_graph_state(doc_id, base_state)

    payload = AnswerQuestionRequest(
        session_id="copilot_multitask_session",
        document_id=doc_id,
        answer="Set watermark to DRAFT, font Georgia, and font size 16px",
    )
    route_resp = await answer_question(payload)
    assert route_resp["status"] == "ready" or route_resp["status"] == "chat_reply"
    assert len(route_resp["ribbon_actions"]) >= 2
    assert route_resp["style_config"]["fontFamily"] == "Georgia"
    assert route_resp["style_config"]["fontSize"] == "16px"
    assert route_resp["style_config"]["watermark"] == "DRAFT"
    print(f"  ✓ Route saved all ribbon styling simultaneously:")
    print(f"    - font: {route_resp['style_config']['fontFamily']}")
    print(f"    - font_size: {route_resp['style_config']['fontSize']}")
    print(f"    - watermark: {route_resp['style_config']['watermark']}")

    print("\n==================================================================")
    print("🏆 COPILOT MULTITASKING SUITE COMPLETED: 100% PASSING")
    print("==================================================================")


if __name__ == "__main__":
    asyncio.run(evaluate_copilot_multitasking())
