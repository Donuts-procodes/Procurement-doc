import { useState, useEffect, useRef } from "react";
import type { Editor } from "@tiptap/react";
import { streamTargetedSelectionEdit } from "../../api/client";
import { useWizardStore } from "../../state/wizardStore";
import type { StreamEvent } from "../../types";

interface InlineFloatingToolbarProps {
  editor: Editor | null;
  segmentId: string;
}

export function InlineFloatingToolbar({ editor, segmentId }: InlineFloatingToolbarProps) {
  const [coords, setCoords] = useState<{ top: number; left: number } | null>(null);
  const [selectedText, setSelectedText] = useState("");
  const [range, setRange] = useState<{ from: number; to: number } | null>(null);
  const [prompt, setPrompt] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!editor) return;

    const handleSelectionUpdate = () => {
      const { from, to, empty } = editor.state.selection;
      if (empty || from === to) {
        if (!isStreaming && !isExpanded) {
          setCoords(null);
          setSelectedText("");
          setRange(null);
        }
        return;
      }

      const text = editor.state.doc.textBetween(from, to, " ");
      if (!text.trim() || text.length < 2) {
        if (!isStreaming && !isExpanded) {
          setCoords(null);
        }
        return;
      }

      setSelectedText(text);
      setRange({ from, to });

      const startPos = editor.view.coordsAtPos(from);
      const endPos = editor.view.coordsAtPos(to);

      // Center above selection
      const left = (startPos.left + endPos.right) / 2;
      const top = startPos.top - 10;

      setCoords({ top, left });
    };

    editor.on("selectionUpdate", handleSelectionUpdate);
    return () => {
      editor.off("selectionUpdate", handleSelectionUpdate);
    };
  }, [editor, isStreaming, isExpanded]);

  if (!coords || !editor || !range) return null;

  async function handleApplyEdit(overridePrompt?: string) {
    const editInstruction = overridePrompt || prompt;
    if (!editInstruction.trim() || !range || !editor) return;

    setIsStreaming(true);

    const docText = editor.getText();
    const contextWindow = docText.slice(Math.max(0, range.from - 200), Math.min(docText.length, range.to + 200));
    const sessionId = useWizardStore.getState().sessionId || `session_${Date.now()}`;

    await streamTargetedSelectionEdit(
      {
        session_id: sessionId,
        prompt: editInstruction,
        target_node_id: segmentId,
        selection_text: selectedText,
        context_window: contextWindow,
      },
      (event: StreamEvent) => {
        if (event.type === "canvas_patch" && event.operation === "replace_range") {
          const content = typeof event.content === "string" ? event.content : JSON.stringify(event.content);
          editor.commands.insertContentAt({ from: range.from, to: range.to }, content);
          // Update the to-range to match new replacement length
          const newTo = range.from + content.length;
          setRange({ from: range.from, to: newTo });
        }
      },
      (err: any) => {
        console.error("Targeted selection edit failed:", err);
        setIsStreaming(false);
      },
      () => {
        setIsStreaming(false);
        setIsExpanded(false);
        setPrompt("");
        setCoords(null);
      }
    );
  }

  const QUICK_ACTIONS = [
    { label: "✨ Polish & Formalize", prompt: "Make this wording more formal, precise, and executive-ready." },
    { label: "📉 Shorten & Condense", prompt: "Condense this text directly into concise bullet points or a short paragraph." },
    { label: "⚖️ Strict Compliance", prompt: "Reword this clause to emphasize mandatory procurement compliance and risk mitigation." },
  ];

  return (
    <div
      ref={menuRef}
      className="inline-floating-ai-toolbar"
      style={{
        position: "fixed",
        top: `${coords.top}px`,
        left: `${coords.left}px`,
        transform: "translate(-50%, -100%)",
        zIndex: 99999,
        background: "#1e293b",
        color: "#ffffff",
        borderRadius: "8px",
        padding: "6px 8px",
        display: "flex",
        flexDirection: "column",
        gap: "6px",
        boxShadow: "0 10px 25px rgba(0,0,0,0.35)",
        border: "1px solid #334155",
        minWidth: isExpanded ? "320px" : "auto",
        animation: "fadeIn 0.15s ease",
      }}
      onClick={(e) => e.stopPropagation()}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
        <button
          style={{
            background: "#0284c7",
            color: "#ffffff",
            border: "none",
            borderRadius: "4px",
            padding: "4px 8px",
            fontSize: "12px",
            fontWeight: 600,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "4px",
          }}
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <span>✨ AI Edit</span>
        </button>

        {!isExpanded && (
          <div style={{ display: "flex", gap: "4px" }}>
            {QUICK_ACTIONS.map((action, i) => (
              <button
                key={i}
                disabled={isStreaming}
                style={{
                  background: "#334155",
                  color: "#f8fafc",
                  border: "none",
                  borderRadius: "4px",
                  padding: "4px 6px",
                  fontSize: "11px",
                  cursor: isStreaming ? "not-allowed" : "pointer",
                  whiteSpace: "nowrap",
                }}
                onClick={() => handleApplyEdit(action.prompt)}
              >
                {action.label}
              </button>
            ))}
          </div>
        )}

        <button
          style={{
            background: "transparent",
            border: "none",
            color: "#94a3b8",
            cursor: "pointer",
            fontSize: "13px",
            padding: "2px 4px",
          }}
          onClick={() => {
            setCoords(null);
            setIsExpanded(false);
          }}
        >
          ✕
        </button>
      </div>

      {isExpanded && (
        <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "2px" }}>
          <div style={{ display: "flex", gap: "4px" }}>
            <input
              type="text"
              value={prompt}
              placeholder="E.g., Rewrite to emphasize net 30 payment terms..."
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleApplyEdit();
                }
              }}
              disabled={isStreaming}
              style={{
                flex: 1,
                background: "#0f172a",
                border: "1px solid #475569",
                borderRadius: "4px",
                color: "#ffffff",
                padding: "5px 8px",
                fontSize: "12px",
                outline: "none",
              }}
              autoFocus
            />
            <button
              disabled={isStreaming || !prompt.trim()}
              onClick={() => handleApplyEdit()}
              style={{
                background: isStreaming ? "#475569" : "#38bdf8",
                color: isStreaming ? "#94a3b8" : "#0f172a",
                border: "none",
                borderRadius: "4px",
                padding: "5px 10px",
                fontSize: "12px",
                fontWeight: 700,
                cursor: isStreaming || !prompt.trim() ? "not-allowed" : "pointer",
              }}
            >
              {isStreaming ? "Patching..." : "Apply"}
            </button>
          </div>

          <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
            {QUICK_ACTIONS.map((action, i) => (
              <button
                key={i}
                disabled={isStreaming}
                style={{
                  background: "#334155",
                  color: "#e2e8f0",
                  border: "none",
                  borderRadius: "3px",
                  padding: "3px 6px",
                  fontSize: "10px",
                  cursor: isStreaming ? "not-allowed" : "pointer",
                }}
                onClick={() => handleApplyEdit(action.prompt)}
              >
                {action.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
