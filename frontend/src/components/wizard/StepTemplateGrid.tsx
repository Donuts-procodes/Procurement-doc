import { useState } from "react";
import { useWizardStore } from "../../state/wizardStore";
import {
  PREBUILT_TEMPLATES_LIST,
  type ProcurementDocType,
  type TemplateDefinition,
} from "../../types";

const CATEGORY_TABS: { id: string; label: string }[] = [
  { id: "ALL", label: "All" },
  { id: "RFP", label: "RFP" },
  { id: "RFQ", label: "RFQ" },
  { id: "RFI", label: "RFI" },
  { id: "SOW", label: "SOW" },
  { id: "VENDOR_CONTRACT", label: "Contracts" },
  { id: "VENDOR_SCORECARD", label: "Scorecards" },
  { id: "PURCHASE_ORDER", label: "PO" },
  { id: "CUSTOM", label: "Custom" },
];

export function StepTemplateGrid() {
  const storeTemplateId = useWizardStore((s) => s.templateId);
  const setStep = useWizardStore((s) => s.setStep);
  const isDarkMode = useWizardStore((s) => s.isDarkMode);

  const [activeTab, setActiveTab] = useState<string>("ALL");
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>(storeTemplateId || "rfp_enterprise");

  const filteredTemplates =
    activeTab === "ALL"
      ? PREBUILT_TEMPLATES_LIST
      : PREBUILT_TEMPLATES_LIST.filter((t) => t.category === activeTab);

  const selectedTemplate = PREBUILT_TEMPLATES_LIST.find((t) => t.id === selectedTemplateId) || PREBUILT_TEMPLATES_LIST[0];

  function handleSelect(tmpl: TemplateDefinition) {
    setSelectedTemplateId(tmpl.id);
    useWizardStore.setState({
      templateId: tmpl.id,
      procurementDocType: (tmpl.category === "ALL" || tmpl.category === "CUSTOM" ? "RFP" : tmpl.category) as ProcurementDocType,
    });
  }

  function handleNext() {
    useWizardStore.setState({
      templateId: selectedTemplateId,
      procurementDocType: (selectedTemplate.category === "ALL" || selectedTemplate.category === "CUSTOM" ? "RFP" : selectedTemplate.category) as ProcurementDocType,
    });
    setStep("prompt-intake");
  }

  return (
    <div className="wizard-step" style={{ maxWidth: "100%" }}>
      <h2 style={{ color: isDarkMode ? "#f8fafc" : "#0f172a" }}>
        Choose a Document Template
      </h2>
      <p className="wizard-step__subtitle" style={{ color: isDarkMode ? "#94a3b8" : "#64748b", marginBottom: "20px" }}>
        Select the procurement document type you want to generate. You'll provide details in the next step.
      </p>

      {/* Category Filter Tabs */}
      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginBottom: "20px" }}>
        {CATEGORY_TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: "6px 14px",
                fontSize: "12px",
                fontWeight: 600,
                borderRadius: "8px",
                border: "1px solid",
                borderColor: isActive
                  ? isDarkMode ? "#3b82f6" : "#1a73e8"
                  : isDarkMode ? "rgba(255,255,255,0.15)" : "#e2e8f0",
                background: isActive
                  ? isDarkMode ? "rgba(59, 130, 246, 0.2)" : "#e8f0fe"
                  : isDarkMode ? "rgba(255,255,255,0.03)" : "#f8fafc",
                color: isActive
                  ? isDarkMode ? "#60a5fa" : "#1a73e8"
                  : isDarkMode ? "#94a3b8" : "#64748b",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Template Cards Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
          gap: "14px",
          maxHeight: "520px",
          overflowY: "auto",
          paddingRight: "6px",
          marginBottom: "24px",
        }}
      >
        {filteredTemplates.map((tmpl) => {
          const isSelected = selectedTemplateId === tmpl.id;
          return (
            <div
              key={tmpl.id}
              onClick={() => handleSelect(tmpl)}
              style={{
                padding: "18px",
                borderRadius: "12px",
                border: isSelected
                  ? isDarkMode ? "2px solid #3b82f6" : "2px solid #1a73e8"
                  : isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid #e2e8f0",
                background: isSelected
                  ? isDarkMode ? "rgba(59, 130, 246, 0.15)" : "rgba(232, 240, 254, 0.8)"
                  : isDarkMode ? "rgba(255,255,255,0.03)" : "#ffffff",
                boxShadow: isSelected
                  ? isDarkMode ? "0 4px 14px rgba(59, 130, 246, 0.2)" : "0 4px 14px rgba(26, 115, 232, 0.15)"
                  : "0 1px 3px rgba(0,0,0,0.03)",
                cursor: "pointer",
                transition: "all 0.2s ease",
                position: "relative",
              }}
            >
              {isSelected && (
                <span
                  style={{
                    position: "absolute",
                    top: "10px",
                    right: "10px",
                    background: isDarkMode ? "#3b82f6" : "#1a73e8",
                    color: "#fff",
                    borderRadius: "50%",
                    width: "22px",
                    height: "22px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "12px",
                    fontWeight: 700,
                  }}
                >
                  ✓
                </span>
              )}

              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                <span style={{ fontSize: "28px" }}>{tmpl.icon}</span>
                <div>
                  <div style={{ fontSize: "14px", fontWeight: 700, color: isDarkMode ? "#f8fafc" : "#1e293b" }}>
                    {tmpl.title}
                  </div>
                  <span
                    style={{
                      fontSize: "10px",
                      fontWeight: 700,
                      padding: "2px 6px",
                      borderRadius: "4px",
                      background: isDarkMode ? "rgba(59, 130, 246, 0.15)" : "#eff6ff",
                      color: isDarkMode ? "#60a5fa" : "#1d4ed8",
                      marginTop: "2px",
                      display: "inline-block",
                    }}
                  >
                    {tmpl.category}
                  </span>
                </div>
              </div>

              <p style={{ fontSize: "12px", color: isDarkMode ? "#94a3b8" : "#64748b", margin: "0 0 8px 0", lineHeight: 1.4 }}>
                {tmpl.description}
              </p>

              <div style={{ fontSize: "11px", color: isDarkMode ? "#64748b" : "#94a3b8" }}>
                {tmpl.sections.length} sections • {tmpl.tone}
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected template summary + Next button */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "16px 20px",
          borderRadius: "12px",
          background: isDarkMode ? "rgba(59, 130, 246, 0.1)" : "#eff6ff",
          border: isDarkMode ? "1px solid rgba(59, 130, 246, 0.2)" : "1px solid #bfdbfe",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "24px" }}>{selectedTemplate.icon}</span>
          <div>
            <div style={{ fontSize: "14px", fontWeight: 700, color: isDarkMode ? "#f8fafc" : "#1e293b" }}>
              {selectedTemplate.title}
            </div>
            <div style={{ fontSize: "11px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
              {selectedTemplate.sections.length} sections • {selectedTemplate.toneDescription}
            </div>
          </div>
        </div>

        <button
          type="button"
          className="primary-button"
          onClick={handleNext}
          style={{
            padding: "10px 28px",
            fontSize: "14px",
            fontWeight: 700,
            borderRadius: "10px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          Next →
        </button>
      </div>
    </div>
  );
}
