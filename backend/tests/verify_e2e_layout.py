import asyncio
from app.db.clause_store import clause_store
from app.schemas.schemas import ProcurementDocType
from app.services.document_parser import extract_images_with_anchors_docx
from app.api.v1.routes_knowledge import KB_SPATIAL_IMAGE_STORE
from app.agents.procurement_graph import (
    ProcurementState,
    visual_curation_subagent,
    ai_docs_agent_node,
    canvas_checkpoint_agent_node,
)


async def test_full_pipeline():
    with open("/app/tests/sample_proposal.docx", "rb") as f:
        bytes_data = f.read()
    anchors = extract_images_with_anchors_docx(bytes_data)
    test_kb = "kb_e2e_verify"
    KB_SPATIAL_IMAGE_STORE[test_kb] = anchors

    state = ProcurementState(
        session_id="e2e_verify_sess",
        raw_prompt="SEG AI Project Command Centre architecture with Evolution API WhatsApp WebSocket ingestion and private VPS Docker",
        doc_type=ProcurementDocType.RFP,
        kb_id=test_kb,
        num_pages=3,
    )

    # 1. Visual curation
    state.extracted_images = await visual_curation_subagent(state)
    print(f"Curated {len(state.extracted_images)} images:")
    for img in state.extracted_images:
        print(f"  - {img.image_id} | role: {img.image_role} | target: {img.section_target} | ratio: {img.aspect_ratio}")

    # 2. AI docs synthesis
    docs_out = await ai_docs_agent_node(state)
    state.segments = docs_out["segments"]

    # 3. Canvas checkpoint
    ckpt_out = await canvas_checkpoint_agent_node(state)
    state.segments = ckpt_out["segments"]

    print(f"\nDocument generated with {len(state.segments)} segments:")
    for idx, seg in enumerate(state.segments, 1):
        content = seg.content.get("content", [])
        img_nodes = [n for n in content if n.get("type") == "image"]
        print(f'  Page {idx}: "{seg.name}" -> {len(img_nodes)} image(s)')
        for im in img_nodes:
            src_sample = im.get("attrs", {}).get("src", "")[:40]
            alt = im.get("attrs", {}).get("alt", "")
            print(f"      alt: '{alt}', src: {src_sample}...")


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
