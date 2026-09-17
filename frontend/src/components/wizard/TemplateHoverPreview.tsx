import { type TemplateDefinition } from "../../types";

interface TemplateHoverPreviewProps {
  template: TemplateDefinition;
  isDarkMode: boolean;
  position: { x: number; y: number };
}

export function TemplateHoverPreview({
  template,
  isDarkMode,
  position,
}: TemplateHoverPreviewProps) {
  // Clamp window within browser viewport
  const popoverWidth = 360;
  const popoverHeight = 440;
  const padding = 16;

  let left = position.x + 20;
  if (left + popoverWidth > window.innerWidth - padding) {
    left = position.x - popoverWidth - 20;
  }
  if (left < padding) left = padding;

  let top = position.y - 120;
  if (top + popoverHeight > window.innerHeight - padding) {
    top = window.innerHeight - popoverHeight - padding;
  }
  if (top < padding) top = padding;

  return (
    <div
      style={{
        position: "fixed",
        left: `${left}px`,
        top: `${top}px`,
        width: `${popoverWidth}px`,
        maxHeight: `${popoverHeight}px`,
        zIndex: 99999,
        pointerEvents: "none",
        borderRadius: "14px",
        overflow: "hidden",
        boxShadow: isDarkMode
          ? "0 20px 40px -10px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.12)"
          : "0 20px 40px -10px rgba(15,23,42,0.25), 0 0 0 1px rgba(0,0,0,0.08)",
        background: isDarkMode ? "#1e293b" : "#ffffff",
        animation: "previewFadeIn 0.15s cubic-bezier(0.16, 1, 0.3, 1)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Header with Title & Tone Badge */}
      <div
        style={{
          padding: "14px 16px",
          background: isDarkMode
            ? "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)"
            : "linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)",
          borderBottom: isDarkMode
            ? "1px solid rgba(255,255,255,0.08)"
            : "1px solid rgba(0,0,0,0.06)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
          <span style={{ fontSize: "11px", fontWeight: 700, color: "#3b82f6", letterSpacing: "0.5px", textTransform: "uppercase" }}>
            Live Document Wireframe
          </span>
          <span
            style={{
              fontSize: "10px",
              fontWeight: 600,
              padding: "2px 8px",
              borderRadius: "10px",
              background: isDarkMode ? "rgba(59,130,246,0.2)" : "#dbeafe",
              color: isDarkMode ? "#93c5fd" : "#1d4ed8",
            }}
          >
            {template.category}
          </span>
        </div>
        <div style={{ fontSize: "14px", fontWeight: 700, color: isDarkMode ? "#f8fafc" : "#0f172a" }}>
          {template.title}
        </div>
        <div style={{ fontSize: "11px", color: isDarkMode ? "#94a3b8" : "#64748b", marginTop: "2px" }}>
          Tone: {template.tone}
        </div>
      </div>

      {/* Simulated Document Sheet (Mini Canvas Viewport) */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px",
          background: isDarkMode ? "#0b0f17" : "#f1f5f9",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
        }}
      >
        {/* Paper Sheet Container */}
        <div
          style={{
            background: isDarkMode ? "#1e293b" : "#ffffff",
            padding: "14px 16px",
            borderRadius: "6px",
            boxShadow: isDarkMode
              ? "0 2px 6px rgba(0,0,0,0.5)"
              : "0 2px 8px rgba(0,0,0,0.06)",
            border: isDarkMode ? "1px solid rgba(255,255,255,0.05)" : "1px solid #e2e8f0",
          }}
        >
          {/* Document Cover / Watermark Header */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", borderBottom: "2px solid #3b82f6", paddingBottom: "8px", marginBottom: "12px" }}>
            <span style={{ fontSize: "16px" }}>{template.icon}</span>
            <div style={{ fontSize: "12px", fontWeight: 800, color: isDarkMode ? "#f8fafc" : "#0f172a" }}>
              {template.title}
            </div>
          </div>

          {/* Section Skeletons */}
          {template.sections.slice(0, 5).map((sec, idx) => (
            <div key={idx} style={{ marginBottom: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                <span style={{ fontSize: "11px", fontWeight: 700, color: isDarkMode ? "#cbd5e1" : "#334155" }}>
                  {idx + 1}. {sec.title}
                </span>
                <span
                  style={{
                    fontSize: "9px",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    padding: "1px 5px",
                    borderRadius: "4px",
                    background: sec.section_type === "line_items"
                      ? isDarkMode ? "rgba(16,185,129,0.2)" : "#d1fae5"
                      : sec.section_type === "payment_schedule"
                      ? isDarkMode ? "rgba(245,158,11,0.2)" : "#fef3c7"
                      : sec.section_type === "clause"
                      ? isDarkMode ? "rgba(239,68,68,0.2)" : "#fee2e2"
                      : isDarkMode ? "rgba(255,255,255,0.08)" : "#e2e8f0",
                    color: sec.section_type === "line_items"
                      ? "#10b981"
                      : sec.section_type === "payment_schedule"
                      ? "#f59e0b"
                      : sec.section_type === "clause"
                      ? "#ef4444"
                      : isDarkMode ? "#94a3b8" : "#64748b",
                  }}
                >
                  {sec.section_type.replace("_", " ")}
                </span>
              </div>

              {sec.section_type === "line_items" ? (
                <div
                  style={{
                    border: isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid #e2e8f0",
                    borderRadius: "4px",
                    fontSize: "9px",
                    padding: "6px 8px",
                    background: isDarkMode ? "rgba(0,0,0,0.2)" : "#f8fafc",
                    color: isDarkMode ? "#94a3b8" : "#64748b",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 700, borderBottom: "1px solid #cbd5e1", paddingBottom: "2px" }}>
                    <span>Item / SKU</span>
                    <span>Qty</span>
                    <span>Unit Cost</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", paddingTop: "3px" }}>
                    <span>Enterprise License</span>
                    <span>1</span>
                    <span>$25,000</span>
                  </div>
                </div>
              ) : sec.section_type === "payment_schedule" ? (
                <div
                  style={{
                    fontSize: "9px",
                    padding: "6px 8px",
                    borderRadius: "4px",
                    background: isDarkMode ? "rgba(245,158,11,0.1)" : "#fffbeb",
                    borderLeft: "3px solid #f59e0b",
                    color: isDarkMode ? "#fde68a" : "#b45309",
                  }}
                >
                  Milestones: 25% Upfront • 50% Delivery • 25% Sign-off
                </div>
              ) : sec.section_type === "clause" ? (
                <div
                  style={{
                    fontSize: "9px",
                    padding: "6px 8px",
                    borderRadius: "4px",
                    background: isDarkMode ? "rgba(239,68,68,0.1)" : "#fef2f2",
                    borderLeft: "3px solid #ef4444",
                    color: isDarkMode ? "#fca5a5" : "#b91c1c",
                  }}
                >
                  🔒 Mandatory Legal & Compliance Warranty Clause
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
                  <div style={{ height: "4px", width: "90%", borderRadius: "2px", background: isDarkMode ? "rgba(255,255,255,0.12)" : "#e2e8f0" }} />
                  <div style={{ height: "4px", width: "75%", borderRadius: "2px", background: isDarkMode ? "rgba(255,255,255,0.08)" : "#f1f5f9" }} />
                </div>
              )}
            </div>
          ))}

          {template.sections.length > 5 && (
            <div style={{ textAlign: "center", fontSize: "10px", color: isDarkMode ? "#64748b" : "#94a3b8", fontStyle: "italic" }}>
              + {template.sections.length - 5} additional dynamic sections
            </div>
          )}
        </div>
      </div>

      {/* Footer Meta */}
      <div
        style={{
          padding: "8px 16px",
          background: isDarkMode ? "#0f172a" : "#f8fafc",
          borderTop: isDarkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(0,0,0,0.06)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "10px",
          color: isDarkMode ? "#94a3b8" : "#64748b",
        }}
      >
        <span>📄 {template.sections.length} Target Sections</span>
        <span>✨ Auto-grounded with Citations</span>
      </div>
    </div>
  );
}
