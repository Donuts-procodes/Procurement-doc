from __future__ import annotations

from typing import Literal
from pydantic import BaseModel
from app.schemas.schemas import ProcurementDocType


class SectionSchema(BaseModel):
    title: str
    section_type: Literal["prose", "line_items", "payment_schedule", "clause"] = "prose"
    guidance: str


class TemplateMetaData(BaseModel):
    id: str
    category: ProcurementDocType
    title: str
    description: str
    tone: str
    tone_description: str
    icon: str
    sections: list[SectionSchema]


PREBUILT_TEMPLATES: dict[str, TemplateMetaData] = {
    # RFP Templates
    "rfp_enterprise": TemplateMetaData(
        id="rfp_enterprise",
        category=ProcurementDocType.RFP,
        title="Standard Enterprise RFP",
        description="Comprehensive evaluation format for corporate software, services, and vendor selection.",
        tone="Formal & Evaluative",
        tone_description="Professional, analytical, clear criteria with structured submission guidelines.",
        icon="🏢",
        sections=[
            SectionSchema(title="Scope of Work", section_type="prose", guidance="Detailed technical and operational requirements, project context, and core objectives."),
            SectionSchema(title="Eligibility Criteria", section_type="prose", guidance="Vendor qualifications, certifications, minimum years in business, and financial stability."),
            SectionSchema(title="Submission Instructions", section_type="prose", guidance="Format requirements, submission deadline, contact point, and required proposal sections."),
            SectionSchema(title="Evaluation Criteria", section_type="prose", guidance="Scoring breakdown (e.g. Technical 40%, Cost 40%, Experience 20%) and decision process."),
            SectionSchema(title="Project Timeline", section_type="prose", guidance="Key procurement milestones: RFP issue date, Q&A window, proposal deadline, award date."),
            SectionSchema(title="Terms & Conditions", section_type="clause", guidance="Standard procurement terms, confidentiality, proposal validity period, and governing law."),
        ],
    ),
    "rfp_gov": TemplateMetaData(
        id="rfp_gov",
        category=ProcurementDocType.RFP,
        title="Government & Public Compliance RFP",
        description="Strict audit-compliant structure for public sector, municipal, or regulated tenders.",
        tone="Strict & Regulatory",
        tone_description="Formal, precise legalistic phrasing adhering to statutory procurement mandates.",
        icon="🏛️",
        sections=[
            SectionSchema(title="Executive Summary & Purpose", section_type="prose", guidance="Public interest scope, statutory background, and high-level mandate."),
            SectionSchema(title="Mandatory Compliance & Certifications", section_type="clause", guidance="Regulatory compliance, non-collusion affidavits, security clearances, and ISO certifications."),
            SectionSchema(title="Technical Specifications & Deliverables", section_type="prose", guidance="Rigid technical baseline, functional capabilities, and mandatory standards."),
            SectionSchema(title="Proposal Costing Structure", section_type="line_items", guidance="Itemized transparent cost breakdown for audit review."),
            SectionSchema(title="Weighted Scoring Matrix", section_type="prose", guidance="Publicly disclosed scoring formula and evaluation panel process."),
            SectionSchema(title="Statutory Terms & Conditions", section_type="clause", guidance="Public procurement general provisions, FOIA clauses, and dispute resolution."),
        ],
    ),
    "rfp_tech": TemplateMetaData(
        id="rfp_tech",
        category=ProcurementDocType.RFP,
        title="IT & SaaS Systems RFP",
        description="Focused on cloud architecture, API integrations, SLA guarantees, and data security.",
        tone="Technical & Rigorous",
        tone_description="In-depth, engineering-focused tone querying system specs and security controls.",
        icon="💻",
        sections=[
            SectionSchema(title="System Architecture & Scope", section_type="prose", guidance="Target system architecture, cloud deployment, and integration specs."),
            SectionSchema(title="Data Security & Privacy Requirements", section_type="clause", guidance="SOC2 Type II, GDPR/CCPA, encryption standards, and vulnerability management."),
            SectionSchema(title="SLA & Support Framework", section_type="prose", guidance="Uptime targets (99.9%), incident response tiers, and escalation paths."),
            SectionSchema(title="Vendor Technical Qualifications", section_type="prose", guidance="Engineering team pedigree, past implementations, and customer references."),
            SectionSchema(title="Licensing & Commercial Model", section_type="line_items", guidance="Subscription tiers, user seats, API calls, and implementation fees."),
        ],
    ),

    # RFQ Templates
    "rfq_goods": TemplateMetaData(
        id="rfq_goods",
        category=ProcurementDocType.RFQ,
        title="Commercial Goods & Hardware RFQ",
        description="Itemized quotation format for physical goods, hardware, and raw materials.",
        tone="Transactional & Precise",
        tone_description="Direct, concise, focused on exact item numbers, lead times, and unit costs.",
        icon="📦",
        sections=[
            SectionSchema(title="Vendor & Requisition Info", section_type="prose", guidance="RFQ reference, buyer details, vendor contact info, and response date."),
            SectionSchema(title="Itemized Quotation Table", section_type="line_items", guidance="SKU codes, descriptions, quantities, unit prices, tax, and freight costs."),
            SectionSchema(title="Delivery & Fulfillment Terms", section_type="prose", guidance="Incoterms (FOB/DDP), shipping destination, lead times, and packaging rules."),
            SectionSchema(title="Commercial Payment Terms", section_type="clause", guidance="Standard payment terms (Net 30/60), early payment discounts, and currency."),
        ],
    ),
    "rfq_services": TemplateMetaData(
        id="rfq_services",
        category=ProcurementDocType.RFQ,
        title="Professional Services Rate Card RFQ",
        description="Pricing solicitation for consulting, engineering hours, or staff augmentation.",
        tone="Commercial & Structured",
        tone_description="Professional rate-card orientation for comparing labor categories.",
        icon="📊",
        sections=[
            SectionSchema(title="Service Scope Overview", section_type="prose", guidance="Summary of requested professional labor categories and estimated effort."),
            SectionSchema(title="Hourly Rate Card Breakdown", section_type="line_items", guidance="Labor roles (Junior/Senior/Architect), hourly billing rates, and cap limits."),
            SectionSchema(title="Travel & Expense Policy", section_type="clause", guidance="Reimbursement bounds, pre-approval rules, and capped per diem rates."),
            SectionSchema(title="Validity & Payment Terms", section_type="clause", guidance="Rate lock duration, invoicing cadence, and payment terms."),
        ],
    ),

    # RFI Templates
    "rfi_market": TemplateMetaData(
        id="rfi_market",
        category=ProcurementDocType.RFI,
        title="Market Capabilities RFI",
        description="Exploratory inquiry to research industry solutions and vendor product roadmaps.",
        tone="Exploratory & Open",
        tone_description="Inquisitive, non-binding tone encouraging vendors to showcase innovations.",
        icon="🔍",
        sections=[
            SectionSchema(title="Problem Statement & Background", section_type="prose", guidance="Business challenge driving the market inquiry and vision."),
            SectionSchema(title="Vendor Organization & Overview", section_type="prose", guidance="Company background, footprint, ownership, and core offerings."),
            SectionSchema(title="Solution Capabilities & Features", section_type="prose", guidance="Open-ended questions on key features, differentiators, and roadmap."),
            SectionSchema(title="Indicative Pricing Models", section_type="prose", guidance="High-level commercial models without requiring binding quotes."),
        ],
    ),
    "rfi_security": TemplateMetaData(
        id="rfi_security",
        category=ProcurementDocType.RFI,
        title="Cybersecurity Risk RFI",
        description="Targeted risk assessment questionnaire for third-party software vendors.",
        tone="Analytical & Risk-Conscious",
        tone_description="Probing, security-focused queries examining data protection and resilience.",
        icon="🛡️",
        sections=[
            SectionSchema(title="Security Governance & Compliance", section_type="prose", guidance="Certifications (ISO 27001, SOC 2), compliance framework, and audit frequency."),
            SectionSchema(title="Data Protection & Encryption", section_type="prose", guidance="Data at rest/in transit encryption standards, key management, and tenant isolation."),
            SectionSchema(title="Business Continuity & Incident Response", section_type="prose", guidance="RTO/RPO metrics, disaster recovery plans, and breach notification SLAs."),
        ],
    ),

    # SOW Templates
    "sow_agile": TemplateMetaData(
        id="sow_agile",
        category=ProcurementDocType.SOW,
        title="Agile Software Development SOW",
        description="Iterative project contract with sprint goals, team rosters, and milestone deliverables.",
        tone="Operational & Collaborative",
        tone_description="Clear, milestone-driven, defining team cadence and sprint acceptance criteria.",
        icon="🚀",
        sections=[
            SectionSchema(title="Project Vision & Objectives", section_type="prose", guidance="Target product features, user outcomes, and business goals."),
            SectionSchema(title="Sprint Cadence & Scope", section_type="prose", guidance="Sprint length (2 weeks), sprint ceremonies, and backlog management."),
            SectionSchema(title="Team Roster & Roles", section_type="prose", guidance="Client vs Vendor staff allocation (PM, Tech Lead, Developers, QA)."),
            SectionSchema(title="Milestone Payment Schedule", section_type="payment_schedule", guidance="Sprint milestone release payments linked to user story sign-offs."),
            SectionSchema(title="Acceptance Criteria & Change Control", section_type="clause", guidance="Definition of Done, testing protocols, and scope change process."),
        ],
    ),
    "sow_managed": TemplateMetaData(
        id="sow_managed",
        category=ProcurementDocType.SOW,
        title="Managed Infrastructure Services SOW",
        description="Long-term IT maintenance, cloud infrastructure management, and technical support SOW.",
        tone="Formal & SLA-Oriented",
        tone_description="Definitive, operational tone centered around uptime guarantees and support response.",
        icon="⚙️",
        sections=[
            SectionSchema(title="Managed Environment Scope", section_type="prose", guidance="Inventory of servers, cloud accounts, networks, and databases managed."),
            SectionSchema(title="SLA Performance & Ticket Resolution", section_type="prose", guidance="P1/P2/P3 incident response times, resolution targets, and uptime guarantees."),
            SectionSchema(title="Routine Maintenance & Backups", section_type="prose", guidance="Patching windows, backup schedules, DR testing, and monitoring."),
            SectionSchema(title="Monthly Recurring Service Fees", section_type="payment_schedule", guidance="Fixed monthly retainer fees, out-of-scope hourly rates, and billing."),
        ],
    ),

    # Contract Templates
    "contract_msa": TemplateMetaData(
        id="contract_msa",
        category=ProcurementDocType.VENDOR_CONTRACT,
        title="Master Services Agreement (MSA)",
        description="Comprehensive legal framework contract governing overall vendor engagement.",
        tone="Legalistic & Binding",
        tone_description="Formal legal prose with robust risk allocation, indemnity, and IP rights.",
        icon="📜",
        sections=[
            SectionSchema(title="Preamble & Purpose", section_type="prose", guidance="Effective date, legal entities, background context, and order of precedence."),
            SectionSchema(title="Services & Statements of Work", section_type="prose", guidance="Framework for issuing individual SOWs under the MSA umbrella."),
            SectionSchema(title="Intellectual Property Rights", section_type="clause", guidance="Pre-existing IP vs Work Product ownership, work-for-hire provisions."),
            SectionSchema(title="Indemnification & Liability Limits", section_type="clause", guidance="Mutual indemnification, direct vs consequential damages, and liability caps."),
            SectionSchema(title="Term & Termination", section_type="clause", guidance="Duration, convenience termination (30-day notice), cause termination, and transition."),
        ],
    ),
    "contract_nda": TemplateMetaData(
        id="contract_nda",
        category=ProcurementDocType.VENDOR_CONTRACT,
        title="Mutual Non-Disclosure Agreement",
        description="Standard bilateral confidentiality agreement for commercial discussions.",
        tone="Protective & Precise",
        tone_description="Strict legal definitions governing confidential trade secrets and data.",
        icon="🔒",
        sections=[
            SectionSchema(title="Definition of Confidential Info", section_type="clause", guidance="Scope of protected information, oral disclosure rules, and exclusions."),
            SectionSchema(title="Obligations & Standard of Care", section_type="clause", guidance="Duty to protect, restricted use sole for evaluation, no reverse engineering."),
            SectionSchema(title="Term & Return of Materials", section_type="clause", guidance="Confidentiality duration (3 years), destruction protocols upon request."),
        ],
    ),

    # Scorecard & PO Templates
    "scorecard_kpi": TemplateMetaData(
        id="scorecard_kpi",
        category=ProcurementDocType.VENDOR_SCORECARD,
        title="Quarterly Vendor KPI Scorecard",
        description="Structured performance assessment matrix for vendor reviews.",
        tone="Objective & Analytical",
        tone_description="Metric-driven rating format comparing SLA metrics to baseline targets.",
        icon="📈",
        sections=[
            SectionSchema(title="Vendor Summary & Evaluation Period", section_type="prose", guidance="Vendor profile, contract reference, evaluation quarter, and reviewer names."),
            SectionSchema(title="Quality & SLA Metrics Breakdown", section_type="prose", guidance="Scored breakdown of deliverable accuracy, defect rate, and uptime SLA."),
            SectionSchema(title="Commercial & Relationship Rating", section_type="prose", guidance="Invoicing transparency, account team responsiveness, and cost savings."),
            SectionSchema(title="Final Tier Rating & Action Plan", section_type="prose", guidance="Weighted final score, vendor tier (Tier 1 Preferred / At Risk), and action items."),
        ],
    ),
    "po_standard": TemplateMetaData(
        id="po_standard",
        category=ProcurementDocType.PURCHASE_ORDER,
        title="Standard Authorized Purchase Order",
        description="Official financial authorization document for goods and service delivery.",
        tone="Formal & Transactional",
        tone_description="Binding financial commitment document with itemized billing details.",
        icon="🧾",
        sections=[
            SectionSchema(title="Header & Party Details", section_type="prose", guidance="PO Number, PO Date, Purchaser Name, Billing Address, Shipping Address."),
            SectionSchema(title="Authorized Line Items", section_type="line_items", guidance="Item descriptions, part numbers, quantities, unit prices, and total amount."),
            SectionSchema(title="Payment & Delivery Instructions", section_type="payment_schedule", guidance="Payment terms (Net 30), shipping instructions, and invoice submission contact."),
        ],
    ),

    # Custom Template
    "custom_template": TemplateMetaData(
        id="custom_template",
        category=ProcurementDocType.RFP,
        title="Custom Template Builder",
        description="Design your own custom section layout, guidance rules, and document structure.",
        tone="Custom User Defined",
        tone_description="User tailored section outlines and guidance.",
        icon="🎨",
        sections=[
            SectionSchema(title="Custom Section 1", section_type="prose", guidance="User defined section guidance."),
        ],
    ),
}


PROCUREMENT_TEMPLATES: dict[ProcurementDocType, list[SectionSchema]] = {
    doc_type: [
        tmpl.sections for tmpl in PREBUILT_TEMPLATES.values() if tmpl.category == doc_type
    ][0]
    for doc_type in ProcurementDocType
}


def get_template_by_id(template_id: str) -> TemplateMetaData:
    return PREBUILT_TEMPLATES.get(template_id, PREBUILT_TEMPLATES["rfp_enterprise"])


def get_procurement_sections(doc_type: ProcurementDocType, template_id: str | None = None) -> list[SectionSchema]:
    if template_id and template_id in PREBUILT_TEMPLATES:
        return PREBUILT_TEMPLATES[template_id].sections
    return PROCUREMENT_TEMPLATES.get(doc_type, PROCUREMENT_TEMPLATES[ProcurementDocType.RFP])

