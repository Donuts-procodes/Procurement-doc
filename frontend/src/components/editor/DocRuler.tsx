import { useWizardStore } from "../../state/wizardStore";

export function DocRuler() {
  const isDarkMode = useWizardStore((s) => s.isDarkMode);
  const pageLayoutSize = useWizardStore((s) => s.pageLayoutSize);

  const sizeUpper = (pageLayoutSize || "A4").toUpperCase();
  let rulerWidth = "794px";
  if (sizeUpper === "LETTER" || sizeUpper === "LEGAL") rulerWidth = "816px";
  if (sizeUpper === "A3") rulerWidth = "1123px";

  const inches = [0, 1, 2, 3, 4, 5, 6, 7];

  return (
    <div
      className="doc-ruler"
      style={{
        width: rulerWidth,
        height: "22px",
        margin: "0 auto 8px auto",
        background: isDarkMode ? "#1e293b" : "#f1f5f9",
        border: isDarkMode ? "1px solid #334155" : "1px solid #cbd5e1",
        borderRadius: "4px 4px 0 0",
        position: "relative",
        boxSizing: "border-box",
        userSelect: "none",
        display: "flex",
        alignItems: "flex-end",
        padding: "0 56px", // Align with page margins padding (56px)
      }}
      title="Google Docs Ruler: 1-inch margin guides"
    >
      {/* Margin Indent Markers */}
      <div
        style={{
          position: "absolute",
          left: "54px",
          top: "2px",
          fontSize: "10px",
          color: "#2563eb",
          fontWeight: 700,
          cursor: "ew-resize",
        }}
        title="First Line Indent Marker"
      >
        ▼
      </div>

      <div
        style={{
          position: "absolute",
          right: "54px",
          top: "2px",
          fontSize: "10px",
          color: "#2563eb",
          fontWeight: 700,
          cursor: "ew-resize",
        }}
        title="Right Indent Marker"
      >
        ▼
      </div>

      {/* Scaled Inch Marks */}
      <div style={{ flex: 1, display: "flex", justifyContent: "space-between", alignItems: "flex-end", height: "100%" }}>
        {inches.map((inch) => (
          <div
            key={inch}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              height: "100%",
              justifyContent: "flex-end",
            }}
          >
            <span style={{ fontSize: "9px", color: isDarkMode ? "#94a3b8" : "#64748b", lineHeight: "1", marginBottom: "2px" }}>
              {inch}
            </span>
            <div style={{ width: "1px", height: "6px", background: isDarkMode ? "#64748b" : "#94a3b8" }} />
          </div>
        ))}
      </div>
    </div>
  );
}
