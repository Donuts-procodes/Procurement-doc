import { useState } from "react";
import { createPortal } from "react-dom";
import { uploadKnowledgeFiles, fetchPreflightBlueprint } from "../../api/client";
import { useWizardStore } from "../../state/wizardStore";
import {
  PREBUILT_TEMPLATES_LIST,
  type GuidedParameters,
  type PageLayoutSize,
  type PreflightBlueprintResponse,
  type ProcurementDocType,
  type TemplateDefinition,
} from "../../types";

const CATEGORY_TABS: { id: string; label: string }[] = [
  { id: "ALL", label: "All Templates" },
  { id: "RFP", label: "RFP" },
  { id: "RFQ", label: "RFQ" },
  { id: "RFI", label: "RFI" },
  { id: "SOW", label: "SOW" },
  { id: "VENDOR_CONTRACT", label: "Contracts" },
  { id: "VENDOR_SCORECARD", label: "Scorecards & PO" },
  { id: "CUSTOM", label: "Custom Builder" },
];

const COMPLIANCE_OPTIONS = ["SOC 2", "ISO 27001", "GDPR", "HIPAA", "PCI-DSS", "FedRAMP"];
const SLA_OPTIONS = ["99.9% (Standard)", "99.95% (High)", "99.99% (Mission Critical)"];

export function StepTemplateConfig() {
  const storeProcurementDocType = useWizardStore((s) => s.procurementDocType);
  const storeTemplateId = useWizardStore((s) => s.templateId);
  const storeNumPages = useWizardStore((s) => s.numPages);
  const storePrompt = useWizardStore((s) => s.prompt);
  const storeGuidedParams = useWizardStore((s) => s.guidedParams);
  const sessionId = useWizardStore((s) => s.sessionId);
  const kbId = useWizardStore((s) => s.kbId);
  const setSession = useWizardStore((s) => s.setSession);
  const setTemplateConfig = useWizardStore((s) => s.setTemplateConfig);
  const setKnowledgeBase = useWizardStore((s) => s.setKnowledgeBase);
  const kbFiles = useWizardStore((s) => s.kbFiles);
  const pageLayoutSize = useWizardStore((s) => s.pageLayoutSize);
  const setPageLayoutSize = useWizardStore((s) => s.setPageLayoutSize);
  const setError = useWizardStore((s) => s.setError);
  const error = useWizardStore((s) => s.error);
  const isDarkMode = useWizardStore((s) => s.isDarkMode);

  const [uploadingRef, setUploadingRef] = useState(false);
  const [referenceFiles, setReferenceFiles] = useState<Array<{ name: string; size: number }>>(
    kbFiles.map((f) => ({ name: f.filename, size: 0 }))
  );

  const storeContentDensity = useWizardStore((s) => s.contentDensity);
  const [activeTab, setActiveTab] = useState<string>("ALL");
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>(storeTemplateId || "rfp_enterprise");
  const [procurementDocType, setProcurementDocType] = useState<ProcurementDocType>(storeProcurementDocType || "RFP");
  const [numPages, setNumPages] = useState(storeNumPages || 5);
  const [prompt, setPrompt] = useState(storePrompt || "");
  const [contentDensity, setContentDensity] = useState<"min" | "med" | "max">(storeContentDensity || "med");
  const [previewTemplate, setPreviewTemplate] = useState<TemplateDefinition | null>(null);

  // GenSpark Blueprint State
  const [analyzingBlueprint, setAnalyzingBlueprint] = useState(false);
  const [blueprint, setBlueprint] = useState<PreflightBlueprintResponse | null>(null);
  const [showAdvancedManualConfig, setShowAdvancedManualConfig] = useState(false);

  // Guided Procurement Parameters State
  const [guidedOpen, setGuidedOpen] = useState(true);
  const [buyerName, setBuyerName] = useState(storeGuidedParams?.buyer_name || "");
  const [vendorName, setVendorName] = useState(storeGuidedParams?.vendor_name || "");
  const [budgetEstimate, setBudgetEstimate] = useState(storeGuidedParams?.budget_estimate || "");
  const [deliveryTimeline, setDeliveryTimeline] = useState(storeGuidedParams?.delivery_timeline || "");
  const [primaryTech, setPrimaryTech] = useState(storeGuidedParams?.primary_tech || "");
  const [complianceFrameworks, setComplianceFrameworks] = useState<string[]>(
    storeGuidedParams?.compliance_frameworks || []
  );
  const [slaTarget, setSlaTarget] = useState(storeGuidedParams?.sla_target || "99.9% (Standard)");

  const filteredTemplates = PREBUILT_TEMPLATES_LIST.filter((t) => {
    if (activeTab === "ALL") return true;
    if (activeTab === "CUSTOM") return t.category === "CUSTOM";
    if (activeTab === "VENDOR_SCORECARD") return t.category === "VENDOR_SCORECARD" || t.category === "PURCHASE_ORDER";
    return t.category === activeTab;
  });

  const selectedTemplate = PREBUILT_TEMPLATES_LIST.find((t) => t.id === selectedTemplateId) || PREBUILT_TEMPLATES_LIST[0];

  function handleSelectTemplate(tmpl: TemplateDefinition) {
    setSelectedTemplateId(tmpl.id);
    if (tmpl.category !== "ALL" && tmpl.category !== "CUSTOM") {
      setProcurementDocType(tmpl.category as ProcurementDocType);
      useWizardStore.setState({ procurementDocType: tmpl.category as ProcurementDocType });
    }
    useWizardStore.setState({ templateId: tmpl.id });
  }

  async function handleAutoBlueprint(overridePrompt?: string, overrideKbId?: string) {
    const activePrompt = overridePrompt ?? prompt;
    const activeKbId = overrideKbId ?? kbId;

    if (!activePrompt.trim() && !activeKbId && (!kbFiles || kbFiles.length === 0)) {
      setError("Please provide procurement requirements or attach a reference document to auto-detect the blueprint.");
      return;
    }

    setAnalyzingBlueprint(true);
    setError(null);
    try {
      const res = await fetchPreflightBlueprint({
        prompt: activePrompt.trim() || "Analyze project requirements and configure procurement blueprint",
        kb_id: activeKbId || undefined,
        current_template_id: selectedTemplateId,
        current_doc_type: procurementDocType,
        session_id: sessionId || undefined,
      });

      setBlueprint(res);
      setSelectedTemplateId(res.recommended_template_id);
      setProcurementDocType(res.recommended_doc_type);
      setNumPages(res.recommended_num_pages);
      setActiveTab(res.recommended_doc_type);

      if (res.guided_params.buyer_name) setBuyerName(res.guided_params.buyer_name);
      if (res.guided_params.vendor_name) setVendorName(res.guided_params.vendor_name);
      if (res.guided_params.budget_estimate) setBudgetEstimate(res.guided_params.budget_estimate);
      if (res.guided_params.delivery_timeline) setDeliveryTimeline(res.guided_params.delivery_timeline);
      if (res.guided_params.primary_tech) setPrimaryTech(res.guided_params.primary_tech);
      if (res.guided_params.compliance_frameworks && res.guided_params.compliance_frameworks.length > 0) {
        setComplianceFrameworks(res.guided_params.compliance_frameworks);
      }
      if (res.guided_params.sla_target) setSlaTarget(res.guided_params.sla_target);

      // Store sync
      useWizardStore.setState({
        templateId: res.recommended_template_id,
        procurementDocType: res.recommended_doc_type,
        numPages: res.recommended_num_pages,
        guidedParams: {
          buyer_name: res.guided_params.buyer_name,
          vendor_name: res.guided_params.vendor_name,
          budget_estimate: res.guided_params.budget_estimate,
          delivery_timeline: res.guided_params.delivery_timeline,
          primary_tech: res.guided_params.primary_tech,
          compliance_frameworks: res.guided_params.compliance_frameworks,
          sla_target: res.guided_params.sla_target,
        },
      });
    } catch (err: any) {
      setError("Failed to formulate pre-flight blueprint: " + (err.message || "Unknown error"));
    } finally {
      setAnalyzingBlueprint(false);
    }
  }

  async function handleReferenceUpload(files: FileList | null) {
    if (!files || files.length === 0) return;
    const newFiles = Array.from(files);
    setUploadingRef(true);
    setError(null);
    try {
      const res = await uploadKnowledgeFiles(newFiles, kbId || undefined);
      setKnowledgeBase(res.kb_id, res.files);
      setReferenceFiles((prev) => {
        const existingNames = new Set(prev.map((f) => f.name));
        const additions = newFiles
          .filter((f) => !existingNames.has(f.name))
          .map((f) => ({ name: f.name, size: f.size }));
        return [...prev, ...additions];
      });
      // GenSpark behavior: Immediately auto-detect blueprint using newly uploaded reference documents
      const allNames = [...referenceFiles.map((f) => f.name), ...newFiles.map((f) => f.name)].join(", ");
      await handleAutoBlueprint(prompt || `Analyze reference documents (${allNames})`, res.kb_id);
    } catch (e: any) {
      setError("Failed to upload reference template(s): " + (e.message || "Upload error"));
    } finally {
      setUploadingRef(false);
    }
  }

  function handleRemoveReferenceFile(fileName: string) {
    setReferenceFiles((prev) => {
      const next = prev.filter((f) => f.name !== fileName);
      if (next.length === 0) {
        setKnowledgeBase("", []);
      }
      return next;
    });
  }

  function handleClearAllReferences() {
    setReferenceFiles([]);
    setKnowledgeBase("", []);
  }

  function toggleCompliance(fw: string) {
    setComplianceFrameworks((prev) =>
      prev.includes(fw) ? prev.filter((item) => item !== fw) : [...prev, fw]
    );
  }

  function handleSubmit() {
    if (prompt.trim().length < 1) {
      setError("Describe what the procurement document should be about.");
      return;
    }

    if (!sessionId) {
      const fallbackSessionId = `session_${Date.now()}`;
      setSession("openai", "gpt-4o", fallbackSessionId);
    }

    const guided: GuidedParameters = {
      buyer_name: buyerName.trim() || undefined,
      vendor_name: vendorName.trim() || undefined,
      budget_estimate: budgetEstimate.trim() || undefined,
      delivery_timeline: deliveryTimeline.trim() || undefined,
      primary_tech: primaryTech.trim() || undefined,
      compliance_frameworks: complianceFrameworks.length > 0 ? complianceFrameworks : undefined,
      sla_target: slaTarget || undefined,
    };

    useWizardStore.setState({ templateId: selectedTemplateId });
    setTemplateConfig(procurementDocType, numPages, prompt.trim(), contentDensity, guided);
  }

  return (
    <div className="wizard-step" style={{ maxWidth: "100%" }}>
      <h2>Configure Procurement Document & Template</h2>
      <p className="wizard-step__subtitle">
        GenSpark-style autonomous planning: Auto-detect the optimal template, outline, and 7 key parameters beforehand, or manually customize below.
      </p>

      {/* 1. Intake Section: Prompt & Reference File */}
      <div
        style={{
          padding: "16px",
          borderRadius: "12px",
          background: isDarkMode ? "rgba(15, 23, 42, 0.7)" : "#ffffff",
          border: isDarkMode ? "1px solid rgba(255,255,255,0.12)" : "1px solid #e2e8f0",
          boxShadow: isDarkMode ? "0 4px 20px rgba(0,0,0,0.25)" : "0 4px 20px rgba(0,0,0,0.05)",
          marginBottom: "20px",
        }}
      >
        <label className="field" style={{ marginBottom: "14px" }}>
          <span style={{ fontWeight: 700, fontSize: "13px", color: isDarkMode ? "#f8fafc" : "#0f172a" }}>
            1. Procurement Details & Project Scope
          </span>
          <textarea
            rows={3}
            value={prompt}
            onChange={(e) => {
              const val = e.target.value;
              setPrompt(val);
              useWizardStore.setState({ prompt: val });
            }}
            placeholder="e.g. SEG AI Project Command Centre - Architecture & Client Proposal V4. Draft cloud RFP for AWS, React, Python FastAPI with SOC 2, HIPAA, and 99.99% SLA. Budget $250,000 timeline 6 months."
            style={{ marginTop: "6px" }}
          />
        </label>

        {/* Reference File Upload */}
        <div
          style={{
            padding: "12px 14px",
            borderRadius: "8px",
            background: isDarkMode ? "rgba(255,255,255,0.03)" : "#f8fafc",
            border: isDarkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid #e2e8f0",
            marginBottom: "16px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
            <span style={{ fontWeight: 600, fontSize: "12px", color: isDarkMode ? "#cbd5e1" : "#334155" }}>
              Attach Reference Document / Tender File (Optional)
            </span>
            <span style={{ fontSize: "11px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
              PDF, DOCX, TXT, MD
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {referenceFiles.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", alignItems: "center" }}>
                {referenceFiles.map((file) => (
                  <div
                    key={file.name}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "8px",
                      padding: "4px 10px",
                      borderRadius: "6px",
                      background: isDarkMode ? "rgba(59, 130, 246, 0.15)" : "#eff6ff",
                      border: isDarkMode ? "1px solid #3b82f6" : "1px solid #93c5fd",
                    }}
                  >
                    <span style={{ fontSize: "9px", fontWeight: 800, padding: "1px 5px", borderRadius: "3px", background: isDarkMode ? "#3b82f6" : "#1a73e8", color: "#ffffff" }}>
                      REF FILE
                    </span>
                    <span style={{ fontWeight: 600, fontSize: "12px", color: isDarkMode ? "#f8fafc" : "#1e293b", maxWidth: "220px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {file.name}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveReferenceFile(file.name)}
                      title={`Remove ${file.name}`}
                      style={{
                        background: "none",
                        border: "none",
                        color: isDarkMode ? "#f87171" : "#dc2626",
                        fontWeight: 700,
                        fontSize: "13px",
                        cursor: "pointer",
                        padding: "0 2px",
                        lineHeight: 1,
                      }}
                    >
                      ✕
                    </button>
                  </div>
                ))}
                {referenceFiles.length > 1 && (
                  <button
                    type="button"
                    onClick={handleClearAllReferences}
                    style={{
                      background: "none",
                      border: "none",
                      color: isDarkMode ? "#94a3b8" : "#64748b",
                      fontSize: "11px",
                      textDecoration: "underline",
                      cursor: "pointer",
                    }}
                  >
                    Clear All ({referenceFiles.length})
                  </button>
                )}
              </div>
            )}

            <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
              <input
                type="file"
                id="custom-ref-upload"
                multiple
                accept=".pdf,.docx,.txt,.md,.json"
                onChange={(e) => {
                  handleReferenceUpload(e.target.files);
                  e.target.value = "";
                }}
                style={{ display: "none" }}
              />
              <label
                htmlFor="custom-ref-upload"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 14px",
                  borderRadius: "6px",
                  background: isDarkMode ? "rgba(255,255,255,0.08)" : "#ffffff",
                  border: isDarkMode ? "1px solid rgba(255,255,255,0.2)" : "1px solid #cbd5e1",
                  color: isDarkMode ? "#f8fafc" : "#1e293b",
                  fontWeight: 600,
                  fontSize: "12px",
                  cursor: "pointer",
                }}
              >
                {uploadingRef ? "Uploading Files..." : referenceFiles.length > 0 ? "+ Attach More Tender Files" : "+ Attach Tender File(s)"}
              </label>
              <span style={{ fontSize: "11px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
                {uploadingRef ? "Parsing text & indexing clauses into RAG knowledge base..." : "Upload one or multiple tender PDFs/DOCX/TXT to auto-extract parameters"}
              </span>
            </div>
          </div>
        </div>

        {/* GenSpark Auto-Pilot Trigger Button */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: "12px", fontWeight: 700, color: isDarkMode ? "#60a5fa" : "#1a73e8", display: "flex", alignItems: "center", gap: "6px" }}>
              <span>✨ GenSpark Autonomous Pre-Flight Agent</span>
            </div>
            <div style={{ fontSize: "11px", color: isDarkMode ? "#94a3b8" : "#64748b", marginTop: "2px" }}>
              Evaluates requirements to auto-select template, page count, and 7 guided parameters beforehand.
            </div>
          </div>

          <button
            type="button"
            onClick={() => handleAutoBlueprint()}
            disabled={analyzingBlueprint}
            style={{
              padding: "10px 20px",
              borderRadius: "8px",
              border: "none",
              background: "linear-gradient(135deg, #2563eb, #7c3aed)",
              color: "#ffffff",
              fontSize: "13px",
              fontWeight: 700,
              cursor: analyzingBlueprint ? "wait" : "pointer",
              boxShadow: "0 4px 14px rgba(99, 102, 241, 0.35)",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              transition: "all 0.2s ease",
            }}
          >
            <span>{analyzingBlueprint ? "🧠 Analyzing & Formulating Blueprint..." : "✨ Auto-Detect Blueprint (GenSpark Style)"}</span>
          </button>
        </div>
      </div>

      {/* 2. GenSpark Blueprint Cockpit Card (Active when blueprint is formulated) */}
      {blueprint && (
        <div
          style={{
            padding: "20px",
            borderRadius: "14px",
            background: isDarkMode
              ? "linear-gradient(180deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9))"
              : "linear-gradient(180deg, #f0fdf4, #ffffff)",
            border: isDarkMode ? "2px solid #3b82f6" : "2px solid #22c55e",
            boxShadow: isDarkMode ? "0 8px 30px rgba(59, 130, 246, 0.25)" : "0 8px 30px rgba(34, 197, 94, 0.15)",
            marginBottom: "24px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", borderBottom: isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid #e2e8f0", paddingBottom: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "24px" }}>🌟</span>
              <div>
                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 800, color: isDarkMode ? "#f8fafc" : "#0f172a" }}>
                  GenSpark Pre-Flight Blueprint Formulated
                </h3>
                <span style={{ fontSize: "11px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
                  Template & parameters selected beforehand based on semantic intent analysis
                </span>
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: 800,
                  padding: "4px 10px",
                  borderRadius: "12px",
                  background: isDarkMode ? "rgba(52, 211, 153, 0.2)" : "#dcfce7",
                  color: isDarkMode ? "#34d399" : "#16a34a",
                }}
              >
                ⚡ {(blueprint.confidence_score * 100).toFixed(0)}% Match Confidence
              </span>
            </div>
          </div>

          {/* Selected Template Highlight */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "14px",
              borderRadius: "10px",
              background: isDarkMode ? "rgba(59, 130, 246, 0.15)" : "#eff6ff",
              border: isDarkMode ? "1px solid #3b82f6" : "1px solid #bfdbfe",
              marginBottom: "14px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "28px" }}>{blueprint.template_icon}</span>
              <div>
                <div style={{ fontSize: "15px", fontWeight: 800, color: isDarkMode ? "#f8fafc" : "#1e293b" }}>
                  {blueprint.template_title}
                </div>
                <div style={{ fontSize: "12px", color: isDarkMode ? "#60a5fa" : "#1d4ed8", fontWeight: 600, marginTop: "2px" }}>
                  Category: {blueprint.recommended_doc_type} • Recommended Length: {blueprint.recommended_num_pages} Pages • Paper: {pageLayoutSize}
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                const tmpl = PREBUILT_TEMPLATES_LIST.find((t) => t.id === blueprint.recommended_template_id);
                if (tmpl) setPreviewTemplate(tmpl);
              }}
              style={{
                background: isDarkMode ? "rgba(255,255,255,0.08)" : "#ffffff",
                border: isDarkMode ? "1px solid rgba(255,255,255,0.2)" : "1px solid #cbd5e1",
                padding: "6px 14px",
                borderRadius: "6px",
                fontSize: "12px",
                fontWeight: 600,
                color: isDarkMode ? "#f8fafc" : "#1e293b",
                cursor: "pointer",
              }}
            >
              Inspect Section Outlines ({blueprint.outline_sections.length})
            </button>
          </div>

          {/* AI Match Rationale */}
          <div
            style={{
              padding: "10px 14px",
              borderRadius: "8px",
              background: isDarkMode ? "rgba(255,255,255,0.03)" : "#f8fafc",
              border: isDarkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid #e2e8f0",
              fontSize: "12px",
              lineHeight: "1.5",
              color: isDarkMode ? "#cbd5e1" : "#475569",
              marginBottom: "16px",
            }}
          >
            <span style={{ fontWeight: 700, color: isDarkMode ? "#93c5fd" : "#2563eb", marginRight: "6px" }}>
              💡 AI Match Rationale:
            </span>
            {blueprint.match_reason}
          </div>

          {/* Auto-Populated 7 Parameters Grid */}
          <div style={{ marginBottom: "16px" }}>
            <div style={{ fontSize: "12px", fontWeight: 700, color: isDarkMode ? "#f8fafc" : "#1e293b", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
              <span>🎯 Auto-Extracted Guided Parameters (Ground Truth)</span>
              <span style={{ fontSize: "10px", padding: "1px 6px", borderRadius: "4px", background: isDarkMode ? "rgba(59, 130, 246, 0.2)" : "#dbeafe", color: isDarkMode ? "#60a5fa" : "#1d4ed8", fontWeight: 700 }}>
                ✨ Verified Inferences
              </span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "10px" }}>
              <div style={{ padding: "8px 12px", borderRadius: "6px", background: isDarkMode ? "rgba(255,255,255,0.04)" : "#f1f5f9" }}>
                <span style={{ fontSize: "10px", fontWeight: 600, color: isDarkMode ? "#94a3b8" : "#64748b", textTransform: "uppercase" }}>Buyer Organization</span>
                <div style={{ fontSize: "12px", fontWeight: 700, color: isDarkMode ? "#f8fafc" : "#0f172a", marginTop: "2px" }}>
                  {buyerName || "Enterprise Client (Inferred)"}
                </div>
              </div>

              <div style={{ padding: "8px 12px", borderRadius: "6px", background: isDarkMode ? "rgba(255,255,255,0.04)" : "#f1f5f9" }}>
                <span style={{ fontSize: "10px", fontWeight: 600, color: isDarkMode ? "#94a3b8" : "#64748b", textTransform: "uppercase" }}>Vendor / Supplier</span>
                <div style={{ fontSize: "12px", fontWeight: 700, color: isDarkMode ? "#f8fafc" : "#0f172a", marginTop: "2px" }}>
                  {vendorName || "Competitive Tender Bidding"}
                </div>
              </div>

              <div style={{ padding: "8px 12px", borderRadius: "6px", background: isDarkMode ? "rgba(255,255,255,0.04)" : "#f1f5f9" }}>
                <span style={{ fontSize: "10px", fontWeight: 600, color: isDarkMode ? "#94a3b8" : "#64748b", textTransform: "uppercase" }}>Budget Ceiling</span>
                <div style={{ fontSize: "12px", fontWeight: 700, color: isDarkMode ? "#34d399" : "#059669", marginTop: "2px" }}>
                  {budgetEstimate || "Commercial Proposal Allocation"}
                </div>
              </div>

              <div style={{ padding: "8px 12px", borderRadius: "6px", background: isDarkMode ? "rgba(255,255,255,0.04)" : "#f1f5f9" }}>
                <span style={{ fontSize: "10px", fontWeight: 600, color: isDarkMode ? "#94a3b8" : "#64748b", textTransform: "uppercase" }}>Target Delivery Timeline</span>
                <div style={{ fontSize: "12px", fontWeight: 700, color: isDarkMode ? "#f8fafc" : "#0f172a", marginTop: "2px" }}>
                  {deliveryTimeline || "Deliverable Milestone Schedule"}
                </div>
              </div>

              <div style={{ padding: "8px 12px", borderRadius: "6px", background: isDarkMode ? "rgba(255,255,255,0.04)" : "#f1f5f9" }}>
                <span style={{ fontSize: "10px", fontWeight: 600, color: isDarkMode ? "#94a3b8" : "#64748b", textTransform: "uppercase" }}>Primary Tech Stack</span>
                <div style={{ fontSize: "12px", fontWeight: 700, color: isDarkMode ? "#f8fafc" : "#0f172a", marginTop: "2px" }}>
                  {primaryTech || "Cloud-Native Architecture"}
                </div>
              </div>

              <div style={{ padding: "8px 12px", borderRadius: "6px", background: isDarkMode ? "rgba(255,255,255,0.04)" : "#f1f5f9" }}>
                <span style={{ fontSize: "10px", fontWeight: 600, color: isDarkMode ? "#94a3b8" : "#64748b", textTransform: "uppercase" }}>Target Availability SLA</span>
                <div style={{ fontSize: "12px", fontWeight: 700, color: isDarkMode ? "#f8fafc" : "#0f172a", marginTop: "2px" }}>
                  {slaTarget}
                </div>
              </div>

              <div style={{ padding: "8px 12px", borderRadius: "6px", background: isDarkMode ? "rgba(255,255,255,0.04)" : "#f1f5f9" }}>
                <span style={{ fontSize: "10px", fontWeight: 600, color: isDarkMode ? "#94a3b8" : "#64748b", textTransform: "uppercase" }}>Compliance Mandates</span>
                <div style={{ fontSize: "12px", fontWeight: 700, color: isDarkMode ? "#60a5fa" : "#1d4ed8", marginTop: "2px" }}>
                  {complianceFrameworks.length > 0 ? complianceFrameworks.join(", ") : "SOC 2, GDPR"}
                </div>
              </div>
            </div>
          </div>

          {/* Planned Sections Outline Chips */}
          <div style={{ marginBottom: "18px" }}>
            <span style={{ fontSize: "11px", fontWeight: 600, color: isDarkMode ? "#94a3b8" : "#64748b" }}>
              Planned Section Blueprint:
            </span>
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "6px" }}>
              {blueprint.outline_sections.map((sec) => (
                <span
                  key={sec.index}
                  style={{
                    fontSize: "11px",
                    fontWeight: 600,
                    padding: "3px 8px",
                    borderRadius: "4px",
                    background: isDarkMode ? "rgba(255,255,255,0.06)" : "#f1f5f9",
                    color: isDarkMode ? "#e2e8f0" : "#334155",
                    border: isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid #cbd5e1",
                  }}
                >
                  {sec.index}. {sec.title}
                </span>
              ))}
            </div>
          </div>

          {/* Launch Action & Customization Toggle */}
          <div style={{ display: "flex", gap: "12px", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", borderTop: isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid #e2e8f0", paddingTop: "14px" }}>
            <button
              type="button"
              onClick={() => setShowAdvancedManualConfig((prev) => !prev)}
              style={{
                background: "none",
                border: "none",
                color: isDarkMode ? "#60a5fa" : "#1a73e8",
                fontWeight: 600,
                fontSize: "12px",
                cursor: "pointer",
                padding: 0,
                textDecoration: "underline",
              }}
            >
              {showAdvancedManualConfig ? "▲ Hide Manual Template & Parameter Overrides" : "⚙️ Review & Manually Override Template / Parameters"}
            </button>

            <button
              type="button"
              className="primary-button"
              onClick={handleSubmit}
              style={{
                padding: "10px 24px",
                fontSize: "14px",
                fontWeight: 700,
                background: "linear-gradient(135deg, #10b981, #059669)",
                border: "none",
                boxShadow: "0 4px 14px rgba(16, 185, 129, 0.35)",
              }}
            >
              🚀 Launch Document Generation with Spark Blueprint
            </button>
          </div>
        </div>
      )}

      {/* 3. Manual Overrides Section (Visible if no blueprint or when expanded) */}
      {(!blueprint || showAdvancedManualConfig) && (
        <div style={{ borderTop: blueprint ? (isDarkMode ? "1px dashed rgba(255,255,255,0.15)" : "1px dashed #cbd5e1") : "none", paddingTop: blueprint ? "20px" : 0 }}>
          {/* Category Tabs */}
          <div className="field">
            <label>
              <span>Select Document Template Category</span>
            </label>
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "8px" }}>
              {CATEGORY_TABS.map((tab) => {
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveTab(tab.id)}
                    style={{
                      padding: "6px 12px",
                      fontSize: "12px",
                      fontWeight: 600,
                      borderRadius: "8px",
                      border: "1px solid",
                      borderColor: isActive
                        ? isDarkMode
                          ? "#3b82f6"
                          : "#1a73e8"
                        : isDarkMode
                        ? "rgba(255,255,255,0.15)"
                        : "#e2e8f0",
                      background: isActive
                        ? isDarkMode
                          ? "rgba(59, 130, 246, 0.2)"
                          : "#e8f0fe"
                        : isDarkMode
                        ? "rgba(255,255,255,0.03)"
                        : "#f8fafc",
                      color: isActive ? (isDarkMode ? "#60a5fa" : "#1a73e8") : isDarkMode ? "#94a3b8" : "#64748b",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      transition: "all 0.15s ease",
                    }}
                  >
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Prebuilt Templates Cards Grid */}
          <div className="field" style={{ marginTop: "16px" }}>
            <label style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span>Choose Prebuilt Template ({filteredTemplates.length})</span>
              <span style={{ fontSize: "12px", color: isDarkMode ? "#60a5fa" : "#1a73e8", fontWeight: 600 }}>
                Selected: {selectedTemplate.title}
              </span>
            </label>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
                gap: "14px",
                marginTop: "10px",
                maxHeight: "440px",
                overflowY: "auto",
                paddingRight: "6px",
              }}
            >
              {filteredTemplates.map((tmpl) => {
                const isSelected = selectedTemplateId === tmpl.id;
                return (
                  <div
                    key={tmpl.id}
                    onClick={() => handleSelectTemplate(tmpl)}
                    style={{
                      padding: "14px",
                      borderRadius: "10px",
                      border: isSelected
                        ? isDarkMode
                          ? "2px solid #3b82f6"
                          : "2px solid #1a73e8"
                        : isDarkMode
                        ? "1px solid rgba(255,255,255,0.1)"
                        : "1px solid #e2e8f0",
                      background: isSelected
                        ? isDarkMode
                          ? "rgba(59, 130, 246, 0.15)"
                          : "rgba(232, 240, 254, 0.8)"
                        : isDarkMode
                        ? "rgba(255,255,255,0.03)"
                        : "#ffffff",
                      boxShadow: isSelected
                        ? isDarkMode
                          ? "0 4px 14px rgba(59, 130, 246, 0.2)"
                          : "0 4px 14px rgba(26, 115, 232, 0.15)"
                        : "none",
                      cursor: "pointer",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between",
                      transition: "all 0.15s ease",
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "6px" }}>
                        <span style={{ fontSize: "11px", fontWeight: 800, padding: "3px 8px", borderRadius: "4px", background: isDarkMode ? "rgba(59, 130, 246, 0.2)" : "#e0f2fe", color: isDarkMode ? "#60a5fa" : "#0284c7", letterSpacing: "0.5px" }}>
                          {tmpl.icon}
                        </span>
                        <span
                          style={{
                            fontSize: "10px",
                            fontWeight: 700,
                            padding: "2px 8px",
                            borderRadius: "10px",
                            background: isDarkMode ? "rgba(255,255,255,0.1)" : "#f1f5f9",
                            color: isDarkMode ? "#cbd5e1" : "#475569",
                            textTransform: "uppercase",
                          }}
                        >
                          {tmpl.category}
                        </span>
                      </div>

                      <h4
                        style={{
                          margin: "0 0 4px 0",
                          fontSize: "14px",
                          fontWeight: 700,
                          color: isDarkMode ? "#f8fafc" : "#1e293b",
                        }}
                      >
                        {tmpl.title}
                      </h4>

                      <p
                        style={{
                          margin: "0 0 10px 0",
                          fontSize: "12px",
                          color: isDarkMode ? "#94a3b8" : "#64748b",
                          lineHeight: "1.4",
                        }}
                      >
                        {tmpl.description}
                      </p>
                    </div>

                    <div>
                      {/* Tone Badge */}
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "4px",
                          fontSize: "11px",
                          fontWeight: 600,
                          color: isDarkMode ? "#38bdf8" : "#0284c7",
                          marginBottom: "8px",
                        }}
                      >
                        <span>Tone:</span>
                        <span>{tmpl.tone}</span>
                      </div>

                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setPreviewTemplate(tmpl);
                          }}
                          style={{
                            background: "none",
                            border: "none",
                            fontSize: "11px",
                            fontWeight: 600,
                            color: isDarkMode ? "#60a5fa" : "#1a73e8",
                            cursor: "pointer",
                            padding: 0,
                            textDecoration: "underline",
                          }}
                        >
                          View Outlines ({tmpl.sections.length})
                        </button>

                        {isSelected && (
                          <span
                            style={{
                              fontSize: "11px",
                              fontWeight: 700,
                              color: isDarkMode ? "#34d399" : "#059669",
                              display: "flex",
                              alignItems: "center",
                              gap: "3px",
                            }}
                          >
                            ✓ Selected
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Grid: Layout Size & Num Pages */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "16px", marginTop: "16px", marginBottom: "16px" }}>
            <label className="field" style={{ margin: 0 }}>
              <span>Page Paper Layout Size</span>
              <select value={pageLayoutSize} onChange={(e) => setPageLayoutSize(e.target.value as PageLayoutSize)}>
                <option value="A4">A4 Standard (210mm x 297mm)</option>
                <option value="LETTER">US Letter (8.5" x 11")</option>
                <option value="A3">A3 Presentation (297mm x 420mm)</option>
                <option value="LEGAL">US Legal (8.5" x 14")</option>
              </select>
            </label>

            <div className="field" style={{ margin: 0 }}>
              <label style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span>Target page length</span>
                <span style={{ fontSize: "11px", color: "#6b7280" }}>1 - 50 pages</span>
              </label>

              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "4px" }}>
                <button
                  type="button"
                  style={{
                    width: "36px",
                    height: "36px",
                    borderRadius: "6px",
                    border: isDarkMode ? "1px solid rgba(255,255,255,0.2)" : "1px solid #cbd5e1",
                    background: isDarkMode ? "rgba(255,255,255,0.05)" : "#f8fafc",
                    color: isDarkMode ? "#f8fafc" : "inherit",
                    fontSize: "16px",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                  onClick={() => {
                    const val = Math.max(1, numPages - 1);
                    setNumPages(val);
                    useWizardStore.setState({ numPages: val });
                  }}
                >
                  -
                </button>

                <input
                  type="number"
                  min={1}
                  max={50}
                  value={numPages}
                  onChange={(e) => {
                    const raw = Number(e.target.value);
                    const val = isNaN(raw) ? 1 : Math.max(1, Math.min(50, raw));
                    setNumPages(val);
                    useWizardStore.setState({ numPages: val });
                  }}
                  style={{
                    flex: 1,
                    height: "36px",
                    fontSize: "14px",
                    fontWeight: 600,
                    textAlign: "center",
                    background: isDarkMode ? "transparent" : "inherit",
                    color: isDarkMode ? "#f8fafc" : "inherit",
                    border: "none",
                    borderBottom: isDarkMode ? "1px solid rgba(255,255,255,0.2)" : "1px solid #cbd5e1",
                  }}
                />

                <button
                  type="button"
                  style={{
                    width: "36px",
                    height: "36px",
                    borderRadius: "6px",
                    border: isDarkMode ? "1px solid rgba(255,255,255,0.2)" : "1px solid #cbd5e1",
                    background: isDarkMode ? "rgba(255,255,255,0.05)" : "#f8fafc",
                    color: isDarkMode ? "#f8fafc" : "inherit",
                    fontSize: "16px",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                  onClick={() => {
                    const val = Math.min(50, numPages + 1);
                    setNumPages(val);
                    useWizardStore.setState({ numPages: val });
                  }}
                >
                  +
                </button>
              </div>
            </div>
          </div>

          {/* Content Density / Temperature */}
          <div className="field" style={{ marginBottom: "16px" }}>
            <label>
              <span>Content Density / Temperature</span>
            </label>
            <div style={{ display: "flex", gap: "8px", marginTop: "6px" }}>
              {(["min", "med", "max"] as const).map((level) => {
                const isActive = contentDensity === level;
                return (
                  <button
                    key={level}
                    type="button"
                    onClick={() => {
                      setContentDensity(level);
                      useWizardStore.setState({ contentDensity: level });
                    }}
                    style={{
                      flex: 1,
                      padding: "8px",
                      borderRadius: "8px",
                      border: "1px solid",
                      borderColor: isActive ? (isDarkMode ? "#3b82f6" : "#1a73e8") : isDarkMode ? "rgba(255,255,255,0.2)" : "#cbd5e1",
                      background: isActive ? (isDarkMode ? "rgba(59, 130, 246, 0.2)" : "#eff6ff") : isDarkMode ? "transparent" : "#f8fafc",
                      color: isActive ? (isDarkMode ? "#60a5fa" : "#1a73e8") : isDarkMode ? "#94a3b8" : "#64748b",
                      fontWeight: isActive ? 600 : 500,
                      textTransform: "uppercase",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    {level}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Guided Key Procurement Parameters (Optional Ground Truth) */}
      <div
        style={{
          border: isDarkMode ? "1px solid rgba(59, 130, 246, 0.3)" : "1px solid #bfdbfe",
          background: isDarkMode ? "rgba(15, 23, 42, 0.6)" : "#f8fafc",
          borderRadius: "10px",
          marginBottom: "16px",
          overflow: "hidden",
          transition: "all 0.2s ease",
        }}
      >
        <button
          type="button"
          onClick={() => setGuidedOpen((prev) => !prev)}
          style={{
            width: "100%",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "10px 14px",
            background: isDarkMode ? "rgba(59, 130, 246, 0.12)" : "#eff6ff",
            border: "none",
            borderBottom: guidedOpen
              ? isDarkMode
                ? "1px solid rgba(59, 130, 246, 0.2)"
                : "1px solid #dbeafe"
              : "none",
            cursor: "pointer",
            textAlign: "left",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "14px" }}>🎯</span>
            <div>
              <span
                style={{
                  fontSize: "13px",
                  fontWeight: 600,
                  color: isDarkMode ? "#93c5fd" : "#1d4ed8",
                }}
              >
                Key Procurement Parameters (Optional)
              </span>
              <span
                style={{
                  fontSize: "11px",
                  marginLeft: "8px",
                  color: isDarkMode ? "#94a3b8" : "#64748b",
                }}
              >
                Provide ground truth parameters directly to avoid AI hallucination
              </span>
            </div>
          </div>
          <span style={{ fontSize: "12px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
            {guidedOpen ? "▲ Hide" : "▼ Show"}
          </span>
        </button>

        {guidedOpen && (
          <div style={{ padding: "14px", display: "flex", flexDirection: "column", gap: "12px" }}>
            {/* Row 1: Buyer & Vendor */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "14px" }}>
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "11px",
                    fontWeight: 600,
                    marginBottom: "4px",
                    color: isDarkMode ? "#cbd5e1" : "#475569",
                  }}
                >
                  Buyer / Client Organization
                </label>
                <input
                  type="text"
                  placeholder="e.g. Acme Health Corp"
                  value={buyerName}
                  onChange={(e) => setBuyerName(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "7px 10px",
                    fontSize: "12px",
                    borderRadius: "6px",
                    border: isDarkMode ? "1px solid rgba(255,255,255,0.15)" : "1px solid #cbd5e1",
                    background: isDarkMode ? "rgba(255,255,255,0.05)" : "#ffffff",
                    color: isDarkMode ? "#f8fafc" : "#1e293b",
                  }}
                />
              </div>

              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "11px",
                    fontWeight: 600,
                    marginBottom: "4px",
                    color: isDarkMode ? "#cbd5e1" : "#475569",
                  }}
                >
                  Vendor / Supplier (if known)
                </label>
                <input
                  type="text"
                  placeholder="e.g. CloudScale Solutions LLC"
                  value={vendorName}
                  onChange={(e) => setVendorName(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "7px 10px",
                    fontSize: "12px",
                    borderRadius: "6px",
                    border: isDarkMode ? "1px solid rgba(255,255,255,0.15)" : "1px solid #cbd5e1",
                    background: isDarkMode ? "rgba(255,255,255,0.05)" : "#ffffff",
                    color: isDarkMode ? "#f8fafc" : "#1e293b",
                  }}
                />
              </div>
            </div>

            {/* Row 2: Budget & Delivery Timeline */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "14px" }}>
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "11px",
                    fontWeight: 600,
                    marginBottom: "4px",
                    color: isDarkMode ? "#cbd5e1" : "#475569",
                  }}
                >
                  Budget Estimate / Ceiling ($)
                </label>
                <input
                  type="text"
                  placeholder="e.g. $150,000"
                  value={budgetEstimate}
                  onChange={(e) => setBudgetEstimate(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "7px 10px",
                    fontSize: "12px",
                    borderRadius: "6px",
                    border: isDarkMode ? "1px solid rgba(255,255,255,0.15)" : "1px solid #cbd5e1",
                    background: isDarkMode ? "rgba(255,255,255,0.05)" : "#ffffff",
                    color: isDarkMode ? "#f8fafc" : "#1e293b",
                  }}
                />
              </div>

              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "11px",
                    fontWeight: 600,
                    marginBottom: "4px",
                    color: isDarkMode ? "#cbd5e1" : "#475569",
                  }}
                >
                  Delivery Timeline / Deadline
                </label>
                <input
                  type="text"
                  placeholder="e.g. 6 Months / Q3 2026"
                  value={deliveryTimeline}
                  onChange={(e) => setDeliveryTimeline(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "7px 10px",
                    fontSize: "12px",
                    borderRadius: "6px",
                    border: isDarkMode ? "1px solid rgba(255,255,255,0.15)" : "1px solid #cbd5e1",
                    background: isDarkMode ? "rgba(255,255,255,0.05)" : "#ffffff",
                    color: isDarkMode ? "#f8fafc" : "#1e293b",
                  }}
                />
              </div>
            </div>

            {/* Row 3: Primary Tech Stack & SLA */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "14px" }}>
              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "11px",
                    fontWeight: 600,
                    marginBottom: "4px",
                    color: isDarkMode ? "#cbd5e1" : "#475569",
                  }}
                >
                  Primary Tech Stack / Platforms
                </label>
                <input
                  type="text"
                  placeholder="e.g. AWS, Kubernetes, React, Python FastAPI, PostgreSQL"
                  value={primaryTech}
                  onChange={(e) => setPrimaryTech(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "7px 10px",
                    fontSize: "12px",
                    borderRadius: "6px",
                    border: isDarkMode ? "1px solid rgba(255,255,255,0.15)" : "1px solid #cbd5e1",
                    background: isDarkMode ? "rgba(255,255,255,0.05)" : "#ffffff",
                    color: isDarkMode ? "#f8fafc" : "#1e293b",
                  }}
                />
              </div>

              <div>
                <label
                  style={{
                    display: "block",
                    fontSize: "11px",
                    fontWeight: 600,
                    marginBottom: "4px",
                    color: isDarkMode ? "#cbd5e1" : "#475569",
                  }}
                >
                  Target SLA Availability
                </label>
                <select
                  value={slaTarget}
                  onChange={(e) => setSlaTarget(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "7px 10px",
                    fontSize: "12px",
                    borderRadius: "6px",
                    border: isDarkMode ? "1px solid rgba(255,255,255,0.15)" : "1px solid #cbd5e1",
                    background: isDarkMode ? "rgba(255,255,255,0.05)" : "#ffffff",
                    color: isDarkMode ? "#f8fafc" : "#1e293b",
                  }}
                >
                  {SLA_OPTIONS.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Row 4: Compliance Framework Badges */}
            <div>
              <label
                style={{
                  display: "block",
                  fontSize: "11px",
                  fontWeight: 600,
                  marginBottom: "6px",
                  color: isDarkMode ? "#cbd5e1" : "#475569",
                }}
              >
                Required Compliance Frameworks
              </label>
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                {COMPLIANCE_OPTIONS.map((fw) => {
                  const isSelected = complianceFrameworks.includes(fw);
                  return (
                    <button
                      key={fw}
                      type="button"
                      onClick={() => toggleCompliance(fw)}
                      style={{
                        padding: "4px 10px",
                        fontSize: "11px",
                        fontWeight: 600,
                        borderRadius: "6px",
                        border: "1px solid",
                        borderColor: isSelected
                          ? isDarkMode
                            ? "#3b82f6"
                            : "#2563eb"
                          : isDarkMode
                          ? "rgba(255,255,255,0.15)"
                          : "#cbd5e1",
                        background: isSelected
                          ? isDarkMode
                            ? "rgba(59, 130, 246, 0.25)"
                            : "#dbeafe"
                          : isDarkMode
                          ? "rgba(255,255,255,0.03)"
                          : "#ffffff",
                        color: isSelected
                          ? isDarkMode
                            ? "#93c5fd"
                            : "#1d4ed8"
                          : isDarkMode
                          ? "#94a3b8"
                          : "#64748b",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                      }}
                    >
                      {isSelected ? `✓ ${fw}` : `+ ${fw}`}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {error && <p className="error-text">{error}</p>}

      <button className="primary-button" onClick={handleSubmit}>
        Generate document
      </button>

      {/* Section Outlines Preview Modal */}
      {/* Interactive Template Preview & Outlines Modal */}
      {previewTemplate &&
        createPortal(
          <div
            style={{
              position: "fixed",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: "rgba(15, 23, 42, 0.8)",
              backdropFilter: "blur(8px)",
              zIndex: 999999,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "24px",
            }}
            onClick={() => setPreviewTemplate(null)}
          >
          <div
            style={{
              background: isDarkMode ? "#0f172a" : "#ffffff",
              borderRadius: "14px",
              padding: "28px",
              maxWidth: "960px",
              width: "90vw",
              maxHeight: "90vh",
              display: "flex",
              flexDirection: "column",
              boxShadow: "0 20px 50px rgba(0,0,0,0.4)",
              border: isDarkMode ? "1px solid rgba(255,255,255,0.12)" : "1px solid rgba(0,0,0,0.1)",
              position: "relative",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", borderBottom: isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid #e2e8f0", paddingBottom: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span style={{ fontSize: "28px" }}>{previewTemplate.icon}</span>
                <div>
                  <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 800, color: isDarkMode ? "#f8fafc" : "#0f172a" }}>
                    {previewTemplate.title}
                  </h3>
                  <span style={{ fontSize: "12px", color: isDarkMode ? "#60a5fa" : "#1a73e8", fontWeight: 600 }}>
                    Category: {previewTemplate.category} • {previewTemplate.sections.length} Document Sections
                  </span>
                </div>
              </div>
              <button
                style={{
                  background: isDarkMode ? "rgba(255,255,255,0.08)" : "#f1f5f9",
                  border: "none",
                  borderRadius: "50%",
                  width: "32px",
                  height: "32px",
                  fontSize: "16px",
                  cursor: "pointer",
                  color: isDarkMode ? "#cbd5e1" : "#475569",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
                onClick={() => setPreviewTemplate(null)}
                title="Close Preview"
              >
                ✕
              </button>
            </div>

            <p style={{ fontSize: "13px", color: isDarkMode ? "#cbd5e1" : "#475569", margin: "0 0 16px 0", lineHeight: "1.4" }}>
              Tone Profile: <strong>{previewTemplate.tone}</strong> — {previewTemplate.toneDescription}
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", flex: 1, minHeight: 0 }}>
              {/* Left Column: Outline List */}
              <div style={{ display: "flex", flexDirection: "column" }}>
                <h4 style={{ margin: "0 0 10px 0", fontSize: "13px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
                  Section Structure & Guidance ({previewTemplate.sections.length} Sections)
                </h4>
                <div style={{ display: "flex", flexDirection: "column", gap: "10px", flex: 1, overflowY: "auto", paddingRight: "6px" }}>
                  {previewTemplate.sections.map((sec, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: "12px 14px",
                        borderRadius: "8px",
                        background: isDarkMode ? "rgba(255,255,255,0.04)" : "#f8fafc",
                        border: isDarkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid #e2e8f0",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                        <span style={{ fontSize: "13px", fontWeight: 700, color: isDarkMode ? "#f8fafc" : "#1e293b" }}>
                          {idx + 1}. {sec.title}
                        </span>
                        <span
                          style={{
                            fontSize: "10px",
                            fontWeight: 700,
                            padding: "2px 8px",
                            borderRadius: "4px",
                            background: isDarkMode ? "rgba(59, 130, 246, 0.2)" : "#e0f2fe",
                            color: isDarkMode ? "#60a5fa" : "#0369a1",
                            textTransform: "uppercase",
                          }}
                        >
                          {sec.section_type}
                        </span>
                      </div>
                      <p style={{ margin: 0, fontSize: "12px", color: isDarkMode ? "#94a3b8" : "#64748b", lineHeight: "1.4" }}>{sec.guidance}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Right Column: Visual Document Page Mockup */}
              <div style={{ display: "flex", flexDirection: "column" }}>
                <h4 style={{ margin: "0 0 10px 0", fontSize: "13px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
                  Sample Layout Preview (Page 1)
                </h4>
                <div
                  style={{
                    background: "#ffffff",
                    color: "#1e293b",
                    borderRadius: "8px",
                    padding: "20px",
                    border: "1px solid #cbd5e1",
                    boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
                    flex: 1,
                    overflowY: "auto",
                    fontFamily: "Inter, sans-serif",
                    fontSize: "12px",
                  }}
                >
                  <div style={{ borderLeft: "5px solid #1a73e8", paddingLeft: "12px", marginBottom: "16px" }}>
                    <div style={{ fontSize: "16px", fontWeight: 800, color: "#0f172a", letterSpacing: "0.5px" }}>{previewTemplate.title.toUpperCase()}</div>
                    <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 600, marginTop: "2px" }}>CONFIDENTIAL ENTERPRISE PROCUREMENT PROPOSAL</div>
                  </div>

                  <div style={{ background: "#f8fafc", padding: "12px 14px", borderRadius: "6px", border: "1px solid #e2e8f0", marginBottom: "14px" }}>
                    <div style={{ fontWeight: 700, color: "#1a73e8", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>1. EXECUTIVE SUMMARY</div>
                    <div style={{ color: "#475569", marginTop: "4px", lineHeight: "1.4" }}>
                      This proposal outlines the technical architecture, commercial terms, compliance specifications, and SLA governance required for enterprise execution...
                    </div>
                  </div>

                  <div style={{ marginBottom: "14px" }}>
                    <div style={{ fontWeight: 700, color: "#0f172a", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "6px" }}>2. SCOPE & DELIVERABLES</div>
                    <ul style={{ margin: 0, paddingLeft: "16px", color: "#334155", lineHeight: "1.5" }}>
                      <li>Core Software Architecture & Hybrid RAG Vector Pipeline</li>
                      <li>Enterprise Access Control & Data Security Governance</li>
                      <li>24/7 Technical Support & Uptime SLA Guarantee</li>
                    </ul>
                  </div>

                  <div style={{ fontWeight: 700, color: "#0f172a", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "6px" }}>3. COMMERCIAL SCHEDULE & PRICING</div>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px", marginBottom: "14px" }}>
                    <thead>
                      <tr style={{ background: "#1e293b", color: "#ffffff" }}>
                        <th style={{ padding: "6px 8px", textAlign: "left" }}>Deliverable</th>
                        <th style={{ padding: "6px 8px", textAlign: "right" }}>Qty</th>
                        <th style={{ padding: "6px 8px", textAlign: "right" }}>Price</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
                        <td style={{ padding: "6px 8px" }}>Enterprise License & Cloud Hosting</td>
                        <td style={{ padding: "6px 8px", textAlign: "right" }}>1</td>
                        <td style={{ padding: "6px 8px", textAlign: "right" }}>$12,500.00</td>
                      </tr>
                      <tr style={{ borderBottom: "1px solid #e2e8f0" }}>
                        <td style={{ padding: "6px 8px" }}>Implementation & Security Audit</td>
                        <td style={{ padding: "6px 8px", textAlign: "right" }}>1</td>
                        <td style={{ padding: "6px 8px", textAlign: "right" }}>$4,500.00</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Footer Actions */}
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "20px", gap: "12px", borderTop: isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid #e2e8f0", paddingTop: "14px" }}>
              <button
                type="button"
                className="secondary-button"
                onClick={() => setPreviewTemplate(null)}
                style={{
                  padding: "10px 18px",
                  fontSize: "13px",
                  fontWeight: 600,
                  color: isDarkMode ? "#f8fafc" : "#1e293b",
                  background: isDarkMode ? "rgba(255,255,255,0.08)" : "#ffffff",
                  borderColor: isDarkMode ? "rgba(255,255,255,0.25)" : "#cbd5e1",
                }}
              >
                Close Preview
              </button>
              <button
                type="button"
                className="primary-button"
                onClick={() => {
                  handleSelectTemplate(previewTemplate);
                  setPreviewTemplate(null);
                }}
                style={{ padding: "10px 22px", fontSize: "13px", fontWeight: 700 }}
              >
                ✓ Select & Use This Template
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}

