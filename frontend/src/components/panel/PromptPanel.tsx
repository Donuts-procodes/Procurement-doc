import { useState } from "react";
import { answerPendingQuestion, refineSegment, refineSelection } from "../../api/client";
import { useWizardStore } from "../../state/wizardStore";

interface PromptPanelProps {
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function PromptPanel({ isCollapsed, onToggleCollapse }: PromptPanelProps) {
  const {
    sessionId,
    documentId,
    model,
    selectedSegmentId,
    promptLog,
    activeEditor,
    isDarkMode,
    setStyleConfig,
    setPageLayoutSize,
    addPage,
    addChatMessage,
    updateSegment,
    setGeneratedDocument,
  } = useWizardStore((s) => ({
    sessionId: s.sessionId,
    documentId: s.documentId,
    model: s.model,
    selectedSegmentId: s.selectedSegmentId,
    promptLog: s.promptLog,
    activeEditor: s.activeEditor,
    isDarkMode: s.isDarkMode,
    setStyleConfig: s.setStyleConfig,
    setPageLayoutSize: s.setPageLayoutSize,
    addPage: s.addPage,
    addChatMessage: s.addChatMessage,
    updateSegment: s.updateSegment,
    setGeneratedDocument: s.setGeneratedDocument,
  }));

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [targetScope, setTargetScope] = useState<"selection" | "segment" | "global">("global");

  const selectedTextSnippet = activeEditor
    ? activeEditor.state.doc.textBetween(activeEditor.state.selection.from, activeEditor.state.selection.to)
    : "";

  async function handleSend() {
    if (!input.trim() || !sessionId) return;
    const userText = input.trim();
    setInput("");

    addChatMessage({
      id: String(Date.now()),
      sender: "user",
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    });

    setLoading(true);
    try {
      if (selectedTextSnippet && selectedTextSnippet.trim().length > 0) {
        const res = await refineSelection({
          session_id: sessionId,
          selection_text: selectedTextSnippet,
          instruction: userText,
          content_density: "med",
        });
        if (activeEditor && res.replacement_text) {
          activeEditor.chain().focus().insertContent(res.replacement_text).run();
        }
        addChatMessage({
          id: String(Date.now() + 1),
          sender: "assistant",
          text: `Surgically updated highlighted text to: "${res.replacement_text}"`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        });
      } else if (targetScope === "segment" && selectedSegmentId && documentId) {
        const res = await refineSegment({
          session_id: sessionId,
          document_id: documentId,
          segment_id: selectedSegmentId,
          instruction: userText,
          content_density: "med",
        });
        if (res.segment) {
          updateSegment(res.segment);
        }
        addChatMessage({
          id: String(Date.now() + 1),
          sender: "assistant",
          text: `Refined segment "${res.segment?.name || 'Page'}" cleanly!`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          segment_id: selectedSegmentId,
        });
      } else {
        const res = await answerPendingQuestion({
          session_id: sessionId,
          document_id: documentId || undefined,
          answer: userText,
          content_density: "med",
        });

        if ((res as any).ribbon_action) {
          const act = (res as any).ribbon_action;
          if (act.action_type === "set_font" && act.font_family) setStyleConfig({ fontFamily: act.font_family });
          else if (act.action_type === "set_font_size" && act.font_size) setStyleConfig({ fontSize: act.font_size });
          else if (act.action_type === "set_accent_color" && act.accent_color) setStyleConfig({ accentColor: act.accent_color });
          else if (act.action_type === "set_watermark" && act.watermark) setStyleConfig({ watermark: act.watermark });
          else if (act.action_type === "set_page_color" && act.page_color) setStyleConfig({ pageColor: act.page_color });
          else if (act.action_type === "set_page_border" && act.page_border) setStyleConfig({ pageBorder: act.page_border });
          else if (act.action_type === "set_paper_size" && act.paper_size) setPageLayoutSize(act.paper_size as any);
          else if (act.action_type === "set_spacing" && act.spacing) setStyleConfig({ paragraphSpacing: act.spacing });
          else if (act.action_type === "insert_table" && activeEditor) activeEditor.chain().focus().insertTable({ rows: act.table_rows || 3, cols: act.table_cols || 3, withHeaderRow: true }).run();
          else if (act.action_type === "add_page") addPage();
          else if (act.action_type === "clear_formatting" && activeEditor) activeEditor.chain().focus().unsetAllMarks().run();
        }

        if (res.segments && res.segments.length > 0) {
          setGeneratedDocument(
            res.document_id || documentId || "doc_current",
            res.lexical_state || {},
            res.page_titles || res.segments.map((s) => s.name),
            res.segments
          );
        }

        const replyMessage = res.chat_reply || (res.status === "ready" ? "Updated document segments cleanly!" : "Processed request cleanly.");

        addChatMessage({
          id: String(Date.now() + 1),
          sender: "assistant",
          text: replyMessage,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        });
      }
    } catch (err) {
      addChatMessage({
        id: String(Date.now() + 1),
        sender: "assistant",
        text: `Error: ${err instanceof Error ? err.message : "Failed to process prompt."}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      });
    } finally {
      setLoading(false);
    }
  }

  if (isCollapsed) {
    return (
      <aside
        className="prompt-panel prompt-panel--collapsed"
        style={{
          background: isDarkMode ? "rgba(18, 18, 18, 0.95)" : "rgba(255, 255, 255, 0.95)",
          border: isDarkMode ? "1px solid rgba(255, 255, 255, 0.1)" : "1px solid rgba(0, 0, 0, 0.1)",
          borderRadius: "12px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          padding: "16px 8px",
          cursor: "pointer",
        }}
        onClick={onToggleCollapse}
        title="Expand AI Co-Pilot Panel"
      >
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (onToggleCollapse) onToggleCollapse();
          }}
          style={{
            background: "transparent",
            border: "none",
            color: isDarkMode ? "#f8fafc" : "#1e293b",
            fontSize: "14px",
            cursor: "pointer",
            marginBottom: "12px",
          }}
        >
          ◀
        </button>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: "12px", color: isDarkMode ? "#60a5fa" : "#1a73e8" }}>
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <span style={{ writingMode: "vertical-rl", textTransform: "uppercase", fontSize: "11px", fontWeight: 700, letterSpacing: "1px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
          Help Bot
        </span>
      </aside>
    );
  }

  return (
    <aside
      className="prompt-panel"
      style={{
        background: isDarkMode ? "rgba(18, 18, 18, 0.95)" : "rgba(255, 255, 255, 0.8)",
        backdropFilter: "blur(12px)",
        border: isDarkMode ? "1px solid rgba(255, 255, 255, 0.1)" : "1px solid rgba(0, 0, 0, 0.08)",
        borderRadius: "12px",
        boxShadow: "0 4px 20px rgba(0, 0, 0, 0.05)",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        maxHeight: "100%",
        overflow: "hidden",
      }}
    >
      <div className="prompt-panel__header" style={{ padding: "14px 16px", borderBottom: isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid rgba(0, 0, 0, 0.05)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "15px", fontWeight: 700, display: "flex", alignItems: "center", gap: "8px", color: isDarkMode ? "#f8fafc" : "#1f2937" }}>
            ✨ AI Co-Pilot
          </h3>
          <div className="model-indicator" style={{ fontSize: "11px", color: isDarkMode ? "#94a3b8" : "#64748b", marginTop: "2px" }}>
            <span>Active Model:</span> <strong>{model || "gpt-4o"}</strong>
          </div>
        </div>
        {onToggleCollapse && (
          <button
            onClick={onToggleCollapse}
            style={{
              background: "transparent",
              border: "none",
              color: isDarkMode ? "#94a3b8" : "#64748b",
              fontSize: "14px",
              cursor: "pointer",
              padding: "4px 8px",
              borderRadius: "4px",
            }}
            title="Collapse Panel"
          >
            ▶
          </button>
        )}
      </div>

      {selectedTextSnippet && selectedTextSnippet.trim().length > 0 ? (
        <div style={{ padding: "6px 12px", background: isDarkMode ? "rgba(120, 53, 15, 0.4)" : "rgba(254, 243, 199, 0.7)", color: isDarkMode ? "#fde68a" : "#92400e", fontSize: "11px", fontWeight: 600, borderBottom: "1px solid rgba(253, 230, 138, 0.3)" }}>
          ✂️ Surgical Highlight: "<em>{selectedTextSnippet.slice(0, 26)}...</em>"
        </div>
      ) : (
        <div style={{ padding: "8px 12px", display: "flex", gap: "6px", background: isDarkMode ? "rgba(255,255,255,0.03)" : "rgba(0,0,0,0.02)", borderBottom: isDarkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(0,0,0,0.05)" }}>
          <button
            onClick={() => setTargetScope("global")}
            style={{
              flex: 1, padding: "5px 8px", fontSize: "11px", fontWeight: 600, borderRadius: "6px",
              border: targetScope === "global" ? (isDarkMode ? "1px solid #3b82f6" : "1px solid rgba(37, 99, 235, 0.5)") : (isDarkMode ? "1px solid #334155" : "1px solid rgba(203, 213, 225, 0.5)"),
              background: targetScope === "global" ? (isDarkMode ? "rgba(59, 130, 246, 0.2)" : "rgba(239, 246, 255, 0.7)") : "transparent",
              color: targetScope === "global" ? (isDarkMode ? "#60a5fa" : "#1d4ed8") : (isDarkMode ? "#94a3b8" : "#64748b"), cursor: "pointer", transition: "all 0.2s"
            }}
          >
            🌐 Full Document
          </button>
          <button
            onClick={() => setTargetScope("segment")}
            disabled={!selectedSegmentId}
            style={{
              flex: 1, padding: "5px 8px", fontSize: "11px", fontWeight: 600, borderRadius: "6px",
              border: targetScope === "segment" ? (isDarkMode ? "1px solid #3b82f6" : "1px solid rgba(37, 99, 235, 0.5)") : (isDarkMode ? "1px solid #334155" : "1px solid rgba(203, 213, 225, 0.5)"),
              background: targetScope === "segment" ? (isDarkMode ? "rgba(59, 130, 246, 0.2)" : "rgba(239, 246, 255, 0.7)") : "transparent",
              color: targetScope === "segment" ? (isDarkMode ? "#60a5fa" : "#1d4ed8") : (isDarkMode ? "#94a3b8" : "#64748b"), opacity: selectedSegmentId ? 1 : 0.5,
              cursor: selectedSegmentId ? "pointer" : "not-allowed", transition: "all 0.2s"
            }}
          >
            🎯 Selected Page
          </button>
        </div>
      )}

      <div className="prompt-panel__log" style={{ flex: 1, overflowY: "auto", overflowX: "hidden", padding: "14px", display: "flex", flexDirection: "column", gap: "10px" }}>
        {promptLog.map((msg) => (
          <div
            key={msg.id}
            className={`chat-message chat-message--${msg.sender}`}
            style={{
              alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
              maxWidth: "88%",
              wordBreak: "break-word",
              overflowWrap: "anywhere",
              whiteSpace: "pre-wrap",
              background: msg.sender === "user" ? (isDarkMode ? "#2563eb" : "#1a73e8") : (isDarkMode ? "#1e293b" : "#ffffff"),
              color: msg.sender === "user" ? "#ffffff" : (isDarkMode ? "#f8fafc" : "#1e293b"),
              padding: "12px 14px",
              borderRadius: msg.sender === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
              boxShadow: msg.sender === "user" ? "0 4px 12px rgba(26,115,232,0.2)" : "0 4px 12px rgba(0,0,0,0.05)",
              border: isDarkMode && msg.sender !== "user" ? "1px solid rgba(255,255,255,0.05)" : "1px solid rgba(0,0,0,0.02)",
              fontSize: "13px",
              lineHeight: "1.5",
            }}
          >
            <div className="chat-message__text">{msg.text}</div>
            {msg.sender !== "user" && (
              <div style={{ display: "flex", gap: "6px", marginTop: "8px", paddingTop: "6px", borderTop: isDarkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(0,0,0,0.05)" }}>
                <button
                  style={{
                    background: isDarkMode ? "rgba(59, 130, 246, 0.2)" : "#eff6ff",
                    border: isDarkMode ? "1px solid rgba(59, 130, 246, 0.4)" : "1px solid #bfdbfe",
                    color: isDarkMode ? "#60a5fa" : "#1d4ed8",
                    padding: "3px 8px",
                    borderRadius: "4px",
                    fontSize: "10.5px",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                  onClick={() => {
                    if (activeEditor) {
                      activeEditor.commands.insertContent(msg.text);
                    }
                  }}
                  title="Insert text at cursor into active document section"
                >
                  📥 Insert to Editor
                </button>
                <button
                  style={{
                    background: isDarkMode ? "rgba(255,255,255,0.05)" : "#f1f5f9",
                    border: isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid #cbd5e1",
                    color: isDarkMode ? "#94a3b8" : "#475569",
                    padding: "3px 8px",
                    borderRadius: "4px",
                    fontSize: "10.5px",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                  onClick={() => navigator.clipboard.writeText(msg.text)}
                  title="Copy response text to clipboard"
                >
                  📋 Copy
                </button>
              </div>
            )}
          </div>
        ))}
        {loading && <div className="chat-message chat-message--assistant" style={{ alignSelf: "flex-start", background: isDarkMode ? "rgba(30, 41, 59, 0.9)" : "rgba(255, 255, 255, 0.9)", padding: "10px 12px", borderRadius: "10px", fontSize: "12px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>Analyzing intent & processing...</div>}
      </div>

      <div className="prompt-panel__footer" style={{ padding: "16px", borderTop: isDarkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(0,0,0,0.04)", background: isDarkMode ? "rgba(15, 23, 42, 0.8)" : "rgba(248, 250, 252, 0.9)" }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Ask AI Co-Pilot to edit, expand, or reformat..."
          rows={2}
          style={{
            width: "100%",
            padding: "12px 14px",
            fontSize: "13px",
            lineHeight: "1.4",
            borderRadius: "12px",
            border: isDarkMode ? "1px solid #334155" : "1px solid #cbd5e1",
            background: isDarkMode ? "#0f172a" : "#ffffff",
            color: isDarkMode ? "#f8fafc" : "#1e293b",
            resize: "none",
            outline: "none",
            boxSizing: "border-box",
            marginBottom: "12px",
            boxShadow: "inset 0 2px 4px rgba(0,0,0,0.02)",
          }}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          style={{
            width: "100%",
            padding: "10px",
            fontSize: "13px",
            fontWeight: 600,
            borderRadius: "10px",
            border: "none",
            background: loading || !input.trim() ? (isDarkMode ? "#334155" : "#cbd5e1") : "linear-gradient(135deg, #2563eb, #1d4ed8)",
            color: "#ffffff",
            cursor: loading || !input.trim() ? "not-allowed" : "pointer",
            transition: "all 0.2s ease",
            boxShadow: loading || !input.trim() ? "none" : "0 4px 12px rgba(37, 99, 235, 0.25)",
          }}
        >
          {loading ? "Processing request..." : "Send to Co-Pilot"}
        </button>
      </div>
    </aside>
  );
}
