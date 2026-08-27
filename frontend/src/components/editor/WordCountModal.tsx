import { useWizardStore } from "../../state/wizardStore";

interface WordCountModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function WordCountModal({ isOpen, onClose }: WordCountModalProps) {
  const isDarkMode = useWizardStore((s) => s.isDarkMode);
  const segments = useWizardStore((s) => s.segments);

  if (!isOpen) return null;

  const fullText = segments.map((s) => (typeof s.content === "string" ? s.content : JSON.stringify(s.content || ""))).join(" ");
  const totalWords = fullText.trim() ? fullText.trim().split(/\s+/).length : 0;
  const totalChars = fullText.length;
  const totalCharsNoSpace = fullText.replace(/\s+/g, "").length;
  const totalPages = segments.length || 1;
  const readingTimeMinutes = Math.ceil(totalWords / 200);

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: "rgba(0, 0, 0, 0.6)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: isDarkMode ? "#18181b" : "#ffffff",
          color: isDarkMode ? "#ffffff" : "#1f2937",
          border: isDarkMode ? "1px solid #27272a" : "1px solid #e5e7eb",
          borderRadius: "12px",
          width: "380px",
          padding: "24px",
          boxShadow: "0 20px 45px rgba(0, 0, 0, 0.4)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 700 }}>📊 Word Count & Metrics</h3>
          <button onClick={onClose} style={{ background: "none", border: "none", color: isDarkMode ? "#aaa" : "#666", cursor: "pointer", fontSize: "18px" }}>✕</button>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "12px", fontSize: "14px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: isDarkMode ? "1px solid #27272a" : "1px solid #f3f4f6", paddingBottom: "8px" }}>
            <span>Pages</span>
            <strong>{totalPages}</strong>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: isDarkMode ? "1px solid #27272a" : "1px solid #f3f4f6", paddingBottom: "8px" }}>
            <span>Words</span>
            <strong>{totalWords}</strong>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: isDarkMode ? "1px solid #27272a" : "1px solid #f3f4f6", paddingBottom: "8px" }}>
            <span>Characters</span>
            <strong>{totalChars}</strong>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: isDarkMode ? "1px solid #27272a" : "1px solid #f3f4f6", paddingBottom: "8px" }}>
            <span>Characters (no spaces)</span>
            <strong>{totalCharsNoSpace}</strong>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", borderBottom: isDarkMode ? "1px solid #27272a" : "1px solid #f3f4f6", paddingBottom: "8px" }}>
            <span>Estimated Reading Time</span>
            <strong>~{readingTimeMinutes} min</strong>
          </div>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "20px" }}>
          <button
            onClick={onClose}
            style={{
              padding: "8px 18px",
              borderRadius: "6px",
              border: "none",
              background: "#2563eb",
              color: "#ffffff",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
