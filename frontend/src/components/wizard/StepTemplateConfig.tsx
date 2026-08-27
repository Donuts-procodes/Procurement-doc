import { useState } from "react";
import { createPortal } from "react-dom";
import { uploadKnowledgeFiles } from "../../api/client";
import { useWizardStore } from "../../state/wizardStore";
import {
  PREBUILT_TEMPLATES_LIST,
  type PageLayoutSize,
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

export function StepTemplateConfig() {
  const storeProcurementDocType = useWizardStore((s) => s.procurementDocType);
  const storeTemplateId = useWizardStore((s) => s.templateId);
  const storeNumPages = useWizardStore((s) => s.numPages);
  const storePrompt = useWizardStore((s) => s.prompt);
  const sessionId = useWizardStore((s) => s.sessionId);
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
  const [referenceFile, setReferenceFile] = useState<{ name: string; size: number } | null>(
    kbFiles.length > 0 ? { name: kbFiles[0].filename, size: 0 } : null
  );

  const storeContentDensity = useWizardStore((s) => s.contentDensity);
  const [activeTab, setActiveTab] = useState<string>("ALL");
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>(storeTemplateId || "rfp_enterprise");
  const [procurementDocType, setProcurementDocType] = useState<ProcurementDocType>(storeProcurementDocType || "RFP");
  const [numPages, setNumPages] = useState(storeNumPages || 5);
  const [prompt, setPrompt] = useState(storePrompt || "");
  const [contentDensity, setContentDensity] = useState<"min" | "med" | "max">(storeContentDensity || "med");
  const [previewTemplate, setPreviewTemplate] = useState<TemplateDefinition | null>(null);

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

  async function handleReferenceUpload(files: FileList | null) {
    if (!files || files.length === 0) return;
    const file = files[0];
    setUploadingRef(true);
    setError(null);
    try {
      const res = await uploadKnowledgeFiles([file]);
      setKnowledgeBase(res.kb_id, res.files);
      setReferenceFile({ name: file.name, size: file.size });
    } catch (e: any) {
      setError("Failed to upload reference template: " + (e.message || "Upload error"));
    } finally {
      setUploadingRef(false);
    }
  }

  function handleRemoveReference() {
    setReferenceFile(null);
    setKnowledgeBase("", []);
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

    useWizardStore.setState({ templateId: selectedTemplateId });
    setTemplateConfig(procurementDocType, numPages, prompt.trim(), contentDensity);
  }

  return (
    <div className="wizard-step" style={{ maxWidth: "100%" }}>
      <h2>Configure Procurement Document & Template</h2>
      <p className="wizard-step__subtitle">
        Select a prebuilt template or custom builder, optionally attach a reference document, and customize your requirements.
      </p>

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
            gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
            gap: "12px",
            marginTop: "10px",
            maxHeight: "320px",
            overflowY: "auto",
            paddingRight: "4px",
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

      {/* Reference Template File Attachment Section */}
      <div
        className="field"
        style={{
          marginTop: "16px",
          marginBottom: "16px",
          padding: "16px",
          borderRadius: "10px",
          background: isDarkMode ? "rgba(30, 41, 59, 0.4)" : "#f8fafc",
          border: isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid #e2e8f0",
        }}
      >
        <label style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
          <span style={{ fontWeight: 700, fontSize: "13px", color: isDarkMode ? "#f8fafc" : "#0f172a" }}>
            Reference Template / Document File (Optional)
          </span>
          <span style={{ fontSize: "11px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
            PDF, DOCX, TXT, MD, JSON
          </span>
        </label>
        <p style={{ margin: "0 0 12px 0", fontSize: "12px", color: isDarkMode ? "#cbd5e1" : "#64748b" }}>
          Attach an existing document or custom template file. The AI RAG agent will extract clause structures, terms, and section layouts to use as an exact reference.
        </p>

        {referenceFile ? (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "10px 14px",
              borderRadius: "8px",
              background: isDarkMode ? "rgba(59, 130, 246, 0.15)" : "#eff6ff",
              border: isDarkMode ? "1px solid #3b82f6" : "1px solid #93c5fd",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "10px", fontWeight: 800, padding: "2px 6px", borderRadius: "4px", background: isDarkMode ? "#3b82f6" : "#1a73e8", color: "#ffffff" }}>
                REF FILE
              </span>
              <div>
                <div style={{ fontWeight: 700, fontSize: "13px", color: isDarkMode ? "#f8fafc" : "#1e293b" }}>
                  {referenceFile.name}
                </div>
                <div style={{ fontSize: "11px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
                  {(referenceFile.size / 1024).toFixed(1)} KB • Indexed in Vector RAG Knowledge Base
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={handleRemoveReference}
              style={{
                background: "none",
                border: "none",
                color: isDarkMode ? "#f87171" : "#dc2626",
                fontWeight: 600,
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              Remove
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <input
              type="file"
              id="custom-ref-upload"
              accept=".pdf,.docx,.txt,.md,.json"
              onChange={(e) => handleReferenceUpload(e.target.files)}
              style={{ display: "none" }}
            />
            <label
              htmlFor="custom-ref-upload"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 16px",
                borderRadius: "8px",
                background: isDarkMode ? "rgba(255,255,255,0.08)" : "#ffffff",
                border: isDarkMode ? "1px solid rgba(255,255,255,0.2)" : "1px solid #cbd5e1",
                color: isDarkMode ? "#f8fafc" : "#1e293b",
                fontWeight: 600,
                fontSize: "12px",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {uploadingRef ? "Uploading Reference..." : "+ Attach Reference Template"}
            </label>
            <span style={{ fontSize: "12px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
              {uploadingRef ? "Indexing text and clauses into vector store..." : "No reference document attached yet."}
            </span>
          </div>
        )}
      </div>

      {/* Grid: Layout Size & Num Pages */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
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
      <div className="field">
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

      {/* Procurement details & requirements textarea */}
      <label className="field">
        <span>Procurement details & requirements</span>
        <textarea
          rows={4}
          value={prompt}
          onChange={(e) => {
            const val = e.target.value;
            setPrompt(val);
            useWizardStore.setState({ prompt: val });
          }}
          placeholder="e.g. Generate RFP for Property Match mobile app with real-time chat, property matching, and web admin dashboard..."
        />
      </label>

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

