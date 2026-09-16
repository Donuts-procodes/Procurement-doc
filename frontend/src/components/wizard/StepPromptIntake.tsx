import { useState, useRef } from "react";
import { uploadKnowledgeFiles } from "../../api/client";
import { useWizardStore } from "../../state/wizardStore";
import {
  PREBUILT_TEMPLATES_LIST,
  type GuidedParameters,
} from "../../types";

export function StepPromptIntake() {
  const sessionId = useWizardStore((s) => s.sessionId);
  const kbId = useWizardStore((s) => s.kbId);
  const templateId = useWizardStore((s) => s.templateId);
  const storePrompt = useWizardStore((s) => s.prompt);
  const storeNumPages = useWizardStore((s) => s.numPages);
  const storeContentDensity = useWizardStore((s) => s.contentDensity);
  const storeGuidedParams = useWizardStore((s) => s.guidedParams);
  const setTemplateConfig = useWizardStore((s) => s.setTemplateConfig);
  const setKnowledgeBase = useWizardStore((s) => s.setKnowledgeBase);
  const setSession = useWizardStore((s) => s.setSession);
  const setStep = useWizardStore((s) => s.setStep);
  const setError = useWizardStore((s) => s.setError);
  const error = useWizardStore((s) => s.error);
  const isDarkMode = useWizardStore((s) => s.isDarkMode);
  const procurementDocType = useWizardStore((s) => s.procurementDocType);
  const addChatMessage = useWizardStore((s) => s.addChatMessage);

  const selectedTemplate = PREBUILT_TEMPLATES_LIST.find((t) => t.id === templateId) || PREBUILT_TEMPLATES_LIST[0];

  const [prompt, setPrompt] = useState(storePrompt || "");
  const [numPages, setNumPages] = useState(storeNumPages || 5);
  const [contentDensity, setContentDensity] = useState<"min" | "med" | "max">(storeContentDensity || "med");
  const [attachedFiles, setAttachedFiles] = useState<Array<{ name: string; size: number }>>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Guided params
  const [buyerName, setBuyerName] = useState(storeGuidedParams?.buyer_name || "");
  const [vendorName, setVendorName] = useState(storeGuidedParams?.vendor_name || "");
  const [budgetEstimate, setBudgetEstimate] = useState(storeGuidedParams?.budget_estimate || "");
  const [deliveryTimeline, setDeliveryTimeline] = useState(storeGuidedParams?.delivery_timeline || "");
  const [showParams, setShowParams] = useState(false);

  async function handleFileUpload(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      const res = await uploadKnowledgeFiles(Array.from(files), kbId || undefined);
      setKnowledgeBase(res.kb_id, res.files);
      const newEntries = Array.from(files).map((f) => ({ name: f.name, size: f.size }));
      setAttachedFiles((prev) => {
        const names = new Set(prev.map((p) => p.name));
        return [...prev, ...newEntries.filter((e) => !names.has(e.name))];
      });
    } catch (e: any) {
      setError("Failed to upload file(s): " + (e.message || "Upload error"));
    } finally {
      setUploading(false);
    }
  }

  function handleRemoveFile(fileName: string) {
    setAttachedFiles((prev) => prev.filter((f) => f.name !== fileName));
  }

  function handleGenerate() {
    if (prompt.trim().length < 1) {
      setError("Describe what the document should be about.");
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
    };

    useWizardStore.setState({ templateId });
    addChatMessage({
      id: `initial_prompt_${Date.now()}`,
      sender: "user",
      text: prompt.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    });
    setTemplateConfig(procurementDocType, numPages, prompt.trim(), contentDensity, guided);
  }

  return (
    <div className="wizard-step" style={{ maxWidth: "100%" }}>
      {/* Header with selected template badge */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <div>
          <h2 style={{ margin: 0, color: isDarkMode ? "#f8fafc" : "#0f172a" }}>
            Describe Your Document
          </h2>
          <p style={{ margin: "4px 0 0 0", fontSize: "13px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
            Provide project requirements and attach any reference documents.
          </p>
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "8px 14px",
            borderRadius: "10px",
            background: isDarkMode ? "rgba(59, 130, 246, 0.12)" : "#eff6ff",
            border: isDarkMode ? "1px solid rgba(59, 130, 246, 0.2)" : "1px solid #bfdbfe",
            cursor: "pointer",
          }}
          onClick={() => setStep("templates")}
          title="Click to change template"
        >
          <span style={{ fontSize: "20px" }}>{selectedTemplate.icon}</span>
          <div>
            <div style={{ fontSize: "12px", fontWeight: 700, color: isDarkMode ? "#f8fafc" : "#1e293b" }}>
              {selectedTemplate.title}
            </div>
            <div style={{ fontSize: "10px", color: isDarkMode ? "#60a5fa" : "#1d4ed8" }}>
              Change template ↗
            </div>
          </div>
        </div>
      </div>

      {/* Main prompt textarea */}
      <div
        style={{
          padding: "18px",
          borderRadius: "14px",
          background: isDarkMode ? "rgba(15, 23, 42, 0.7)" : "#ffffff",
          border: isDarkMode ? "1px solid rgba(255,255,255,0.12)" : "1px solid #e2e8f0",
          boxShadow: isDarkMode ? "0 4px 20px rgba(0,0,0,0.25)" : "0 4px 20px rgba(0,0,0,0.05)",
          marginBottom: "16px",
        }}
      >
        <label style={{ display: "block", marginBottom: "6px", fontWeight: 700, fontSize: "13px", color: isDarkMode ? "#f8fafc" : "#0f172a" }}>
          System Prompt / Project Requirements
        </label>
        <textarea
          rows={5}
          value={prompt}
          onChange={(e) => {
            setPrompt(e.target.value);
            useWizardStore.setState({ prompt: e.target.value });
          }}
          placeholder="e.g. Draft a cloud infrastructure RFP for AWS, React, Python FastAPI with SOC 2, HIPAA, and 99.99% SLA. Budget $250,000, timeline 6 months. Include vendor evaluation criteria and milestone payment schedule."
          style={{
            width: "100%",
            padding: "12px 14px",
            fontSize: "14px",
            lineHeight: "1.5",
            borderRadius: "10px",
            border: isDarkMode ? "1px solid rgba(255,255,255,0.15)" : "1px solid #d7d9dd",
            background: isDarkMode ? "rgba(255,255,255,0.05)" : "#f8fafc",
            color: isDarkMode ? "#f8fafc" : "#1e293b",
            resize: "vertical",
            outline: "none",
            boxSizing: "border-box",
            fontFamily: "inherit",
          }}
        />
      </div>

      {/* File Upload Section */}
      <div
        style={{
          padding: "16px 18px",
          borderRadius: "12px",
          background: isDarkMode ? "rgba(255,255,255,0.03)" : "#f8fafc",
          border: isDarkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid #e2e8f0",
          marginBottom: "16px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
          <span style={{ fontWeight: 600, fontSize: "13px", color: isDarkMode ? "#cbd5e1" : "#334155" }}>
            📎 Attach Reference Documents (Optional)
          </span>
          <span style={{ fontSize: "11px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
            PDF, DOCX, TXT, MD
          </span>
        </div>

        {/* Attached files */}
        {attachedFiles.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "10px" }}>
            {attachedFiles.map((file) => (
              <div
                key={file.name}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "5px 10px",
                  borderRadius: "6px",
                  background: isDarkMode ? "rgba(59, 130, 246, 0.15)" : "#eff6ff",
                  border: isDarkMode ? "1px solid #3b82f6" : "1px solid #93c5fd",
                  fontSize: "12px",
                }}
              >
                <span style={{ fontWeight: 600, color: isDarkMode ? "#f8fafc" : "#1e293b", maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  📄 {file.name}
                </span>
                <button
                  type="button"
                  onClick={() => handleRemoveFile(file.name)}
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
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.md"
          style={{ display: "none" }}
          onChange={(e) => handleFileUpload(e.target.files)}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          style={{
            padding: "8px 16px",
            fontSize: "13px",
            fontWeight: 600,
            borderRadius: "8px",
            border: isDarkMode ? "1px dashed rgba(255,255,255,0.2)" : "1px dashed #cbd5e1",
            background: isDarkMode ? "rgba(255,255,255,0.05)" : "#ffffff",
            color: isDarkMode ? "#94a3b8" : "#475569",
            cursor: uploading ? "not-allowed" : "pointer",
            width: "100%",
            transition: "all 0.15s ease",
          }}
        >
          {uploading ? "⏳ Uploading..." : "+ Upload docs / PDF / tender files"}
        </button>
      </div>

      {/* Document Config Row */}
      <div
        style={{
          display: "flex",
          gap: "14px",
          marginBottom: "16px",
          flexWrap: "wrap",
        }}
      >
        <div style={{ flex: 1, minWidth: "140px" }}>
          <label style={{ display: "block", fontSize: "11px", fontWeight: 600, marginBottom: "4px", color: isDarkMode ? "#cbd5e1" : "#475569" }}>
            Pages
          </label>
          <select
            value={numPages}
            onChange={(e) => setNumPages(Number(e.target.value))}
            style={{
              width: "100%",
              padding: "8px 10px",
              fontSize: "13px",
              borderRadius: "8px",
              border: isDarkMode ? "1px solid rgba(255,255,255,0.15)" : "1px solid #cbd5e1",
              background: isDarkMode ? "rgba(255,255,255,0.05)" : "#ffffff",
              color: isDarkMode ? "#f8fafc" : "#1e293b",
            }}
          >
            {[3, 4, 5, 6, 7, 8, 10, 12, 15].map((n) => (
              <option key={n} value={n}>{n} pages</option>
            ))}
          </select>
        </div>
        <div style={{ flex: 1, minWidth: "140px" }}>
          <label style={{ display: "block", fontSize: "11px", fontWeight: 600, marginBottom: "4px", color: isDarkMode ? "#cbd5e1" : "#475569" }}>
            Content Density
          </label>
          <select
            value={contentDensity}
            onChange={(e) => setContentDensity(e.target.value as "min" | "med" | "max")}
            style={{
              width: "100%",
              padding: "8px 10px",
              fontSize: "13px",
              borderRadius: "8px",
              border: isDarkMode ? "1px solid rgba(255,255,255,0.15)" : "1px solid #cbd5e1",
              background: isDarkMode ? "rgba(255,255,255,0.05)" : "#ffffff",
              color: isDarkMode ? "#f8fafc" : "#1e293b",
            }}
          >
            <option value="min">Concise</option>
            <option value="med">Standard</option>
            <option value="max">Comprehensive</option>
          </select>
        </div>
      </div>

      {/* Optional Parameters Accordion */}
      <div
        style={{
          borderRadius: "12px",
          border: isDarkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid #e2e8f0",
          overflow: "hidden",
          marginBottom: "20px",
        }}
      >
        <button
          type="button"
          onClick={() => setShowParams(!showParams)}
          style={{
            width: "100%",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "10px 14px",
            background: isDarkMode ? "rgba(59, 130, 246, 0.08)" : "#eff6ff",
            border: "none",
            cursor: "pointer",
            textAlign: "left",
          }}
        >
          <span style={{ fontSize: "12px", fontWeight: 600, color: isDarkMode ? "#93c5fd" : "#1d4ed8" }}>
            🎯 Key Parameters (Optional — Buyer, Vendor, Budget, Timeline)
          </span>
          <span style={{ fontSize: "12px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
            {showParams ? "▲" : "▼"}
          </span>
        </button>

        {showParams && (
          <div style={{ padding: "14px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 600, marginBottom: "3px", color: isDarkMode ? "#cbd5e1" : "#475569" }}>Buyer / Organization</label>
              <input
                type="text"
                value={buyerName}
                onChange={(e) => setBuyerName(e.target.value)}
                placeholder="e.g. Acme Corp"
                style={{
                  width: "100%",
                  padding: "7px 10px",
                  fontSize: "12px",
                  borderRadius: "6px",
                  border: isDarkMode ? "1px solid rgba(255,255,255,0.15)" : "1px solid #cbd5e1",
                  background: isDarkMode ? "rgba(255,255,255,0.05)" : "#ffffff",
                  color: isDarkMode ? "#f8fafc" : "#1e293b",
                  boxSizing: "border-box",
                }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 600, marginBottom: "3px", color: isDarkMode ? "#cbd5e1" : "#475569" }}>Vendor Name</label>
              <input
                type="text"
                value={vendorName}
                onChange={(e) => setVendorName(e.target.value)}
                placeholder="e.g. CloudTech Solutions"
                style={{
                  width: "100%",
                  padding: "7px 10px",
                  fontSize: "12px",
                  borderRadius: "6px",
                  border: isDarkMode ? "1px solid rgba(255,255,255,0.15)" : "1px solid #cbd5e1",
                  background: isDarkMode ? "rgba(255,255,255,0.05)" : "#ffffff",
                  color: isDarkMode ? "#f8fafc" : "#1e293b",
                  boxSizing: "border-box",
                }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 600, marginBottom: "3px", color: isDarkMode ? "#cbd5e1" : "#475569" }}>Budget Estimate</label>
              <input
                type="text"
                value={budgetEstimate}
                onChange={(e) => setBudgetEstimate(e.target.value)}
                placeholder="e.g. $250,000"
                style={{
                  width: "100%",
                  padding: "7px 10px",
                  fontSize: "12px",
                  borderRadius: "6px",
                  border: isDarkMode ? "1px solid rgba(255,255,255,0.15)" : "1px solid #cbd5e1",
                  background: isDarkMode ? "rgba(255,255,255,0.05)" : "#ffffff",
                  color: isDarkMode ? "#f8fafc" : "#1e293b",
                  boxSizing: "border-box",
                }}
              />
            </div>
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 600, marginBottom: "3px", color: isDarkMode ? "#cbd5e1" : "#475569" }}>Delivery Timeline</label>
              <input
                type="text"
                value={deliveryTimeline}
                onChange={(e) => setDeliveryTimeline(e.target.value)}
                placeholder="e.g. 6 months"
                style={{
                  width: "100%",
                  padding: "7px 10px",
                  fontSize: "12px",
                  borderRadius: "6px",
                  border: isDarkMode ? "1px solid rgba(255,255,255,0.15)" : "1px solid #cbd5e1",
                  background: isDarkMode ? "rgba(255,255,255,0.05)" : "#ffffff",
                  color: isDarkMode ? "#f8fafc" : "#1e293b",
                  boxSizing: "border-box",
                }}
              />
            </div>
          </div>
        )}
      </div>

      {error && <p className="error-text" style={{ marginBottom: "12px" }}>{error}</p>}

      {/* Action buttons */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <button
          type="button"
          className="secondary-button"
          onClick={() => setStep("templates")}
          style={{ padding: "10px 20px" }}
        >
          ← Back
        </button>

        <button
          type="button"
          className="primary-button"
          onClick={handleGenerate}
          style={{
            padding: "12px 32px",
            fontSize: "15px",
            fontWeight: 700,
            background: "linear-gradient(135deg, #2563eb, #1d4ed8)",
            boxShadow: "0 4px 14px rgba(37, 99, 235, 0.35)",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          🚀 Generate Document
        </button>
      </div>
    </div>
  );
}
