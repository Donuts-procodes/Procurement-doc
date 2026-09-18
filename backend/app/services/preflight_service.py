from __future__ import annotations

import logging
import re
from typing import Any

from app.api.v1.routes_knowledge import KB_RAW_TEXT_STORE
from app.schemas.preflight_schemas import (
    PreflightBlueprintRequest,
    PreflightBlueprintResponse,
    PreflightGuidedParams,
    PreflightSectionOutline,
)
from app.schemas.schemas import ProcurementDocType
from app.services.procurement_templates import PREBUILT_TEMPLATES, get_template_by_id

logger = logging.getLogger("gdocs.preflight_service")

# Semantic scoring keyword weights for prebuilt templates
TEMPLATE_SIGNATURES: dict[str, dict[str, Any]] = {
    "rfp_tech": {
        "doc_type": ProcurementDocType.RFP,
        "title": "IT & SaaS Systems RFP",
        "icon": "💻",
        "keywords": [
            "cloud", "saas", "software", "api", "ai", "architecture", "microservices",
            "backend", "frontend", "database", "kubernetes", "docker", "fastapi", "react",
            "command centre", "portal", "system", "platform", "app", "mobile", "tech",
            "whatsapp", "integration", "uptime", "latency", "vector", "rag", "server"
        ],
        "default_pages": 5,
    },
    "rfp_gov": {
        "doc_type": ProcurementDocType.RFP,
        "title": "Government & Public Compliance RFP",
        "icon": "🏛️",
        "keywords": [
            "government", "public sector", "municipal", "statutory", "regulatory",
            "tender", "foia", "non-collusion", "audit", "compliance", "federal", "state",
            "public procurement", "ministry", "agency", "citizen", "statute"
        ],
        "default_pages": 6,
    },
    "rfp_enterprise": {
        "doc_type": ProcurementDocType.RFP,
        "title": "Standard Enterprise RFP",
        "icon": "🏢",
        "keywords": [
            "enterprise", "corporate", "vendor selection", "rfp", "procurement",
            "commercial", "bidding", "proposal", "qualifications", "scoring matrix",
            "evaluation criteria", "eligibility"
        ],
        "default_pages": 5,
    },
    "rfq_goods": {
        "doc_type": ProcurementDocType.RFQ,
        "title": "Commercial Goods & Hardware RFQ",
        "icon": "📦",
        "keywords": [
            "hardware", "goods", "materials", "physical", "equipment", "units",
            "sku", "quantity", "unit price", "shipping", "freight", "incoterms",
            "delivery lead time", "warehouse", "manufacturing"
        ],
        "default_pages": 4,
    },
    "rfq_services": {
        "doc_type": ProcurementDocType.RFQ,
        "title": "Professional Services Rate Card RFQ",
        "icon": "📊",
        "keywords": [
            "rate card", "hourly rate", "consulting", "staff augmentation", "billable",
            "labor", "engineering hours", "daily rate", "professional services", "time and materials"
        ],
        "default_pages": 4,
    },
    "rfi_market": {
        "doc_type": ProcurementDocType.RFI,
        "title": "Market Capabilities RFI",
        "icon": "🔍",
        "keywords": [
            "rfi", "market research", "exploratory", "industry inquiry", "capabilities",
            "product roadmap", "landscape", "vendor discovery", "non-binding"
        ],
        "default_pages": 4,
    },
    "rfi_security": {
        "doc_type": ProcurementDocType.RFI,
        "title": "Cybersecurity Risk RFI",
        "icon": "🛡️",
        "keywords": [
            "security questionnaire", "cybersecurity", "infosec", "penetration testing",
            "vulnerability", "breach", "soc2", "iso 27001", "data protection",
            "encryption", "threat", "incident response"
        ],
        "default_pages": 4,
    },
    "sow_agile": {
        "doc_type": ProcurementDocType.SOW,
        "title": "Agile Software Development SOW",
        "icon": "🚀",
        "keywords": [
            "sow", "statement of work", "agile", "sprint", "scrum", "user stories",
            "backlog", "milestone deliverable", "definition of done", "acceptance criteria",
            "sprint cadence", "epics", "velocity"
        ],
        "default_pages": 5,
    },
    "sow_managed": {
        "doc_type": ProcurementDocType.SOW,
        "title": "Managed Infrastructure Services SOW",
        "icon": "⚙️",
        "keywords": [
            "managed services", "infrastructure support", "patching", "backups",
            "ticket resolution", "maintenance", "disaster recovery", "monthly retainer"
        ],
        "default_pages": 4,
    },
    "contract_msa": {
        "doc_type": ProcurementDocType.VENDOR_CONTRACT,
        "title": "Master Services Agreement (MSA)",
        "icon": "📜",
        "keywords": [
            "msa", "master services agreement", "contract", "indemnification",
            "intellectual property", "liability", "governing law", "termination",
            "confidentiality", "legal terms", "breach"
        ],
        "default_pages": 5,
    },
    "contract_nda": {
        "doc_type": ProcurementDocType.VENDOR_CONTRACT,
        "title": "Mutual Non-Disclosure Agreement",
        "icon": "🔒",
        "keywords": [
            "nda", "non-disclosure", "confidentiality agreement", "trade secret",
            "bilateral", "proprietary information"
        ],
        "default_pages": 3,
    },
    "scorecard_kpi": {
        "doc_type": ProcurementDocType.VENDOR_SCORECARD,
        "title": "Quarterly Vendor KPI Scorecard",
        "icon": "📈",
        "keywords": [
            "scorecard", "kpi", "vendor evaluation", "quarterly review",
            "performance rating", "tier rating", "metrics breakdown"
        ],
        "default_pages": 4,
    },
    "po_standard": {
        "doc_type": ProcurementDocType.PURCHASE_ORDER,
        "title": "Standard Authorized Purchase Order",
        "icon": "🧾",
        "keywords": [
            "purchase order", "po", "authorized line items", "billing address",
            "shipping address", "order authorization", "payment terms net 30"
        ],
        "default_pages": 3,
    },
}

TECH_KEYWORDS_MAP = {
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "kubernetes": "Kubernetes",
    "docker": "Docker",
    "fastapi": "Python FastAPI",
    "python": "Python",
    "react": "React",
    "next.js": "Next.js",
    "typescript": "TypeScript",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "chromadb": "ChromaDB",
    "graphql": "GraphQL",
    "kafka": "Apache Kafka",
    "openai": "OpenAI LLM",
    "whatsapp": "WhatsApp Cloud API",
    "microservices": "Microservices",
    "rest api": "RESTful APIs",
    "flutter": "Flutter",
    "node": "Node.js",
}

COMPLIANCE_KEYWORD_MAP = {
    "soc 2": "SOC 2",
    "soc2": "SOC 2",
    "iso 27001": "ISO 27001",
    "iso27001": "ISO 27001",
    "gdpr": "GDPR",
    "hipaa": "HIPAA",
    "pci": "PCI-DSS",
    "pci-dss": "PCI-DSS",
    "fedramp": "FedRAMP",
}


def compute_preflight_blueprint(req: PreflightBlueprintRequest) -> PreflightBlueprintResponse:
    """GenSpark-style preflight intake:
    Evaluates user prompt + ingested KB text to automatically choose the template,
    extract all 7 guided parameters, determine page count, and format outline beforehand."""
    prompt = req.prompt.strip()
    kb_text = ""
    if req.kb_id and req.kb_id in KB_RAW_TEXT_STORE:
        kb_text = KB_RAW_TEXT_STORE[req.kb_id][:8000]

    combined_corpus = f"{prompt}\n\n{kb_text}".strip()
    corpus_lower = combined_corpus.lower()

    # 1. Multi-Dimensional Template Scoring
    scores: dict[str, float] = {}
    matched_keywords_per_tmpl: dict[str, list[str]] = {}

    for tmpl_id, tmpl_meta in TEMPLATE_SIGNATURES.items():
        base_score = 1.0
        matched = []
        for kw in tmpl_meta["keywords"]:
            if kw in corpus_lower:
                # Count frequency capped at 3
                cnt = min(3, corpus_lower.count(kw))
                base_score += 1.5 * cnt
                matched.append(kw)

        # Bonus if current_doc_type matches
        if req.current_doc_type and req.current_doc_type.upper() == tmpl_meta["doc_type"].value:
            base_score += 3.0

        # High-priority exact intent hints
        if "sow" in corpus_lower and tmpl_meta["doc_type"] == ProcurementDocType.SOW:
            base_score += 8.0
        if "rfq" in corpus_lower and tmpl_meta["doc_type"] == ProcurementDocType.RFQ:
            base_score += 8.0
        if "rfi" in corpus_lower and tmpl_meta["doc_type"] == ProcurementDocType.RFI:
            base_score += 8.0
        if "contract" in corpus_lower and tmpl_meta["doc_type"] == ProcurementDocType.VENDOR_CONTRACT:
            base_score += 8.0
        if "scorecard" in corpus_lower and tmpl_meta["doc_type"] == ProcurementDocType.VENDOR_SCORECARD:
            base_score += 8.0
        if "purchase order" in corpus_lower and tmpl_meta["doc_type"] == ProcurementDocType.PURCHASE_ORDER:
            base_score += 8.0

        scores[tmpl_id] = base_score
        matched_keywords_per_tmpl[tmpl_id] = matched

    # Find highest scoring template
    best_tmpl_id = max(scores, key=scores.get)
    best_meta = TEMPLATE_SIGNATURES[best_tmpl_id]
    best_matched_kws = matched_keywords_per_tmpl[best_tmpl_id]

    # Calculate normalized confidence score (0.80 to 0.98)
    raw_top_score = scores[best_tmpl_id]
    confidence_score = min(0.98, max(0.82, 0.75 + (raw_top_score / 40.0)))

    # 2. Extract Guided Parameters (Pre-Flight Ground Truth)
    # Buyer extraction: Priority 1 - Prominent Title Entity (e.g. 'SEG AI Project Command Centre' -> 'SEG AI')
    buyer_name = None
    leading_entity = re.search(
        r"^([A-Z0-9]{2,}(?:\s+[A-Z0-9]{2,}){0,2})\s+(?:Project|Command|Architecture|Proposal|RFP|Tender|Initiative|System|Platform|Portal)",
        prompt,
    )
    if leading_entity:
        cand = leading_entity.group(1).strip()
        if cand.lower() not in ["generate", "draft", "create", "procurement", "the", "an", "new"]:
            buyer_name = cand

    if not buyer_name:
        buyer_match = re.search(
            r"(?:buyer|client|organization|issued by)\s*[:\-]?\s*([A-Z][A-Za-z0-9\s&]{2,35}?)(?:'s|\s+project|\s+command|\s+portal|\s+system|\s+initiative|\s+rfp|\s+tender|\.|\,|$)",
            combined_corpus,
            re.IGNORECASE,
        )
        if buyer_match:
            cand = buyer_match.group(1).strip()
            if len(cand) >= 3 and cand.lower() not in ["a", "an", "the", "generate", "procurement", "enterprise", "proposal", "aws", "azure", "gcp"]:
                buyer_name = cand

    # Vendor extraction
    vendor_name = None
    vendor_match = re.search(
        r"(?:vendor|supplier|contractor|bidder|provider)\s*[:\-]?\s*([A-Z][A-Za-z0-9\s&]{2,35}?)(?:\.|\,|$|\n)",
        combined_corpus,
        re.IGNORECASE,
    )
    if vendor_match:
        cand = vendor_match.group(1).strip()
        if len(cand) >= 3 and cand.lower() not in ["selection", "evaluation", "scorecard", "known"]:
            vendor_name = cand

    # Budget extraction
    budget_estimate = None
    budget_match = re.search(
        r"(?:(?:USD|EUR|GBP|INR|\$)\s*[\d,]+(?:\.\d+)?(?:\s*(?:k|m|million|thousand))?|[\d,]+(?:\.\d+)?\s*(?:USD|EUR|GBP|INR|dollars?|k|m|million|thousand))",
        combined_corpus,
        re.IGNORECASE,
    )
    if budget_match:
        budget_estimate = budget_match.group(0).strip()
        if not (budget_estimate.startswith("$") or any(cur in budget_estimate.upper() for cur in ["USD", "EUR", "GBP", "INR"])) and any(c.isdigit() for c in budget_estimate):
            budget_estimate = f"${budget_estimate}"

    # Timeline extraction
    delivery_timeline = None
    timeline_match = re.search(
        r"(\b\d+[\s-]*(?:months?|weeks?|days?|sprints?)\b|\bQ[1-4]\s*20\d\d\b|\b(?:october|november|december|january|february|march|april|may|june|july|august|september)\s*20\d\d\b)",
        combined_corpus,
        re.IGNORECASE,
    )
    if timeline_match:
        delivery_timeline = timeline_match.group(1).strip()

    # Primary Tech Stack (deduplicating substrings like Python when Python FastAPI is present)
    detected_tech_raw = []
    for kw, label in TECH_KEYWORDS_MAP.items():
        if kw in corpus_lower and label not in detected_tech_raw:
            detected_tech_raw.append(label)

    detected_tech = []
    for t in detected_tech_raw:
        # Don't add 'Python' if 'Python FastAPI' is already present
        if t == "Python" and "Python FastAPI" in detected_tech_raw:
            continue
        if t == "PostgreSQL" and "Postgres" in detected_tech:
            continue
        detected_tech.append(t)

    primary_tech = ", ".join(detected_tech[:6]) if detected_tech else None

    # Compliance Frameworks
    detected_compliance = []
    for kw, label in COMPLIANCE_KEYWORD_MAP.items():
        if kw in corpus_lower and label not in detected_compliance:
            detected_compliance.append(label)
    if not detected_compliance and best_tmpl_id in ["rfp_tech", "rfi_security"]:
        detected_compliance = ["SOC 2", "GDPR"]

    # SLA Target
    sla_target = "99.9% (Standard)"
    if "99.99" in corpus_lower or "mission critical" in corpus_lower or "24/7" in corpus_lower:
        sla_target = "99.99% (Mission Critical)"
    elif "99.95" in corpus_lower or "high availability" in corpus_lower:
        sla_target = "99.95% (High)"

    # Dates & Room / Facility extraction (Simplified intake - manual staff verification)
    dates_match = re.search(
        r"(?:(?:from|between|dates?|check-in|arrival|during)\s*[:\-]?\s*(\w+\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*-\s*\w+\s+\d{1,2}(?:st|nd|rd|th)?)?(?:,?\s*\d{4})?|\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b))",
        combined_corpus,
        re.IGNORECASE,
    )
    target_dates = dates_match.group(1).strip() if dates_match else delivery_timeline

    room_match = re.search(
        r"(?:room|hall|suite|auditorium|conference room|venue|facility|space)\s*[:\-]?\s*([A-Za-z0-9\s\-]{2,30}?)(?:\.|\,|$|\n)",
        combined_corpus,
        re.IGNORECASE,
    )
    room_or_facility = room_match.group(1).strip() if room_match else None

    # Guided parameters DTO with Manual Staff Verification
    guided_params = PreflightGuidedParams(
        buyer_name=buyer_name,
        vendor_name=vendor_name,
        budget_estimate=budget_estimate,
        delivery_timeline=delivery_timeline,
        target_dates=target_dates,
        room_or_facility=room_or_facility,
        availability_verification="Manual Staff Verification",
        primary_tech=primary_tech,
        compliance_frameworks=detected_compliance,
        sla_target=sla_target,
    )

    # 3. Outline sections from chosen template
    tmpl_obj = get_template_by_id(best_tmpl_id)
    outline_sections: list[PreflightSectionOutline] = []
    for idx, sec in enumerate(tmpl_obj.sections):
        outline_sections.append(
            PreflightSectionOutline(
                index=idx + 1,
                title=sec.title,
                section_type=sec.section_type,
                guidance=sec.guidance,
            )
        )

    # 4. Formulate GenSpark Rationale
    tech_summary = primary_tech or "enterprise specifications"
    comp_summary = ", ".join(detected_compliance) if detected_compliance else "industry standards"
    match_reason = (
        f"Auto-selected '{best_meta['title']}' based on detection of {tech_summary}, "
        f"{comp_summary} compliance mandates, and structured {best_meta['doc_type'].value} procurement requirements."
    )

    return PreflightBlueprintResponse(
        recommended_template_id=best_tmpl_id,
        recommended_doc_type=best_meta["doc_type"],
        template_title=best_meta["title"],
        template_icon=best_meta["icon"],
        confidence_score=round(confidence_score, 2),
        match_reason=match_reason,
        recommended_num_pages=best_meta["default_pages"],
        guided_params=guided_params,
        outline_sections=outline_sections,
        detected_keywords=best_matched_kws[:8],
    )
