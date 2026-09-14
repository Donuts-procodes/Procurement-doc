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

EXPANSION_SECTIONS_PER_DOC_TYPE: dict[ProcurementDocType, list[SectionSchema]] = {
    ProcurementDocType.RFP: [
        SectionSchema(title="Technical Architecture & System Specifications", section_type="prose", guidance="Detailed infrastructure standards, data flow, API architectures, and technology specifications."),
        SectionSchema(title="Functional & Operational Requirements", section_type="prose", guidance="Itemized functional capabilities, administrative workflows, and user requirements."),
        SectionSchema(title="Detailed Cost Breakdown & Line Items", section_type="line_items", guidance="Itemized transparent cost breakdown, rate categories, and unit pricing."),
        SectionSchema(title="Milestone Deliverables & Payment Schedule", section_type="payment_schedule", guidance="Deliverable allocations, percentage payments, and invoice trigger conditions."),
        SectionSchema(title="SLA Commitments & Governance Framework", section_type="prose", guidance="Service level targets, 99.9% availability, issue escalation, and governance reporting."),
        SectionSchema(title="Data Protection, Security & Compliance", section_type="clause", guidance="Data privacy regulations, SOC2/GDPR compliance, access controls, and statutory requirements."),
        SectionSchema(title="Quality Assurance & Acceptance Testing", section_type="prose", guidance="Testing methodologies, staging reviews, defect resolution, and sign-off criteria."),
        SectionSchema(title="Training, Documentation & Handover", section_type="prose", guidance="Administrative manuals, user onboarding sessions, and operational handover."),
        SectionSchema(title="Formal Execution & Sign-Off Authorization", section_type="clause", guidance="Authorized signatory execution blocks and binding procurement sign-off."),
    ],
    ProcurementDocType.SOW: [
        SectionSchema(title="Technical Architecture & Integration Standards", section_type="prose", guidance="Platform baseline, architecture standards, and third-party integrations."),
        SectionSchema(title="Milestone Deliverable Payment Allocations", section_type="payment_schedule", guidance="Structured milestone payment schedule tied to accepted deliverables."),
        SectionSchema(title="Key Performance Indicators & Service Levels", section_type="prose", guidance="Response SLAs, code review criteria, and performance benchmarks."),
        SectionSchema(title="Acceptance Criteria & Inspection Protocol", section_type="clause", guidance="Formal deliverable review periods, sign-off workflow, and deficiency remedies."),
        SectionSchema(title="Governance, Communication & Change Orders", section_type="prose", guidance="Meeting cadences, escalation paths, and scope change management."),
        SectionSchema(title="Confidentiality & Intellectual Property Transfer", section_type="clause", guidance="Ownership of code, documentation, work product, and non-disclosure terms."),
        SectionSchema(title="Formal Execution & Sign-Off Authorization", section_type="clause", guidance="Binding authorized signatures and execution certification."),
    ],
    ProcurementDocType.RFQ: [
        SectionSchema(title="Detailed Quotation & Line Items", section_type="line_items", guidance="Comprehensive itemized bill of materials, unit rates, and pricing."),
        SectionSchema(title="Delivery Logistics & Packaging Protocol", section_type="prose", guidance="Shipping terms, freight logistics, packaging, and receipt criteria."),
        SectionSchema(title="Warranty, Defect Remediation & AMC", section_type="clause", guidance="Standard replacement terms, repair turnaround, and defect remediation."),
        SectionSchema(title="Milestone Payment Schedule & Terms", section_type="payment_schedule", guidance="Payment milestones, invoicing rules, and currency commitments."),
        SectionSchema(title="Statutory Certifications & Compliance", section_type="clause", guidance="Regulatory compliance, manufacturer certifications, and standards."),
        SectionSchema(title="Formal Execution & Sign-Off Authorization", section_type="clause", guidance="Authorized commercial signatures and RFQ binding acceptance."),
    ],
    ProcurementDocType.VENDOR_CONTRACT: [
        SectionSchema(title="Scope of Services & Performance Baseline", section_type="prose", guidance="Authorized scope boundaries, quality baseline, and delivery standard."),
        SectionSchema(title="Fee Schedule & Authorized Compensation", section_type="line_items", guidance="Detailed fee schedule, hourly rates, and allowable expenses."),
        SectionSchema(title="Milestone Payment Terms & Allocations", section_type="payment_schedule", guidance="Payment milestone allocations and invoicing rules."),
        SectionSchema(title="Service Level Agreements & Remedies", section_type="prose", guidance="Performance credits, uptime guarantees, and remedial obligations."),
        SectionSchema(title="Data Protection, IP & Confidential Information", section_type="clause", guidance="Work-made-for-hire IP assignment, non-disclosure, and data privacy."),
        SectionSchema(title="Indemnification, Liability & Terminations", section_type="clause", guidance="Mutual indemnification, cap on liability, and termination rights."),
        SectionSchema(title="Formal Execution & Sign-Off Authorization", section_type="clause", guidance="Execution blocks, corporate seals, and binding signatory clauses."),
    ],
    ProcurementDocType.RFI: [
        SectionSchema(title="Technical Architecture & Product Roadmap", section_type="prose", guidance="System topology, API capabilities, and technology vision."),
        SectionSchema(title="Data Protection, Security & Hosting Infrastructure", section_type="prose", guidance="Cloud hosting, certifications, data isolation, and cybersecurity controls."),
        SectionSchema(title="Commercial Pricing Models & Licensing Options", section_type="prose", guidance="Indicative enterprise tiers, seat licenses, and commercial arrangements."),
        SectionSchema(title="Implementation Methodology & Case Studies", section_type="prose", guidance="Deployment timetables, proven client references, and rollout practices."),
        SectionSchema(title="Operational Resilience & Disaster Recovery", section_type="prose", guidance="Business continuity, RTO/RPO metrics, and risk management."),
    ],
    ProcurementDocType.PURCHASE_ORDER: [
        SectionSchema(title="Itemized Authorized Line Items", section_type="line_items", guidance="Part numbers, quantities, unit prices, and total financial amounts."),
        SectionSchema(title="Delivery Location & Fulfillment Instructions", section_type="prose", guidance="Site contacts, receiving guidelines, and freight terms."),
        SectionSchema(title="Milestone Payment Schedule & Invoicing Terms", section_type="payment_schedule", guidance="Invoice submission rules, Net terms, and payment allocation."),
        SectionSchema(title="Inspection, Quality & Acceptance Protocol", section_type="clause", guidance="Inspection rights, defect rejection, and return shipping rules."),
        SectionSchema(title="Authorized Corporate Signatures & Order Verification", section_type="clause", guidance="Authorized purchasing agent signature and PO validation."),
    ],
    ProcurementDocType.VENDOR_SCORECARD: [
        SectionSchema(title="Operational SLA Attainment Breakdown", section_type="prose", guidance="Recorded uptime, response times, and incident resolution scorecard."),
        SectionSchema(title="Quality, Defect & Delivery Scorecard", section_type="prose", guidance="Scored assessment of milestone punctuality and deliverable accuracy."),
        SectionSchema(title="Commercial Rating & Value Realization", section_type="line_items", guidance="Budget variance, invoice accuracy, and contract savings audit."),
        SectionSchema(title="Continuous Improvement & Remedial Action Plan", section_type="prose", guidance="Corrective action requirements and upcoming performance goals."),
        SectionSchema(title="Authorized Stakeholder Review Signatures", section_type="clause", guidance="Signatures of vendor manager and authorized reviewer."),
    ],
}

# Comprehensive 35-section enterprise taxonomy ensuring documents expanding to 25-30+ pages
# maintain 100% unique, non-overlapping, substantive procurement chapters.
MASTER_PROCUREMENT_TAXONOMY: list[SectionSchema] = [
    SectionSchema(title="Executive Summary & Strategic Objectives", section_type="prose", guidance="High-level commercial context, executive drivers, and core procurement vision."),
    SectionSchema(title="Project Scope Boundaries & Limitations", section_type="prose", guidance="Explicit inclusions, exclusions, edge constraints, and operational boundaries."),
    SectionSchema(title="Technical Architecture & System Specifications", section_type="prose", guidance="Infrastructure baseline, component topology, integration protocols, and technology specifications."),
    SectionSchema(title="Functional & Operational Specifications", section_type="prose", guidance="Itemized capabilities, operational roles, business processes, and user workflows."),
    SectionSchema(title="Non-Functional Performance & Scalability Benchmarks", section_type="prose", guidance="Throughput, latency benchmarks, concurrency targets, and scalability requirements."),
    SectionSchema(title="Cloud Hosting, Infrastructure & DevOps Standards", section_type="prose", guidance="Cloud hosting environment, container orchestration, CI/CD pipelines, and infrastructure governance."),
    SectionSchema(title="Data Security, Encryption & Privacy Compliance", section_type="clause", guidance="Data at rest and in transit encryption standards, tenant isolation, and SOC2/GDPR adherence."),
    SectionSchema(title="Identity, Access Management & Zero-Trust Security", section_type="clause", guidance="Role-based access controls, MFA requirements, zero-trust network protocols, and audit logs."),
    SectionSchema(title="API Integration & Third-Party Interface Protocols", section_type="prose", guidance="RESTful / GraphQL interface standards, payload serialization, rate limits, and webhook handling."),
    SectionSchema(title="Service Level Agreements & Uptime Commitments", section_type="prose", guidance="99.9% availability targets, planned maintenance windows, service credits, and SLA remedy mechanisms."),
    SectionSchema(title="Incident Response, Severity Tiers & Escalation Matrix", section_type="prose", guidance="P1-P4 classification, response/resolution SLAs, 24/7 on-call coverage, and escalation contacts."),
    SectionSchema(title="Business Continuity, Disaster Recovery & High Availability", section_type="prose", guidance="RTO/RPO metrics, automated failover architecture, backup schedules, and annual DR drills."),
    SectionSchema(title="Quality Assurance, Automated Testing & Verification", section_type="prose", guidance="Unit, integration, security test coverage requirements, staging verification, and sign-off criteria."),
    SectionSchema(title="User Acceptance Testing (UAT) & Defect Remediation", section_type="prose", guidance="Acceptance testing cadence, issue classification, turnaround times, and final sign-off gates."),
    SectionSchema(title="Delivery Milestones & Phased Work Breakdown Structure", section_type="prose", guidance="Phased delivery roadmap, work breakdown structure (WBS), key deliverables, and target completion dates."),
    SectionSchema(title="Detailed Cost Breakdown & Line Items", section_type="line_items", guidance="Itemized bill of quantities, labor rate categories, unit pricing, taxes, and grand totals."),
    SectionSchema(title="Milestone Payment Schedule & Invoicing Trigger Conditions", section_type="payment_schedule", guidance="Structured milestone payment allocations, percentage disbursements, and invoice certification criteria."),
    SectionSchema(title="Change Control Management & Scope Variance Protocol", section_type="clause", guidance="Formal change request procedure, impact assessments, pricing adjustments, and approval thresholds."),
    SectionSchema(title="Project Governance, Steering Committee & Reporting Cadence", section_type="prose", guidance="Executive steering cadence, weekly operational syncs, status reporting templates, and risk logs."),
    SectionSchema(title="Vendor Key Personnel, Staffing Matrix & Resource Commitments", section_type="prose", guidance="Named key personnel, staffing allocation matrix, resume qualifications, and substitution rules."),
    SectionSchema(title="Training, Knowledge Transfer & Administrative Handover", section_type="prose", guidance="Super-user training workshops, admin curriculum, recorded modules, and knowledge handover protocols."),
    SectionSchema(title="Operational Runbooks & Deliverables Documentation", section_type="prose", guidance="Standard operating procedures (SOPs), system administration runbooks, API documentation, and asset delivery."),
    SectionSchema(title="Intellectual Property Rights & Work-Product Ownership", section_type="clause", guidance="Pre-existing vendor IP, client work-for-hire assignment, patent rights, and open-source licensing."),
    SectionSchema(title="Indemnification, Limitation of Liability & Insurance Coverage", section_type="clause", guidance="Mutual indemnification, direct vs consequential damages carve-outs, liability caps, and insurance certificates."),
    SectionSchema(title="Confidentiality, Non-Disclosure & Data Retention", section_type="clause", guidance="Trade secret protection, employee confidentiality agreements, statutory retention, and secure destruction."),
    SectionSchema(title="Warranties, Representations & Defect Remediation", section_type="clause", guidance="Express performance warranties, 12-month defect remediation coverage, and manufacturer backing."),
    SectionSchema(title="Termination Rights, Transition Services & Exit Management", section_type="clause", guidance="Termination for convenience, breach cure periods, post-termination transition services, and data extraction."),
    SectionSchema(title="Statutory Certifications, Regulatory Mandates & Standards", section_type="clause", guidance="Industry regulatory compliance (ISO, HIPAA, PCI-DSS), trade authorizations, and statutory filings."),
    SectionSchema(title="Legal Jurisdiction, Governing Law & Dispute Resolution", section_type="clause", guidance="Governing law, forum selection, mandatory mediation, and binding arbitration procedures."),
    SectionSchema(title="Vendor Evaluation Criteria & Continuous Improvement Scorecard", section_type="prose", guidance="Quarterly vendor scoring metrics, cost efficiency reviews, and service improvement action plans."),
    SectionSchema(title="Subcontracting, Third-Party Providers & Dependency Risk", section_type="clause", guidance="Subcontractor disclosure requirements, flow-down terms, and third-party risk management."),
    SectionSchema(title="Environmental, Social & Corporate Governance (ESG) Compliance", section_type="clause", guidance="Sustainability benchmarks, ethical labor standards, supplier diversity, and ESG commitments."),
    SectionSchema(title="Audit Rights, Inspection & Regulatory Oversight", section_type="clause", guidance="Annual buyer and third-party auditor inspection rights, facility access, and logging verification."),
    SectionSchema(title="Hardware, Tooling & Environment Requirements", section_type="prose", guidance="Prerequisite hardware specifications, developer environment tooling, and client infrastructure dependencies."),
    SectionSchema(title="Formal Execution & Sign-Off Authorization", section_type="clause", guidance="Authorized commercial signatures, corporate seal, power of attorney validation, and binding execution."),
]


def get_template_by_id(template_id: str) -> TemplateMetaData:
    return PREBUILT_TEMPLATES.get(template_id, PREBUILT_TEMPLATES["rfp_enterprise"])


def get_procurement_sections(
    doc_type: ProcurementDocType,
    template_id: str | None = None,
    num_pages: int | None = None,
) -> list[SectionSchema]:
    if template_id and template_id in PREBUILT_TEMPLATES:
        base_sections = list(PREBUILT_TEMPLATES[template_id].sections)
    else:
        base_sections = list(PROCUREMENT_TEMPLATES.get(doc_type, PROCUREMENT_TEMPLATES[ProcurementDocType.RFP]))

    if not num_pages or num_pages == len(base_sections):
        return base_sections

    if num_pages < len(base_sections):
        return base_sections[:max(1, num_pages)]

    existing_titles = {s.title.lower() for s in base_sections}
    result_sections = list(base_sections)

    # 1. Expand from doc-type specific pool
    expansion_pool = EXPANSION_SECTIONS_PER_DOC_TYPE.get(doc_type, EXPANSION_SECTIONS_PER_DOC_TYPE[ProcurementDocType.RFP])
    for exp_sec in expansion_pool:
        if len(result_sections) >= num_pages:
            break
        if exp_sec.title.lower() not in existing_titles:
            result_sections.append(exp_sec)
            existing_titles.add(exp_sec.title.lower())

    # 2. If user requests up to 25-35 pages, draw from comprehensive Master Taxonomy
    if len(result_sections) < num_pages:
        for master_sec in MASTER_PROCUREMENT_TAXONOMY:
            if len(result_sections) >= num_pages:
                break
            # Check for title uniqueness or core title similarity
            master_title_lower = master_sec.title.lower()
            if master_title_lower not in existing_titles:
                result_sections.append(master_sec)
                existing_titles.add(master_title_lower)

    return result_sections

