import { useState } from "react";
import { createPortal } from "react-dom";
import { useWizardStore } from "../../state/wizardStore";

interface FindReplaceModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function FindReplaceModal({ isOpen, onClose }: FindReplaceModalProps) {
  const isDarkMode = useWizardStore((s) => s.isDarkMode);
  const activeEditor = useWizardStore((s) => s.activeEditor);

  const [findText, setFindText] = useState("");
  const [replaceText, setReplaceText] = useState("");
  const [matchCase, setMatchCase] = useState(false);
  const [matchesCount, setMatchesCount] = useState<number | null>(null);

  if (!isOpen) return null;

  function handleFind() {
    if (!findText.trim() || !activeEditor) return;
    const content = activeEditor.getText();
    const regex = new RegExp(findText, matchCase ? "g" : "gi");
    const matches = content.match(regex);
    setMatchesCount(matches ? matches.length : 0);
  }

  function handleReplace() {
    if (!findText.trim() || !activeEditor) return;
    const content = activeEditor.getHTML();
    const regex = new RegExp(findText, matchCase ? "g" : "gi");
    const updated = content.replace(regex, replaceText);
    activeEditor.commands.setContent(updated);
    handleFind();
  }

  return createPortal(
    <div
      style={{
        position: "fixed",
        top: "100px",
        right: "24px",
        background: isDarkMode ? "#18181b" : "#ffffff",
        color: isDarkMode ? "#ffffff" : "#1f2937",
        border: isDarkMode ? "1px solid #27272a" : "1px solid #e5e7eb",
        borderRadius: "10px",
        width: "360px",
        padding: "18px",
        boxShadow: "0 10px 30px rgba(0, 0, 0, 0.4)",
        zIndex: 999999,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <h4 style={{ margin: 0, fontSize: "15px", fontWeight: 700 }}>🔍 Find and Replace</h4>
        <button onClick={onClose} style={{ background: "none", border: "none", color: isDarkMode ? "#aaa" : "#666", cursor: "pointer" }}>✕</button>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "13px" }}>
        <div>
          <label style={{ fontWeight: 600 }}>Find:</label>
          <input
            type="text"
            value={findText}
            onChange={(e) => setFindText(e.target.value)}
            placeholder="Type text to search..."
            style={{
              width: "100%",
              padding: "6px 10px",
              marginTop: "4px",
              borderRadius: "6px",
              border: isDarkMode ? "1px solid #3f3f46" : "1px solid #d1d5db",
              background: isDarkMode ? "#27272a" : "#f9fafb",
              color: isDarkMode ? "#ffffff" : "#111827",
              boxSizing: "border-box",
            }}
          />
        </div>

        <div>
          <label style={{ fontWeight: 600 }}>Replace with:</label>
          <input
            type="text"
            value={replaceText}
            onChange={(e) => setReplaceText(e.target.value)}
            placeholder="Replacement text..."
            style={{
              width: "100%",
              padding: "6px 10px",
              marginTop: "4px",
              borderRadius: "6px",
              border: isDarkMode ? "1px solid #3f3f46" : "1px solid #d1d5db",
              background: isDarkMode ? "#27272a" : "#f9fafb",
              color: isDarkMode ? "#ffffff" : "#111827",
              boxSizing: "border-box",
            }}
          />
        </div>

        <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
          <input type="checkbox" checked={matchCase} onChange={(e) => setMatchCase(e.target.checked)} />
          <span>Match case</span>
        </label>

        {matchesCount !== null && (
          <div style={{ fontSize: "12px", color: matchesCount > 0 ? "#16a34a" : "#dc2626", fontWeight: 600 }}>
            {matchesCount > 0 ? `Found ${matchesCount} match(es)` : "No matches found"}
          </div>
        )}

        <div style={{ display: "flex", gap: "8px", marginTop: "10px" }}>
          <button
            onClick={handleFind}
            style={{
              flex: 1,
              padding: "6px 12px",
              borderRadius: "6px",
              border: isDarkMode ? "1px solid #3f3f46" : "1px solid #d1d5db",
              background: isDarkMode ? "#27272a" : "#f3f4f6",
              color: isDarkMode ? "#ffffff" : "#374151",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Find Next
          </button>
          <button
            onClick={handleReplace}
            style={{
              flex: 1,
              padding: "6px 12px",
              borderRadius: "6px",
              border: "none",
              background: "#2563eb",
              color: "#ffffff",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Replace All
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
