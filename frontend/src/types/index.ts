export type LLMProvider = "openai" | "gemini" | "anthropic";

export type ProcurementDocType =
  | "RFP"
  | "RFQ"
  | "RFI"
  | "PURCHASE_ORDER"
  | "VENDOR_CONTRACT"
  | "SOW"
  | "VENDOR_SCORECARD";

export const PROVIDER_LABELS: Record<LLMProvider, string> = {
  openai: "OpenAI",
  gemini: "Google Gemini",
  anthropic: "Anthropic",
};

export const PROCUREMENT_DOC_LABELS: Record<ProcurementDocType, string> = {
  RFP: "Request for Proposal (RFP)",
  RFQ: "Request for Quotation (RFQ)",
  RFI: "Request for Information (RFI)",
  PURCHASE_ORDER: "Purchase Order (PO)",
  VENDOR_CONTRACT: "Vendor Contract",
  SOW: "Statement of Work (SOW)",
  VENDOR_SCORECARD: "Vendor Evaluation Scorecard",
};

export interface SectionGuidance {
  title: string;
  section_type: "prose" | "line_items" | "payment_schedule" | "clause";
  guidance: string;
}

export interface TemplateDefinition {
  id: string;
  category: ProcurementDocType | "ALL" | "CUSTOM";
  title: string;
  description: string;
  tone: string;
  toneDescription: string;
  icon: string;
  sections: SectionGuidance[];
}

export const PREBUILT_TEMPLATES_LIST: TemplateDefinition[] = [
  // RFP
  {
    id: "rfp_enterprise",
    category: "RFP",
    title: "Standard Enterprise RFP",
    description: "Comprehensive evaluation format for corporate software, services, and vendor selection.",
    tone: "Formal & Evaluative",
    toneDescription: "Professional, analytical, clear criteria with structured submission guidelines.",
    icon: "🏢",
    sections: [
      { title: "Scope of Work", section_type: "prose", guidance: "Detailed technical and operational requirements." },
      { title: "Eligibility Criteria", section_type: "prose", guidance: "Vendor qualifications, certifications, and financial stability." },
      { title: "Submission Instructions", section_type: "prose", guidance: "Format requirements, submission deadline, contact point." },
      { title: "Evaluation Criteria", section_type: "prose", guidance: "Scoring breakdown (Technical 40%, Cost 40%, Experience 20%)." },
      { title: "Project Timeline", section_type: "prose", guidance: "Key procurement milestones." },
      { title: "Terms & Conditions", section_type: "clause", guidance: "Standard procurement terms, confidentiality, governing law." },
    ],
  },
  {
    id: "rfp_gov",
    category: "RFP",
    title: "Government & Public Compliance RFP",
    description: "Strict audit-compliant structure for public sector, municipal, or regulated tenders.",
    tone: "Strict & Regulatory",
    toneDescription: "Formal, precise legalistic phrasing adhering to statutory procurement mandates.",
    icon: "GOV",
    sections: [
      { title: "Executive Summary & Purpose", section_type: "prose", guidance: "Public interest scope and statutory mandate." },
      { title: "Mandatory Compliance & Certifications", section_type: "clause", guidance: "Regulatory compliance and security clearances." },
      { title: "Technical Specifications & Deliverables", section_type: "prose", guidance: "Rigid technical baseline and mandatory standards." },
      { title: "Proposal Costing Structure", section_type: "line_items", guidance: "Itemized transparent cost breakdown for audit." },
      { title: "Weighted Scoring Matrix", section_type: "prose", guidance: "Publicly disclosed scoring formula." },
      { title: "Statutory Terms & Conditions", section_type: "clause", guidance: "Public procurement provisions and FOIA clauses." },
    ],
  },
  {
    id: "rfp_tech",
    category: "RFP",
    title: "IT & SaaS Systems RFP",
    description: "Focused on cloud architecture, API integrations, SLA guarantees, and data security.",
    tone: "Technical & Rigorous",
    toneDescription: "In-depth, engineering-focused tone querying system specs and security controls.",
    icon: "TECH",
    sections: [
      { title: "System Architecture & Scope", section_type: "prose", guidance: "Target architecture, cloud deployment, integrations." },
      { title: "Data Security & Privacy", section_type: "clause", guidance: "SOC2 Type II, GDPR/CCPA, encryption standards." },
      { title: "SLA & Support Framework", section_type: "prose", guidance: "Uptime targets (99.9%), incident response tiers." },
      { title: "Vendor Technical Qualifications", section_type: "prose", guidance: "Engineering team pedigree and customer references." },
      { title: "Licensing & Commercial Model", section_type: "line_items", guidance: "Subscription tiers, user seats, API calls." },
    ],
  },
  // RFQ
  {
    id: "rfq_goods",
    category: "RFQ",
    title: "Commercial Goods & Hardware RFQ",
    description: "Itemized quotation format for physical goods, hardware, and raw materials.",
    tone: "Transactional & Precise",
    toneDescription: "Direct, concise, focused on exact item numbers, lead times, and unit costs.",
    icon: "RFQ",
    sections: [
      { title: "Vendor & Requisition Info", section_type: "prose", guidance: "RFQ reference number and buyer details." },
      { title: "Itemized Quotation Table", section_type: "line_items", guidance: "SKU codes, descriptions, quantities, unit prices, tax." },
      { title: "Delivery & Fulfillment Terms", section_type: "prose", guidance: "Incoterms (FOB/DDP), shipping destination, lead times." },
      { title: "Commercial Payment Terms", section_type: "clause", guidance: "Standard payment terms (Net 30/60) and currency." },
    ],
  },
  {
    id: "rfq_services",
    category: "RFQ",
    title: "Professional Services Rate Card RFQ",
    description: "Pricing solicitation for consulting, engineering hours, or staff augmentation.",
    tone: "Commercial & Structured",
    toneDescription: "Professional rate-card orientation for comparing labor categories.",
    icon: "RATE",
    sections: [
      { title: "Service Scope Overview", section_type: "prose", guidance: "Summary of requested professional labor categories." },
      { title: "Hourly Rate Card Breakdown", section_type: "line_items", guidance: "Labor roles (Junior/Senior/Architect), billing rates." },
      { title: "Travel & Expense Policy", section_type: "clause", guidance: "Reimbursement bounds and pre-approval rules." },
      { title: "Validity & Payment Terms", section_type: "clause", guidance: "Rate lock duration and invoicing cadence." },
    ],
  },
  // RFI
  {
    id: "rfi_market",
    category: "RFI",
    title: "Market Capabilities RFI",
    description: "Exploratory inquiry to research industry solutions and vendor product roadmaps.",
    tone: "Exploratory & Open",
    toneDescription: "Inquisitive, non-binding tone encouraging vendors to showcase innovations.",
    icon: "RFI",
    sections: [
      { title: "Problem Statement & Background", section_type: "prose", guidance: "Business challenge driving market inquiry." },
      { title: "Vendor Organization & Overview", section_type: "prose", guidance: "Company footprint, ownership, and core offerings." },
      { title: "Solution Capabilities & Features", section_type: "prose", guidance: "Open-ended questions on key differentiators." },
      { title: "Indicative Pricing Models", section_type: "prose", guidance: "High-level commercial models without binding quotes." },
    ],
  },
  {
    id: "rfi_security",
    category: "RFI",
    title: "Cybersecurity Risk RFI",
    description: "Targeted risk assessment questionnaire for third-party software vendors.",
    tone: "Analytical & Risk-Conscious",
    toneDescription: "Probing, security-focused queries examining data protection and resilience.",
    icon: "SEC",
    sections: [
      { title: "Security Governance & Compliance", section_type: "prose", guidance: "ISO 27001, SOC 2, and audit frequency." },
      { title: "Data Protection & Encryption", section_type: "prose", guidance: "Encryption standards, key management, tenant isolation." },
      { title: "Continuity & Incident Response", section_type: "prose", guidance: "RTO/RPO metrics, disaster recovery plans, SLAs." },
    ],
  },
  // SOW
  {
    id: "sow_agile",
    category: "SOW",
    title: "Agile Software Development SOW",
    description: "Iterative project contract with sprint goals, team rosters, and milestone deliverables.",
    tone: "Operational & Collaborative",
    toneDescription: "Clear, milestone-driven, defining team cadence and sprint acceptance criteria.",
    icon: "SOW",
    sections: [
      { title: "Project Vision & Objectives", section_type: "prose", guidance: "Target product features and business outcomes." },
      { title: "Sprint Cadence & Scope", section_type: "prose", guidance: "Sprint length (2 weeks) and backlog management." },
      { title: "Team Roster & Roles", section_type: "prose", guidance: "Client vs Vendor staff allocation." },
      { title: "Milestone Payment Schedule", section_type: "payment_schedule", guidance: "Sprint milestone release payments." },
      { title: "Acceptance Criteria & Change Control", section_type: "clause", guidance: "Definition of Done and scope change process." },
    ],
  },
  {
    id: "sow_managed",
    category: "SOW",
    title: "Managed Infrastructure Services SOW",
    description: "Long-term IT maintenance, cloud infrastructure management, and technical support SOW.",
    tone: "Formal & SLA-Oriented",
    toneDescription: "Definitive, operational tone centered around uptime guarantees and support response.",
    icon: "OPS",
    sections: [
      { title: "Managed Environment Scope", section_type: "prose", guidance: "Inventory of managed servers, cloud accounts, databases." },
      { title: "SLA Performance & Ticket Resolution", section_type: "prose", guidance: "Incident response times and uptime guarantees." },
      { title: "Routine Maintenance & Backups", section_type: "prose", guidance: "Patching windows and backup schedules." },
      { title: "Monthly Service Fees", section_type: "payment_schedule", guidance: "Fixed monthly retainer fees and billing." },
    ],
  },
  // Contract
  {
    id: "contract_msa",
    category: "VENDOR_CONTRACT",
    title: "Master Services Agreement (MSA)",
    description: "Comprehensive legal framework contract governing overall vendor engagement.",
    tone: "Legalistic & Binding",
    toneDescription: "Formal legal prose with robust risk allocation, indemnity, and IP rights.",
    icon: "MSA",
    sections: [
      { title: "Preamble & Purpose", section_type: "prose", guidance: "Effective date, legal entities, background context." },
      { title: "Services & Statements of Work", section_type: "prose", guidance: "Framework for issuing individual SOWs." },
      { title: "Intellectual Property Rights", section_type: "clause", guidance: "Work Product ownership and IP provisions." },
      { title: "Indemnification & Liability Limits", section_type: "clause", guidance: "Liability caps, direct vs consequential damages." },
      { title: "Term & Termination", section_type: "clause", guidance: "Duration, 30-day notice, cause termination." },
    ],
  },
  {
    id: "contract_nda",
    category: "VENDOR_CONTRACT",
    title: "Mutual Non-Disclosure Agreement",
    description: "Standard bilateral confidentiality agreement for commercial discussions.",
    tone: "Protective & Precise",
    toneDescription: "Strict legal definitions governing confidential trade secrets and data.",
    icon: "🔒",
    sections: [
      { title: "Definition of Confidential Info", section_type: "clause", guidance: "Protected info scope and exclusions." },
      { title: "Obligations & Standard of Care", section_type: "clause", guidance: "Duty to protect, no reverse engineering." },
      { title: "Term & Return of Materials", section_type: "clause", guidance: "Duration (3 years) and destruction protocols." },
    ],
  },
  // Scorecard / PO
  {
    id: "scorecard_kpi",
    category: "VENDOR_SCORECARD",
    title: "Quarterly Vendor KPI Scorecard",
    description: "Structured performance assessment matrix for vendor reviews.",
    tone: "Objective & Analytical",
    toneDescription: "Metric-driven rating format comparing SLA metrics to baseline targets.",
    icon: "📈",
    sections: [
      { title: "Vendor Summary & Evaluation Period", section_type: "prose", guidance: "Vendor profile, contract reference, evaluation quarter." },
      { title: "Quality & SLA Metrics Breakdown", section_type: "prose", guidance: "Scored deliverable accuracy and defect rate." },
      { title: "Commercial & Relationship Rating", section_type: "prose", guidance: "Invoicing transparency and account responsiveness." },
      { title: "Final Tier Rating & Action Plan", section_type: "prose", guidance: "Weighted score, vendor tier, and renewal plan." },
    ],
  },
  {
    id: "po_standard",
    category: "PURCHASE_ORDER",
    title: "Standard Authorized Purchase Order",
    description: "Official financial authorization document for goods and service delivery.",
    tone: "Formal & Transactional",
    toneDescription: "Binding financial commitment document with itemized billing details.",
    icon: "🧾",
    sections: [
      { title: "Header & Party Details", section_type: "prose", guidance: "PO Number, Buyer details, Billing/Shipping Address." },
      { title: "Authorized Line Items", section_type: "line_items", guidance: "Item descriptions, quantities, unit prices, subtotal." },
      { title: "Payment & Delivery Instructions", section_type: "payment_schedule", guidance: "Payment terms (Net 30) and shipping instructions." },
    ],
  },
  // Custom
  {
    id: "custom_template",
    category: "CUSTOM",
    title: "Custom Template Builder",
    description: "Build your own custom section layout, guidance rules, and document structure.",
    tone: "Custom User Defined",
    toneDescription: "Tailored section titles and customized guidance instructions.",
    icon: "🎨",
    sections: [
      { title: "Custom Section 1", section_type: "prose", guidance: "User defined section guidance." },
    ],
  },
];

export interface SessionResponse {
  session_id: string;
  provider: LLMProvider;
  model: string;
}

export interface KnowledgeFileSummary {
  filename: string;
  chunk_count: number;
}

export interface KnowledgeUploadResponse {
  kb_id: string;
  files: KnowledgeFileSummary[];
  total_chunks: number;
}

export interface DocumentSegment {
  segment_id: string;
  name: string;
  segment_type: "text" | "table" | "signature_block";
  content: Record<string, unknown>;
  compliance_flag?: boolean;
  compliance_note?: string;
}

export interface DocumentStyleConfig {
  fontFamily: string;
  fontSize: string;
  accentColor: string;
  theme?: string;
  formatStyle?: "modern" | "elegant" | "shaded" | "lines" | "centered";
  colorPalette?: string;
  fontPairing?: string;
  paragraphSpacing?: string;
  watermark?: string;
  pageColor?: string;
  pageBorder?: string;
  showPageNumbers?: boolean;
  pageNumberPosition?: "bottom-right" | "bottom-center" | "bottom-left" | "top-right" | "none";
  showHeaderFooter?: boolean;
  headerText?: string;
}

export interface ChatMessage {
  id: string;
  sender: "user" | "assistant" | "system";
  text: string;
  timestamp: string;
  segment_id?: string;
}

export interface GenerateResponse {
  status: "collecting" | "ready" | "chat_reply";
  document_id: string;
  pending_question?: string;
  chat_reply?: string;
  session_id?: string;
  missing_fields?: string[];
  segments?: DocumentSegment[];
  style_config?: DocumentStyleConfig;
  page_layout_size?: PageLayoutSize;
  lexical_state?: Record<string, unknown>;
  page_titles?: string[];
  research_findings?: Array<{
    finding_id: string;
    statement: string;
    extracted_quote?: string;
    source_title?: string;
    source_url?: string;
    publication_date?: string;
    reliability_score?: number;
  }>;
  audit_report?: {
    status?: "APPROVED" | "REJECTED";
    conflicts?: string[];
    citations_mapped?: string[];
    audit_notes?: string;
  };
  document_audit_report?: {
    score?: number;
    passed?: boolean;
    critical_defects?: string[];
    warnings?: string[];
    recommendations?: string[];
  };
  sandbox_computations?: Record<string, unknown>;
}

export type StreamEvent =
  | { type: "agent_thought"; step: string; status: "running" | "completed" }
  | { type: "tool_execution"; tool_name: string; input: Record<string, unknown>; output?: string }
  | { type: "canvas_patch"; operation: "insert_node" | "replace_range" | "append"; target_id?: string; content: any }
  | {
      type: "checkpoint";
      version_id: string;
      timestamp: number;
      document_id?: string;
      segments?: DocumentSegment[];
      page_titles?: string[];
      style_config?: DocumentStyleConfig;
      page_layout_size?: PageLayoutSize;
      missing_fields?: string[];
    };

export interface DocumentCheckpoint {
  version_id: string;
  timestamp: number;
  label: string;
  segments: DocumentSegment[];
  lexical_state?: Record<string, unknown>;
  trigger: "generation" | "user_typing" | "inline_ai" | "manual";
}

export interface TargetedEditParams {
  prompt: string;
  target_node_id: string;
  selection_text: string;
  context_window: string;
}

export interface GuidedParameters {
  buyer_name?: string;
  vendor_name?: string;
  budget_estimate?: string;
  delivery_timeline?: string;
  compliance_frameworks?: string[];
  primary_tech?: string;
  sla_target?: string;
}

export interface PreflightSectionOutline {
  index: number;
  title: string;
  section_type: string;
  guidance: string;
}

export interface PreflightBlueprintResponse {
  recommended_template_id: string;
  recommended_doc_type: ProcurementDocType;
  template_title: string;
  template_icon: string;
  confidence_score: number;
  match_reason: string;
  recommended_num_pages: number;
  guided_params: GuidedParameters;
  outline_sections: PreflightSectionOutline[];
  detected_keywords: string[];
}

export type PageLayoutSize = "A4" | "LETTER" | "A3" | "LEGAL";

export type WizardStep = "api-key" | "templates" | "prompt-intake" | "generating" | "editor";

export interface SavedSession {
  _id: string;
  idNumber: number;
  displayId: string;
  sessionId: string;
  documentId: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  provider: LLMProvider | null;
  model: string | null;
  kbId: string | null;
  kbFiles: KnowledgeFileSummary[];
  procurementDocType: ProcurementDocType;
  prompt: string;
  segments: DocumentSegment[];
  promptLog: ChatMessage[];
  styleConfig: DocumentStyleConfig;
  pageLayoutSize: PageLayoutSize;
  docStatus: string;
}
