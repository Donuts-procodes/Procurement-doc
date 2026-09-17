from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.schemas import ProcurementDocType


# ============================================================================
# ENUMS & TYPES
# ============================================================================

class SectionType(str, Enum):
    """Section rendering type."""
    PROSE = "prose"
    LINE_ITEMS = "line_items"
    PAYMENT_SCHEDULE = "payment_schedule"
    CLAUSE = "clause"


# ============================================================================
# SCHEMA MODELS
# ============================================================================

class SectionSchema(BaseModel):
    """
    Represents a document section with unique ID, content, and composition metadata.
    """
    section_id: str = Field(default="")
    title: str
    section_type: str = "prose"
    guidance: str
    tags: list[str] = Field(default_factory=list)
    page_estimate: int = 1

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("section_type", mode="before")
    @classmethod
    def normalize_section_type(cls, v: Any) -> str:
        if isinstance(v, SectionType):
            return v.value
        return str(v)


class TemplateMetaData(BaseModel):
    """
    Defines a prebuilt template with composition rules.
    Maintains backwards compatibility by providing .sections as a property
    or direct attribute.
    """
    id: str
    category: ProcurementDocType
    title: str
    description: str
    tone: str
    tone_description: str
    icon: str
    section_ids: list[str] = Field(default_factory=list)
    expansion_tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)

    @property
    def sections(self) -> list[SectionSchema]:
        """Backwards compatibility for code accessing meta.sections."""
        return [SECTION_REGISTRY[sid] for sid in self.section_ids if sid in SECTION_REGISTRY]


# ============================================================================
# SECTION REGISTRY: Single Source of Truth
# ============================================================================

SECTION_REGISTRY: dict[str, SectionSchema] = {
    # Executive & Strategic Sections
    "exec_summary": SectionSchema(
        section_id="exec_summary",
        title="Executive Summary & Strategic Objectives",
        section_type="prose",
        guidance="High-level commercial context, executive drivers, and core procurement vision.",
        tags=["rfp", "sow", "vendor_contract", "master"],
        page_estimate=1,
    ),
    "scope_boundaries": SectionSchema(
        section_id="scope_boundaries",
        title="Project Scope Boundaries & Limitations",
        section_type="prose",
        guidance="Explicit inclusions, exclusions, edge constraints, and operational boundaries.",
        tags=["rfp", "sow", "vendor_contract", "expansion", "master"],
        page_estimate=1,
    ),

    # Technical Architecture & Infrastructure
    "technical_architecture": SectionSchema(
        section_id="technical_architecture",
        title="Technical Architecture & System Specifications",
        section_type="prose",
        guidance="Infrastructure baseline, component topology, integration protocols, and technology specifications.",
        tags=["rfp", "sow", "rfi", "expansion", "master"],
        page_estimate=2,
    ),
    "functional_specs": SectionSchema(
        section_id="functional_specs",
        title="Functional & Operational Specifications",
        section_type="prose",
        guidance="Itemized capabilities, operational roles, business processes, and user workflows.",
        tags=["rfp", "sow", "expansion", "master"],
        page_estimate=2,
    ),
    "nonfunctional_performance": SectionSchema(
        section_id="nonfunctional_performance",
        title="Non-Functional Performance & Scalability Benchmarks",
        section_type="prose",
        guidance="Throughput, latency benchmarks, concurrency targets, and scalability requirements.",
        tags=["rfp", "expansion", "master"],
        page_estimate=1,
    ),
    "cloud_infrastructure": SectionSchema(
        section_id="cloud_infrastructure",
        title="Cloud Hosting, Infrastructure & DevOps Standards",
        section_type="prose",
        guidance="Cloud hosting environment, container orchestration, CI/CD pipelines, and infrastructure governance.",
        tags=["rfp", "expansion", "master"],
        page_estimate=1,
    ),
    "hardware_requirements": SectionSchema(
        section_id="hardware_requirements",
        title="Hardware, Tooling & Environment Requirements",
        section_type="prose",
        guidance="Prerequisite hardware specifications, developer environment tooling, and client infrastructure dependencies.",
        tags=["rfp", "sow", "expansion", "master"],
        page_estimate=1,
    ),

    # Security & Compliance
    "data_security": SectionSchema(
        section_id="data_security",
        title="Data Security, Encryption & Privacy Compliance",
        section_type="clause",
        guidance="Data at rest and in transit encryption standards, tenant isolation, and SOC2/GDPR adherence.",
        tags=["rfp", "rfi", "vendor_contract", "expansion", "master"],
        page_estimate=2,
    ),
    "identity_access": SectionSchema(
        section_id="identity_access",
        title="Identity, Access Management & Zero-Trust Security",
        section_type="clause",
        guidance="Role-based access controls, MFA requirements, zero-trust network protocols, and audit logs.",
        tags=["rfp", "expansion", "master"],
        page_estimate=1,
    ),
    "api_integration": SectionSchema(
        section_id="api_integration",
        title="API Integration & Third-Party Interface Protocols",
        section_type="prose",
        guidance="RESTful / GraphQL interface standards, payload serialization, rate limits, and webhook handling.",
        tags=["rfp", "rfi", "expansion", "master"],
        page_estimate=1,
    ),

    # Service Levels & Operations
    "sla_uptime": SectionSchema(
        section_id="sla_uptime",
        title="Service Level Agreements & Uptime Commitments",
        section_type="prose",
        guidance="99.9% availability targets, planned maintenance windows, service credits, and SLA remedy mechanisms.",
        tags=["rfp", "sow", "vendor_contract", "expansion", "master"],
        page_estimate=1,
    ),
    "incident_response": SectionSchema(
        section_id="incident_response",
        title="Incident Response, Severity Tiers & Escalation Matrix",
        section_type="prose",
        guidance="P1-P4 classification, response/resolution SLAs, 24/7 on-call coverage, and escalation contacts.",
        tags=["rfp", "expansion", "master"],
        page_estimate=1,
    ),
    "business_continuity": SectionSchema(
        section_id="business_continuity",
        title="Business Continuity, Disaster Recovery & High Availability",
        section_type="prose",
        guidance="RTO/RPO metrics, automated failover architecture, backup schedules, and annual DR drills.",
        tags=["rfp", "rfi", "vendor_contract", "expansion", "master"],
        page_estimate=1,
    ),

    # Quality Assurance & Testing
    "qa_testing": SectionSchema(
        section_id="qa_testing",
        title="Quality Assurance, Automated Testing & Verification",
        section_type="prose",
        guidance="Unit, integration, security test coverage requirements, staging verification, and sign-off criteria.",
        tags=["rfp", "sow", "expansion", "master"],
        page_estimate=1,
    ),
    "uat_testing": SectionSchema(
        section_id="uat_testing",
        title="User Acceptance Testing (UAT) & Defect Remediation",
        section_type="prose",
        guidance="Acceptance testing cadence, issue classification, turnaround times, and final sign-off gates.",
        tags=["rfp", "sow", "expansion", "master"],
        page_estimate=1,
    ),

    # Project Planning & Delivery
    "milestones_wbs": SectionSchema(
        section_id="milestones_wbs",
        title="Delivery Milestones & Phased Work Breakdown Structure",
        section_type="prose",
        guidance="Phased delivery roadmap, work breakdown structure (WBS), key deliverables, and target completion dates.",
        tags=["rfp", "sow", "expansion", "master"],
        page_estimate=2,
    ),
    "project_governance": SectionSchema(
        section_id="project_governance",
        title="Project Governance, Steering Committee & Reporting Cadence",
        section_type="prose",
        guidance="Executive steering cadence, weekly operational syncs, status reporting templates, and risk logs.",
        tags=["rfp", "sow", "expansion", "master"],
        page_estimate=1,
    ),
    "change_control": SectionSchema(
        section_id="change_control",
        title="Change Control Management & Scope Variance Protocol",
        section_type="clause",
        guidance="Formal change request procedure, impact assessments, pricing adjustments, and approval thresholds.",
        tags=["rfp", "sow", "expansion", "master"],
        page_estimate=1,
    ),

    # Staffing & Resources
    "vendor_staffing": SectionSchema(
        section_id="vendor_staffing",
        title="Vendor Key Personnel, Staffing Matrix & Resource Commitments",
        section_type="prose",
        guidance="Named key personnel, staffing allocation matrix, resume qualifications, and substitution rules.",
        tags=["rfp", "sow", "expansion", "master"],
        page_estimate=1,
    ),

    # Training & Knowledge Transfer
    "training_handover": SectionSchema(
        section_id="training_handover",
        title="Training, Knowledge Transfer & Administrative Handover",
        section_type="prose",
        guidance="Super-user training workshops, admin curriculum, recorded modules, and knowledge handover protocols.",
        tags=["rfp", "sow", "expansion", "master"],
        page_estimate=1,
    ),
    "documentation_runbooks": SectionSchema(
        section_id="documentation_runbooks",
        title="Operational Runbooks & Deliverables Documentation",
        section_type="prose",
        guidance="Standard operating procedures (SOPs), system administration runbooks, API documentation, and asset delivery.",
        tags=["rfp", "sow", "expansion", "master"],
        page_estimate=2,
    ),

    # Legal & IP
    "ip_rights": SectionSchema(
        section_id="ip_rights",
        title="Intellectual Property Rights & Work-Product Ownership",
        section_type="clause",
        guidance="Pre-existing vendor IP, client work-for-hire assignment, patent rights, and open-source licensing.",
        tags=["rfp", "sow", "vendor_contract", "expansion", "master"],
        page_estimate=1,
    ),
    "indemnification": SectionSchema(
        section_id="indemnification",
        title="Indemnification, Limitation of Liability & Insurance Coverage",
        section_type="clause",
        guidance="Mutual indemnification, direct vs consequential damages carve-outs, liability caps, and insurance certificates.",
        tags=["rfp", "sow", "vendor_contract", "expansion", "master"],
        page_estimate=1,
    ),
    "confidentiality": SectionSchema(
        section_id="confidentiality",
        title="Confidentiality, Non-Disclosure & Data Retention",
        section_type="clause",
        guidance="Trade secret protection, employee confidentiality agreements, statutory retention, and secure destruction.",
        tags=["rfp", "sow", "vendor_contract", "expansion", "master"],
        page_estimate=1,
    ),
    "warranties": SectionSchema(
        section_id="warranties",
        title="Warranties, Representations & Defect Remediation",
        section_type="clause",
        guidance="Express performance warranties, 12-month defect remediation coverage, and manufacturer backing.",
        tags=["rfp", "rfq", "vendor_contract", "expansion", "master"],
        page_estimate=1,
    ),

    # Commercial & Payment
    "cost_breakdown": SectionSchema(
        section_id="cost_breakdown",
        title="Detailed Cost Breakdown & Line Items",
        section_type="line_items",
        guidance="Itemized bill of quantities, labor rate categories, unit pricing, taxes, and grand totals.",
        tags=["rfp", "rfq", "sow", "vendor_contract", "po", "expansion", "master"],
        page_estimate=1,
    ),
    "payment_schedule": SectionSchema(
        section_id="payment_schedule",
        title="Milestone Payment Schedule & Invoicing Trigger Conditions",
        section_type="payment_schedule",
        guidance="Structured milestone payment allocations, percentage disbursements, and invoice certification criteria.",
        tags=["rfp", "rfq", "sow", "vendor_contract", "po", "expansion", "master"],
        page_estimate=1,
    ),

    # Termination & Exit
    "termination": SectionSchema(
        section_id="termination",
        title="Termination Rights, Transition Services & Exit Management",
        section_type="clause",
        guidance="Termination for convenience, breach cure periods, post-termination transition services, and data extraction.",
        tags=["rfp", "sow", "vendor_contract", "expansion", "master"],
        page_estimate=1,
    ),

    # Compliance & Governance
    "statutory_compliance": SectionSchema(
        section_id="statutory_compliance",
        title="Statutory Certifications, Regulatory Mandates & Standards",
        section_type="clause",
        guidance="Industry regulatory compliance (ISO, HIPAA, PCI-DSS), trade authorizations, and statutory filings.",
        tags=["rfp", "rfq", "vendor_contract", "expansion", "master"],
        page_estimate=1,
    ),
    "legal_jurisdiction": SectionSchema(
        section_id="legal_jurisdiction",
        title="Legal Jurisdiction, Governing Law & Dispute Resolution",
        section_type="clause",
        guidance="Governing law, forum selection, mandatory mediation, and binding arbitration procedures.",
        tags=["rfp", "sow", "vendor_contract", "expansion", "master"],
        page_estimate=1,
    ),
    "subcontracting": SectionSchema(
        section_id="subcontracting",
        title="Subcontracting, Third-Party Providers & Dependency Risk",
        section_type="clause",
        guidance="Subcontractor disclosure requirements, flow-down terms, and third-party risk management.",
        tags=["rfp", "vendor_contract", "expansion", "master"],
        page_estimate=1,
    ),
    "audit_rights": SectionSchema(
        section_id="audit_rights",
        title="Audit Rights, Inspection & Regulatory Oversight",
        section_type="clause",
        guidance="Annual buyer and third-party auditor inspection rights, facility access, and logging verification.",
        tags=["rfp", "vendor_contract", "expansion", "master"],
        page_estimate=1,
    ),

    # ESG & Social
    "esg_compliance": SectionSchema(
        section_id="esg_compliance",
        title="Environmental, Social & Corporate Governance (ESG) Compliance",
        section_type="clause",
        guidance="Sustainability benchmarks, ethical labor standards, supplier diversity, and ESG commitments.",
        tags=["rfp", "vendor_contract", "expansion", "master"],
        page_estimate=1,
    ),

    # Performance & Vendor Management
    "vendor_scorecard_kpi": SectionSchema(
        section_id="vendor_scorecard_kpi",
        title="Operational SLA Attainment Breakdown",
        section_type="prose",
        guidance="Recorded uptime, response times, and incident resolution scorecard.",
        tags=["scorecard", "expansion", "master"],
        page_estimate=1,
    ),
    "vendor_quality": SectionSchema(
        section_id="vendor_quality",
        title="Quality, Defect & Delivery Scorecard",
        section_type="prose",
        guidance="Scored assessment of milestone punctuality and deliverable accuracy.",
        tags=["scorecard", "expansion", "master"],
        page_estimate=1,
    ),
    "vendor_commercial": SectionSchema(
        section_id="vendor_commercial",
        title="Commercial Rating & Value Realization",
        section_type="line_items",
        guidance="Budget variance, invoice accuracy, and contract savings audit.",
        tags=["scorecard", "expansion", "master"],
        page_estimate=1,
    ),
    "vendor_improvement": SectionSchema(
        section_id="vendor_improvement",
        title="Continuous Improvement & Remedial Action Plan",
        section_type="prose",
        guidance="Corrective action requirements and upcoming performance goals.",
        tags=["scorecard", "expansion", "master"],
        page_estimate=1,
    ),
    "vendor_evaluation": SectionSchema(
        section_id="vendor_evaluation",
        title="Vendor Evaluation Criteria & Continuous Improvement Scorecard",
        section_type="prose",
        guidance="Quarterly vendor scoring metrics, cost efficiency reviews, and service improvement action plans.",
        tags=["rfp", "expansion", "master"],
        page_estimate=1,
    ),

    # RFP-Specific Sections
    "scope_of_work": SectionSchema(
        section_id="scope_of_work",
        title="Scope of Work",
        section_type="prose",
        guidance="Detailed technical and operational requirements, project context, and core objectives.",
        tags=["rfp", "base"],
        page_estimate=1,
    ),
    "eligibility_criteria": SectionSchema(
        section_id="eligibility_criteria",
        title="Eligibility Criteria",
        section_type="prose",
        guidance="Vendor qualifications, certifications, minimum years in business, and financial stability.",
        tags=["rfp", "base"],
        page_estimate=1,
    ),
    "submission_instructions": SectionSchema(
        section_id="submission_instructions",
        title="Submission Instructions",
        section_type="prose",
        guidance="Format requirements, submission deadline, contact point, and required proposal sections.",
        tags=["rfp", "base"],
        page_estimate=1,
    ),
    "evaluation_criteria": SectionSchema(
        section_id="evaluation_criteria",
        title="Evaluation Criteria",
        section_type="prose",
        guidance="Scoring breakdown (e.g. Technical 40%, Cost 40%, Experience 20%) and decision process.",
        tags=["rfp", "base"],
        page_estimate=1,
    ),
    "project_timeline": SectionSchema(
        section_id="project_timeline",
        title="Project Timeline",
        section_type="prose",
        guidance="Key procurement milestones: RFP issue date, Q&A window, proposal deadline, award date.",
        tags=["rfp", "base"],
        page_estimate=1,
    ),
    "terms_conditions": SectionSchema(
        section_id="terms_conditions",
        title="Terms & Conditions",
        section_type="clause",
        guidance="Standard procurement terms, confidentiality, proposal validity period, and governing law.",
        tags=["rfp", "base"],
        page_estimate=1,
    ),

    # RFP Government/Regulatory Specific
    "exec_summary_gov": SectionSchema(
        section_id="exec_summary_gov",
        title="Executive Summary & Purpose",
        section_type="prose",
        guidance="Public interest scope, statutory background, and high-level mandate.",
        tags=["rfp_gov", "base"],
        page_estimate=1,
    ),
    "mandatory_compliance": SectionSchema(
        section_id="mandatory_compliance",
        title="Mandatory Compliance & Certifications",
        section_type="clause",
        guidance="Regulatory compliance, non-collusion affidavits, security clearances, and ISO certifications.",
        tags=["rfp_gov", "base"],
        page_estimate=1,
    ),
    "technical_specs_gov": SectionSchema(
        section_id="technical_specs_gov",
        title="Technical Specifications & Deliverables",
        section_type="prose",
        guidance="Rigid technical baseline, functional capabilities, and mandatory standards.",
        tags=["rfp_gov", "base"],
        page_estimate=1,
    ),
    "proposal_costing": SectionSchema(
        section_id="proposal_costing",
        title="Proposal Costing Structure",
        section_type="line_items",
        guidance="Itemized transparent cost breakdown for audit review.",
        tags=["rfp_gov", "base"],
        page_estimate=1,
    ),
    "weighted_scoring": SectionSchema(
        section_id="weighted_scoring",
        title="Weighted Scoring Matrix",
        section_type="prose",
        guidance="Publicly disclosed scoring formula and evaluation panel process.",
        tags=["rfp_gov", "base"],
        page_estimate=1,
    ),
    "statutory_terms": SectionSchema(
        section_id="statutory_terms",
        title="Statutory Terms & Conditions",
        section_type="clause",
        guidance="Public procurement general provisions, FOIA clauses, and dispute resolution.",
        tags=["rfp_gov", "base"],
        page_estimate=1,
    ),

    # RFP Tech/SaaS Specific
    "system_architecture": SectionSchema(
        section_id="system_architecture",
        title="System Architecture & Scope",
        section_type="prose",
        guidance="Target system architecture, cloud deployment, and integration specs.",
        tags=["rfp_tech", "base"],
        page_estimate=1,
    ),
    "security_privacy": SectionSchema(
        section_id="security_privacy",
        title="Data Security & Privacy Requirements",
        section_type="clause",
        guidance="SOC2 Type II, GDPR/CCPA, encryption standards, and vulnerability management.",
        tags=["rfp_tech", "base"],
        page_estimate=1,
    ),
    "sla_support": SectionSchema(
        section_id="sla_support",
        title="SLA & Support Framework",
        section_type="prose",
        guidance="Uptime targets (99.9%), incident response tiers, and escalation paths.",
        tags=["rfp_tech", "base"],
        page_estimate=1,
    ),
    "vendor_tech_qualifications": SectionSchema(
        section_id="vendor_tech_qualifications",
        title="Vendor Technical Qualifications",
        section_type="prose",
        guidance="Engineering team pedigree, past implementations, and customer references.",
        tags=["rfp_tech", "base"],
        page_estimate=1,
    ),
    "licensing_model": SectionSchema(
        section_id="licensing_model",
        title="Licensing & Commercial Model",
        section_type="line_items",
        guidance="Subscription tiers, user seats, API calls, and implementation fees.",
        tags=["rfp_tech", "base"],
        page_estimate=1,
    ),

    # RFQ Specific Sections
    "vendor_info": SectionSchema(
        section_id="vendor_info",
        title="Vendor & Requisition Info",
        section_type="prose",
        guidance="RFQ reference, buyer details, vendor contact info, and response date.",
        tags=["rfq_goods", "base"],
        page_estimate=1,
    ),
    "itemized_quotation": SectionSchema(
        section_id="itemized_quotation",
        title="Itemized Quotation Table",
        section_type="line_items",
        guidance="SKU codes, descriptions, quantities, unit prices, tax, and freight costs.",
        tags=["rfq_goods", "base"],
        page_estimate=1,
    ),
    "delivery_fulfillment": SectionSchema(
        section_id="delivery_fulfillment",
        title="Delivery & Fulfillment Terms",
        section_type="prose",
        guidance="Incoterms (FOB/DDP), shipping destination, lead times, and packaging rules.",
        tags=["rfq_goods", "rfq_services", "base"],
        page_estimate=1,
    ),
    "commercial_terms": SectionSchema(
        section_id="commercial_terms",
        title="Commercial Payment Terms",
        section_type="clause",
        guidance="Standard payment terms (Net 30/60), early payment discounts, and currency.",
        tags=["rfq_goods", "base"],
        page_estimate=1,
    ),

    # RFQ Services Specific
    "service_scope": SectionSchema(
        section_id="service_scope",
        title="Service Scope Overview",
        section_type="prose",
        guidance="Summary of requested professional labor categories and estimated effort.",
        tags=["rfq_services", "base"],
        page_estimate=1,
    ),
    "hourly_rates": SectionSchema(
        section_id="hourly_rates",
        title="Hourly Rate Card Breakdown",
        section_type="line_items",
        guidance="Labor roles (Junior/Senior/Architect), hourly billing rates, and cap limits.",
        tags=["rfq_services", "base"],
        page_estimate=1,
    ),
    "travel_expense": SectionSchema(
        section_id="travel_expense",
        title="Travel & Expense Policy",
        section_type="clause",
        guidance="Reimbursement bounds, pre-approval rules, and capped per diem rates.",
        tags=["rfq_services", "base"],
        page_estimate=1,
    ),
    "validity_payment": SectionSchema(
        section_id="validity_payment",
        title="Validity & Payment Terms",
        section_type="clause",
        guidance="Rate lock duration, invoicing cadence, and payment terms.",
        tags=["rfq_services", "base"],
        page_estimate=1,
    ),

    # RFI Specific Sections
    "problem_statement": SectionSchema(
        section_id="problem_statement",
        title="Problem Statement & Background",
        section_type="prose",
        guidance="Business challenge driving the market inquiry and vision.",
        tags=["rfi_market", "base"],
        page_estimate=1,
    ),
    "vendor_organization": SectionSchema(
        section_id="vendor_organization",
        title="Vendor Organization & Overview",
        section_type="prose",
        guidance="Company background, footprint, ownership, and core offerings.",
        tags=["rfi_market", "base"],
        page_estimate=1,
    ),
    "solution_capabilities": SectionSchema(
        section_id="solution_capabilities",
        title="Solution Capabilities & Features",
        section_type="prose",
        guidance="Open-ended questions on key features, differentiators, and roadmap.",
        tags=["rfi_market", "base"],
        page_estimate=1,
    ),
    "indicative_pricing": SectionSchema(
        section_id="indicative_pricing",
        title="Indicative Pricing Models",
        section_type="prose",
        guidance="High-level commercial models without requiring binding quotes.",
        tags=["rfi_market", "base"],
        page_estimate=1,
    ),

    # RFI Security Specific
    "security_governance": SectionSchema(
        section_id="security_governance",
        title="Security Governance & Compliance",
        section_type="prose",
        guidance="Certifications (ISO 27001, SOC 2), compliance framework, and audit frequency.",
        tags=["rfi_security", "base"],
        page_estimate=1,
    ),
    "data_protection": SectionSchema(
        section_id="data_protection",
        title="Data Protection & Encryption",
        section_type="prose",
        guidance="Data at rest/in transit encryption standards, key management, and tenant isolation.",
        tags=["rfi_security", "base"],
        page_estimate=1,
    ),
    "business_continuity_security": SectionSchema(
        section_id="business_continuity_security",
        title="Business Continuity & Incident Response",
        section_type="prose",
        guidance="RTO/RPO metrics, disaster recovery plans, and breach notification SLAs.",
        tags=["rfi_security", "base"],
        page_estimate=1,
    ),

    # SOW Agile Specific
    "project_vision": SectionSchema(
        section_id="project_vision",
        title="Project Vision & Objectives",
        section_type="prose",
        guidance="Target product features, user outcomes, and business goals.",
        tags=["sow_agile", "base"],
        page_estimate=1,
    ),
    "sprint_cadence": SectionSchema(
        section_id="sprint_cadence",
        title="Sprint Cadence & Scope",
        section_type="prose",
        guidance="Sprint length (2 weeks), sprint ceremonies, and backlog management.",
        tags=["sow_agile", "base"],
        page_estimate=1,
    ),
    "team_roster": SectionSchema(
        section_id="team_roster",
        title="Team Roster & Roles",
        section_type="prose",
        guidance="Client vs Vendor staff allocation (PM, Tech Lead, Developers, QA).",
        tags=["sow_agile", "base"],
        page_estimate=1,
    ),
    "acceptance_criteria": SectionSchema(
        section_id="acceptance_criteria",
        title="Acceptance Criteria & Change Control",
        section_type="clause",
        guidance="Definition of Done, testing protocols, and scope change process.",
        tags=["sow_agile", "base"],
        page_estimate=1,
    ),

    # SOW Managed Services Specific
    "managed_environment": SectionSchema(
        section_id="managed_environment",
        title="Managed Environment Scope",
        section_type="prose",
        guidance="Inventory of servers, cloud accounts, networks, and databases managed.",
        tags=["sow_managed", "base"],
        page_estimate=1,
    ),
    "sla_ticket_resolution": SectionSchema(
        section_id="sla_ticket_resolution",
        title="SLA Performance & Ticket Resolution",
        section_type="prose",
        guidance="P1/P2/P3 incident response times, resolution targets, and uptime guarantees.",
        tags=["sow_managed", "base"],
        page_estimate=1,
    ),
    "routine_maintenance": SectionSchema(
        section_id="routine_maintenance",
        title="Routine Maintenance & Backups",
        section_type="prose",
        guidance="Patching windows, backup schedules, DR testing, and monitoring.",
        tags=["sow_managed", "base"],
        page_estimate=1,
    ),
    "monthly_fees": SectionSchema(
        section_id="monthly_fees",
        title="Monthly Recurring Service Fees",
        section_type="payment_schedule",
        guidance="Fixed monthly retainer fees, out-of-scope hourly rates, and billing.",
        tags=["sow_managed", "base"],
        page_estimate=1,
    ),

    # Contract MSA Specific
    "preamble": SectionSchema(
        section_id="preamble",
        title="Preamble & Purpose",
        section_type="prose",
        guidance="Effective date, legal entities, background context, and order of precedence.",
        tags=["contract_msa", "base"],
        page_estimate=1,
    ),
    "services_sow_framework": SectionSchema(
        section_id="services_sow_framework",
        title="Services & Statements of Work",
        section_type="prose",
        guidance="Framework for issuing individual SOWs under the MSA umbrella.",
        tags=["contract_msa", "base"],
        page_estimate=1,
    ),

    # Contract NDA Specific
    "confidential_info_def": SectionSchema(
        section_id="confidential_info_def",
        title="Definition of Confidential Info",
        section_type="clause",
        guidance="Scope of protected information, oral disclosure rules, and exclusions.",
        tags=["contract_nda", "base"],
        page_estimate=1,
    ),
    "obligations_care": SectionSchema(
        section_id="obligations_care",
        title="Obligations & Standard of Care",
        section_type="clause",
        guidance="Duty to protect, restricted use sole for evaluation, no reverse engineering.",
        tags=["contract_nda", "base"],
        page_estimate=1,
    ),
    "term_return": SectionSchema(
        section_id="term_return",
        title="Term & Return of Materials",
        section_type="clause",
        guidance="Confidentiality duration (3 years), destruction protocols upon request.",
        tags=["contract_nda", "base"],
        page_estimate=1,
    ),

    # Scorecard Specific
    "vendor_summary": SectionSchema(
        section_id="vendor_summary",
        title="Vendor Summary & Evaluation Period",
        section_type="prose",
        guidance="Vendor profile, contract reference, evaluation quarter, and reviewer names.",
        tags=["scorecard_kpi", "base"],
        page_estimate=1,
    ),
    "quality_metrics": SectionSchema(
        section_id="quality_metrics",
        title="Quality & SLA Metrics Breakdown",
        section_type="prose",
        guidance="Scored breakdown of deliverable accuracy, defect rate, and uptime SLA.",
        tags=["scorecard_kpi", "base"],
        page_estimate=1,
    ),
    "relationship_rating": SectionSchema(
        section_id="relationship_rating",
        title="Commercial & Relationship Rating",
        section_type="prose",
        guidance="Invoicing transparency, account team responsiveness, and cost savings.",
        tags=["scorecard_kpi", "base"],
        page_estimate=1,
    ),
    "final_rating": SectionSchema(
        section_id="final_rating",
        title="Final Tier Rating & Action Plan",
        section_type="prose",
        guidance="Weighted final score, vendor tier (Tier 1 Preferred / At Risk), and action items.",
        tags=["scorecard_kpi", "base"],
        page_estimate=1,
    ),
    "stakeholder_signatures": SectionSchema(
        section_id="stakeholder_signatures",
        title="Authorized Stakeholder Review Signatures",
        section_type="clause",
        guidance="Signatures of vendor manager and authorized reviewer.",
        tags=["scorecard", "base"],
        page_estimate=1,
    ),

    # PO Specific Sections
    "po_header": SectionSchema(
        section_id="po_header",
        title="Header & Party Details",
        section_type="prose",
        guidance="PO Number, PO Date, Purchaser Name, Billing Address, Shipping Address.",
        tags=["po_standard", "base"],
        page_estimate=1,
    ),
    "po_line_items": SectionSchema(
        section_id="po_line_items",
        title="Authorized Line Items",
        section_type="line_items",
        guidance="Item descriptions, part numbers, quantities, unit prices, and total amount.",
        tags=["po_standard", "base"],
        page_estimate=1,
    ),
    "po_payment_delivery": SectionSchema(
        section_id="po_payment_delivery",
        title="Payment & Delivery Instructions",
        section_type="payment_schedule",
        guidance="Payment terms (Net 30), shipping instructions, and invoice submission contact.",
        tags=["po_standard", "base"],
        page_estimate=1,
    ),

    # Execution & Sign-Off (common to many documents)
    "formal_execution": SectionSchema(
        section_id="formal_execution",
        title="Formal Execution & Sign-Off Authorization",
        section_type="clause",
        guidance="Authorized commercial signatures, corporate seal, power of attorney validation, and binding execution.",
        tags=["rfp", "sow", "vendor_contract", "po", "scorecard", "expansion", "master", "base"],
        page_estimate=1,
    ),

    # Custom placeholder
    "custom_section": SectionSchema(
        section_id="custom_section",
        title="Custom Section 1",
        section_type="prose",
        guidance="User defined section guidance.",
        tags=["custom", "base"],
        page_estimate=1,
    ),
}


# ============================================================================
# PREBUILT TEMPLATES (Composition-Based)
# ============================================================================

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
        section_ids=[
            "scope_of_work",
            "eligibility_criteria",
            "submission_instructions",
            "evaluation_criteria",
            "project_timeline",
            "terms_conditions",
        ],
        expansion_tags=["rfp"],
    ),
    "rfp_gov": TemplateMetaData(
        id="rfp_gov",
        category=ProcurementDocType.RFP,
        title="Government & Public Compliance RFP",
        description="Strict audit-compliant structure for public sector, municipal, or regulated tenders.",
        tone="Strict & Regulatory",
        tone_description="Formal, precise legalistic phrasing adhering to statutory procurement mandates.",
        icon="🏛️",
        section_ids=[
            "exec_summary_gov",
            "mandatory_compliance",
            "technical_specs_gov",
            "proposal_costing",
            "weighted_scoring",
            "statutory_terms",
        ],
        expansion_tags=["rfp_gov"],
    ),
    "rfp_tech": TemplateMetaData(
        id="rfp_tech",
        category=ProcurementDocType.RFP,
        title="IT & SaaS Systems RFP",
        description="Focused on cloud architecture, API integrations, SLA guarantees, and data security.",
        tone="Technical & Rigorous",
        tone_description="In-depth, engineering-focused tone querying system specs and security controls.",
        icon="💻",
        section_ids=[
            "system_architecture",
            "security_privacy",
            "sla_support",
            "vendor_tech_qualifications",
            "licensing_model",
        ],
        expansion_tags=["rfp_tech"],
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
        section_ids=[
            "vendor_info",
            "itemized_quotation",
            "delivery_fulfillment",
            "commercial_terms",
        ],
        expansion_tags=["rfq"],
    ),
    "rfq_services": TemplateMetaData(
        id="rfq_services",
        category=ProcurementDocType.RFQ,
        title="Professional Services Rate Card RFQ",
        description="Pricing solicitation for consulting, engineering hours, or staff augmentation.",
        tone="Commercial & Structured",
        tone_description="Professional rate-card orientation for comparing labor categories.",
        icon="📊",
        section_ids=[
            "service_scope",
            "hourly_rates",
            "travel_expense",
            "validity_payment",
        ],
        expansion_tags=["rfq_services"],
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
        section_ids=[
            "problem_statement",
            "vendor_organization",
            "solution_capabilities",
            "indicative_pricing",
        ],
        expansion_tags=["rfi"],
    ),
    "rfi_security": TemplateMetaData(
        id="rfi_security",
        category=ProcurementDocType.RFI,
        title="Cybersecurity Risk RFI",
        description="Targeted risk assessment questionnaire for third-party software vendors.",
        tone="Analytical & Risk-Conscious",
        tone_description="Probing, security-focused queries examining data protection and resilience.",
        icon="🛡️",
        section_ids=[
            "security_governance",
            "data_protection",
            "business_continuity_security",
        ],
        expansion_tags=["rfi_security"],
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
        section_ids=[
            "project_vision",
            "sprint_cadence",
            "team_roster",
            "payment_schedule",
            "acceptance_criteria",
        ],
        expansion_tags=["sow"],
    ),
    "sow_managed": TemplateMetaData(
        id="sow_managed",
        category=ProcurementDocType.SOW,
        title="Managed Infrastructure Services SOW",
        description="Long-term IT maintenance, cloud infrastructure management, and technical support SOW.",
        tone="Formal & SLA-Oriented",
        tone_description="Definitive, operational tone centered around uptime guarantees and support response.",
        icon="⚙️",
        section_ids=[
            "managed_environment",
            "sla_ticket_resolution",
            "routine_maintenance",
            "monthly_fees",
        ],
        expansion_tags=["sow"],
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
        section_ids=[
            "preamble",
            "services_sow_framework",
            "ip_rights",
            "indemnification",
            "termination",
        ],
        expansion_tags=["vendor_contract"],
    ),
    "contract_nda": TemplateMetaData(
        id="contract_nda",
        category=ProcurementDocType.VENDOR_CONTRACT,
        title="Mutual Non-Disclosure Agreement",
        description="Standard bilateral confidentiality agreement for commercial discussions.",
        tone="Protective & Precise",
        tone_description="Strict legal definitions governing confidential trade secrets and data.",
        icon="🔒",
        section_ids=[
            "confidential_info_def",
            "obligations_care",
            "term_return",
        ],
        expansion_tags=[],
    ),

    # Scorecard Template
    "scorecard_kpi": TemplateMetaData(
        id="scorecard_kpi",
        category=ProcurementDocType.VENDOR_SCORECARD,
        title="Quarterly Vendor KPI Scorecard",
        description="Structured performance assessment matrix for vendor reviews.",
        tone="Objective & Analytical",
        tone_description="Metric-driven rating format comparing SLA metrics to baseline targets.",
        icon="📈",
        section_ids=[
            "vendor_summary",
            "quality_metrics",
            "relationship_rating",
            "final_rating",
        ],
        expansion_tags=["scorecard"],
    ),

    # Purchase Order Template
    "po_standard": TemplateMetaData(
        id="po_standard",
        category=ProcurementDocType.PURCHASE_ORDER,
        title="Standard Authorized Purchase Order",
        description="Official financial authorization document for goods and service delivery.",
        tone="Formal & Transactional",
        tone_description="Binding financial commitment document with itemized billing details.",
        icon="🧾",
        section_ids=[
            "po_header",
            "po_line_items",
            "po_payment_delivery",
        ],
        expansion_tags=[],
    ),

    # Custom Template Builder
    "custom_template": TemplateMetaData(
        id="custom_template",
        category=ProcurementDocType.RFP,
        title="Custom Template Builder",
        description="Design your own custom section layout, guidance rules, and document structure.",
        tone="Custom User Defined",
        tone_description="User tailored section outlines and guidance.",
        icon="🎨",
        section_ids=["custom_section"],
        expansion_tags=[],
    ),
}


# ============================================================================
# EXPANSION POOLS (Per Document Type)
# ============================================================================

EXPANSION_SECTIONS_PER_DOC_TYPE: dict[ProcurementDocType, list[str]] = {
    ProcurementDocType.RFP: [
        "technical_architecture",
        "functional_specs",
        "cost_breakdown",
        "payment_schedule",
        "sla_uptime",
        "data_security",
        "qa_testing",
        "training_handover",
        "formal_execution",
    ],
    ProcurementDocType.SOW: [
        "technical_architecture",
        "milestones_wbs",
        "payment_schedule",
        "qa_testing",
        "project_governance",
        "change_control",
        "confidentiality",
        "ip_rights",
        "formal_execution",
    ],
    ProcurementDocType.RFQ: [
        "cost_breakdown",
        "payment_schedule",
        "delivery_fulfillment",
        "warranties",
        "statutory_compliance",
        "formal_execution",
    ],
    ProcurementDocType.VENDOR_CONTRACT: [
        "scope_boundaries",
        "cost_breakdown",
        "payment_schedule",
        "sla_uptime",
        "data_security",
        "indemnification",
        "termination",
        "legal_jurisdiction",
        "formal_execution",
    ],
    ProcurementDocType.RFI: [
        "technical_architecture",
        "data_security",
        "business_continuity",
        "vendor_evaluation",
    ],
    ProcurementDocType.PURCHASE_ORDER: [
        "cost_breakdown",
        "payment_schedule",
        "statutory_compliance",
        "formal_execution",
    ],
    ProcurementDocType.VENDOR_SCORECARD: [
        "vendor_quality",
        "vendor_commercial",
        "vendor_improvement",
        "stakeholder_signatures",
    ],
}

PROCUREMENT_TEMPLATES: dict[ProcurementDocType, list[SectionSchema]] = {
    doc_type: [
        tmpl.sections for tmpl in PREBUILT_TEMPLATES.values() if tmpl.category == doc_type
    ][0]
    for doc_type in ProcurementDocType
}

# Compatibility reference for legacy master list
MASTER_PROCUREMENT_TAXONOMY: list[SectionSchema] = [
    sec for sec in SECTION_REGISTRY.values() if "master" in sec.tags
]


# ============================================================================
# MAIN API FUNCTIONS
# ============================================================================

def get_template_by_id(template_id: str) -> TemplateMetaData:
    """Retrieve a template by ID, falling back to rfp_enterprise."""
    return PREBUILT_TEMPLATES.get(template_id, PREBUILT_TEMPLATES["rfp_enterprise"])


def get_procurement_sections(
    doc_type: ProcurementDocType,
    template_id: str | None = None,
    num_pages: int | None = None,
) -> list[SectionSchema]:
    """
    Get sections for a procurement document with ID-based deduplication and page expansion.
    Returns list[SectionSchema] for complete downstream compatibility.
    """
    if template_id and template_id in PREBUILT_TEMPLATES:
        base_sections = list(PREBUILT_TEMPLATES[template_id].sections)
    else:
        base_sections = list(PROCUREMENT_TEMPLATES.get(doc_type, PROCUREMENT_TEMPLATES[ProcurementDocType.RFP]))

    if not num_pages or num_pages == len(base_sections):
        return base_sections

    if num_pages < len(base_sections):
        return base_sections[:max(1, num_pages)]

    used_ids: set[str] = {s.section_id for s in base_sections if s.section_id}
    used_titles: set[str] = {s.title.lower() for s in base_sections}
    result_sections: list[SectionSchema] = list(base_sections)

    # 1. Expand from doc-type specific expansion pool
    expansion_ids = EXPANSION_SECTIONS_PER_DOC_TYPE.get(doc_type, EXPANSION_SECTIONS_PER_DOC_TYPE[ProcurementDocType.RFP])
    for sid in expansion_ids:
        if len(result_sections) >= num_pages:
            break
        if sid in SECTION_REGISTRY and sid not in used_ids:
            sec = SECTION_REGISTRY[sid]
            if sec.title.lower() not in used_titles:
                result_sections.append(sec)
                used_ids.add(sid)
                used_titles.add(sec.title.lower())

    # 2. Expand from master taxonomy if target page count is higher (e.g. 15-35 pages)
    if len(result_sections) < num_pages:
        for sec in MASTER_PROCUREMENT_TAXONOMY:
            if len(result_sections) >= num_pages:
                break
            if sec.section_id and sec.section_id in used_ids:
                continue
            if sec.title.lower() in used_titles:
                continue
            result_sections.append(sec)
            if sec.section_id:
                used_ids.add(sec.section_id)
            used_titles.add(sec.title.lower())

    return result_sections
