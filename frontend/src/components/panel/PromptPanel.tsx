import { useState, useRef } from "react";
import { answerPendingQuestion, refineSegment, refineSelection, uploadKnowledgeFiles } from "../../api/client";
import { useWizardStore } from "../../state/wizardStore";
import { exportToPdf, exportToWord, exportToTxt } from "../../utils/exportUtils";
import type { StreamEvent } from "../../types";

interface PromptPanelProps {
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  onStreamEvent?: (event: StreamEvent) => void;
  onStreamStatusChange?: (isStreaming: boolean) => void;
}

export function PromptPanel({ isCollapsed, onToggleCollapse, onStreamEvent, onStreamStatusChange }: PromptPanelProps) {
  const {
    sessionId,
    documentId,
    model,
    kbId,
    kbFiles,
    setKnowledgeBase,
    selectedSegmentId,
    segments,
    promptLog,
    activeEditor,
    isDarkMode,
    toggleDarkMode,
    styleConfig,
    setStyleConfig,
    pageLayoutSize,
    setPageLayoutSize,
    setZoomLevel,
    setLayoutMode,
    undo,
    redo,
    addPage,
    addChatMessage,
    updateSegment,
    setGeneratedDocument,
  } = useWizardStore((s) => ({
    sessionId: s.sessionId,
    documentId: s.documentId,
    model: s.model,
    kbId: s.kbId,
    kbFiles: s.kbFiles,
    setKnowledgeBase: s.setKnowledgeBase,
    selectedSegmentId: s.selectedSegmentId,
    segments: s.segments,
    promptLog: s.promptLog,
    activeEditor: s.activeEditor,
    isDarkMode: s.isDarkMode,
    toggleDarkMode: s.toggleDarkMode,
    styleConfig: s.styleConfig,
    setStyleConfig: s.setStyleConfig,
    pageLayoutSize: s.pageLayoutSize,
    setPageLayoutSize: s.setPageLayoutSize,
    setZoomLevel: s.setZoomLevel,
    setLayoutMode: s.setLayoutMode,
    undo: s.undo,
    redo: s.redo,
    addPage: s.addPage,
    addChatMessage: s.addChatMessage,
    updateSegment: s.updateSegment,
    setGeneratedDocument: s.setGeneratedDocument,
  }));

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [targetScope, setTargetScope] = useState<"selection" | "segment" | "global">("global");
  const [uploadingFiles, setUploadingFiles] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleFileUpload(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploadingFiles(true);
    try {
      const res = await uploadKnowledgeFiles(Array.from(files), kbId || undefined);
      setKnowledgeBase(res.kb_id, res.files);
      addChatMessage({
        id: `upload_${Date.now()}`,
        sender: "assistant",
        text: `📎 Ingested ${files.length} reference document(s) into Copilot context (${res.total_chunks} vector chunks indexed).`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      });
    } catch (err: any) {
      console.error("Upload error in PromptPanel:", err);
    } finally {
      setUploadingFiles(false);
    }
  }

  const getChain = () => {
    if (!activeEditor || activeEditor.isDestroyed) return null;
    try {
      return activeEditor.chain?.()?.focus?.() || null;
    } catch {
      return null;
    }
  };

  const selectedTextSnippet = activeEditor && !activeEditor.isDestroyed
    ? (activeEditor.state?.doc?.textBetween(activeEditor.state?.selection?.from || 0, activeEditor.state?.selection?.to || 0) || "")
    : "";

  const selectedSegment = segments.find((s) => s.segment_id === selectedSegmentId);

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

    const isBroadInstruction = /\b(whole document|entire document|all pages|all sections|remake|regenerate|rebuild|add section|new page|across the document)\b/i.test(userText);
    const isExplicitSnippet = targetScope === "selection" && selectedTextSnippet && selectedTextSnippet.trim().length > 0 && !isBroadInstruction;

    setLoading(true);
    onStreamStatusChange?.(true);
    onStreamEvent?.({
      type: "agent_thought",
      step: isExplicitSnippet ? "targeted_selection_refine" : targetScope === "segment" ? "segment_refine" : "document_agent_orchestration",
      status: "running",
    });
    try {
      if (isExplicitSnippet) {
        const res = await refineSelection({
          session_id: sessionId,
          selection_text: selectedTextSnippet,
          instruction: userText,
          content_density: "med",
        });
        const refusalIndicators = ["sorry", "cannot fulfill", "can't assist", "unable to assist", "as an ai"];
        const isRefusal = refusalIndicators.some((ind) => (res.replacement_text || "").toLowerCase().includes(ind));
        if (res.replacement_text && !isRefusal) {
          const chain = getChain();
          chain?.insertContent(res.replacement_text)?.run?.();
          addChatMessage({
            id: String(Date.now() + 1),
            sender: "assistant",
            text: `Surgically updated highlighted text to: "${res.replacement_text}"`,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          });
        } else {
          addChatMessage({
            id: String(Date.now() + 1),
            sender: "assistant",
            text: isRefusal ? "Unable to rewrite snippet with that prompt. Switched to document-level processing." : "Processed snippet request.",
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          });
        }
      } else if (targetScope === "segment" && selectedSegmentId && documentId && !isBroadInstruction) {
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
          else if (act.action_type === "insert_table") getChain()?.insertTable({ rows: act.table_rows || 3, cols: act.table_cols || 3, withHeaderRow: true })?.run?.();
          else if (act.action_type === "add_page") addPage();
          else if (act.action_type === "clear_formatting") getChain()?.unsetAllMarks()?.run?.();
          else if (act.action_type === "undo") undo();
          else if (act.action_type === "redo") redo();
          else if (act.action_type === "set_zoom" && act.zoom_level) setZoomLevel(act.zoom_level);
          else if (act.action_type === "set_layout_mode" && act.layout_mode) setLayoutMode(act.layout_mode as any);
          else if (act.action_type === "toggle_dark_mode") toggleDarkMode();
          else if (act.action_type === "set_header") setStyleConfig({ headerText: act.header_text || "Procurement Proposal Specification", showHeaderFooter: true });
          else if (act.action_type === "set_page_numbers") {
            const pos = act.page_number_position || "bottom-right";
            if (pos === "none") setStyleConfig({ showPageNumbers: false, pageNumberPosition: "none" });
            else setStyleConfig({ showPageNumbers: true, pageNumberPosition: pos as any });
          }
          else if (act.action_type === "align_text") {
            const align = act.alignment || "left";
            getChain()?.setTextAlign(align)?.run?.();
          }
          else if (act.action_type === "text_format") {
            const fmt = act.format_style || "bold";
            const chain = getChain();
            if (chain) {
              if (fmt === "bold") chain.toggleBold()?.run?.();
              else if (fmt === "italic") chain.toggleItalic()?.run?.();
              else if (fmt === "underline") chain.toggleUnderline()?.run?.();
              else if (fmt === "strike") chain.toggleStrike()?.run?.();
              else if (fmt === "subscript") chain.toggleSubscript()?.run?.();
              else if (fmt === "superscript") chain.toggleSuperscript()?.run?.();
            }
          }
          else if (act.action_type === "insert_signature_block") {
            getChain()?.insertContent(`
              <table border="1" style="width:100%; border-collapse:collapse; margin:20px 0;">
                <tr>
                  <th style="padding:10px; background:#f1f5f9;">Purchaser Authorized Representative</th>
                  <th style="padding:10px; background:#f1f5f9;">Vendor Authorized Representative</th>
                </tr>
                <tr>
                  <td style="padding:20px;">Signature: ____________________<br>Name: Gulmira Abdullaeva<br>Date: ${new Date().toLocaleDateString()}</td>
                  <td style="padding:20px;">Signature: ____________________<br>Name: Abdalah Jadaan<br>Seal: [ Corporate Seal ]</td>
                </tr>
              </table>
            `)?.run?.();
          }
          else if (act.action_type === "insert_callout_box") {
            getChain()?.insertContent(`
              <div style="border: 2px dashed #1a73e8; background: #f8fafc; padding: 16px; border-radius: 8px; margin: 16px 0;">
                <p style="margin: 0; font-weight: 600; color: #1a73e8;">📦 Important Procurement Notice</p>
                <p style="margin-top: 4px; font-size: 13px;">Enter key compliance notes, SLA thresholds, or vendor deliverables here...</p>
              </div>
            `)?.run?.();
          }
          else if (act.action_type === "insert_date") {
            getChain()?.insertContent(` ${new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })} `)?.run?.();
          }
          else if (act.action_type === "insert_cover_page") {
            const style = act.cover_style || "corporate";
            const chain = getChain();
            if (style === "corporate") {
              chain?.insertContent(`<div style="background: linear-gradient(135deg, #0f4c81, #1a73e8); color: white; padding: 40px; border-radius: 8px; text-align: center; margin-bottom: 24px;"><h1 style="color: white; font-size: 28px; margin-bottom: 8px;">${act.custom_text || "EXECUTIVE PROCUREMENT PROPOSAL"}</h1><p style="font-size: 16px; opacity: 0.9;">ENTERPRISE SPECIFICATION & TECHNICAL BLUEPRINT</p><div style="margin-top: 20px; font-size: 13px; opacity: 0.8;">Date: ${new Date().toLocaleDateString()} • Status: Confidential</div></div>`)?.run?.();
            } else if (style === "minimal") {
              chain?.insertContent(`<div style="text-align: center; padding: 40px 0; border-bottom: 2px solid #333;"><h1 style="letter-spacing: 2px;">${act.custom_text || "PROCUREMENT PROPOSAL SPECIFICATION"}</h1><p>Confidential Tender Document</p></div>`)?.run?.();
            } else {
              chain?.insertContent(`<div style="border-left: 8px solid #2563eb; padding: 24px; background: #eff6ff; margin-bottom: 24px;"><h1 style="color: #1e40af; margin: 0;">${act.custom_text || "TECHNICAL PROPOSAL BLUEPRINT"}</h1><p style="margin-top: 6px; color: #1e3a8a;">RFP Technical Submission</p></div>`)?.run?.();
            }
          }
          else if (act.action_type === "insert_wordart") {
            const text = act.custom_text || "ENTERPRISE PROCUREMENT";
            getChain()?.insertContent(`<h1 style="background: linear-gradient(45deg, #1a73e8, #9c27b0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 32px; font-weight: 800; text-align: center; margin: 20px 0;">${text}</h1>`)?.run?.();
          }
          else if (act.action_type === "insert_reviewer_note") {
            const note = act.custom_text || "Please review compliance terms against RFP Appendix 4.";
            getChain()?.insertContent(`<div style="background: #fff8e1; border-left: 4px solid #ffb300; padding: 10px; margin: 12px 0; font-size: 13px; color: #78350f;">💬 <strong>Reviewer Note:</strong> ${note}</div>`)?.run?.();
          }
          else if (act.action_type === "insert_image" && act.url) {
            getChain()?.setImage({ src: act.url })?.run?.();
          }
          else if (act.action_type === "insert_link" && act.url) {
            const linkText = act.custom_text || act.url;
            getChain()?.insertContent(`<a href="${act.url}" target="_blank" rel="noopener noreferrer">${linkText}</a>`)?.run?.();
          }
          else if (act.action_type === "insert_bookmark") {
            const bookmarkName = act.custom_text || "section-mark";
            getChain()?.insertContent(`<span id="${bookmarkName}" style="color: #2563eb; font-weight: 600;">🚩 [${bookmarkName}]</span>`)?.run?.();
          }
          else if (act.action_type === "insert_horizontal_rule") {
            getChain()?.setHorizontalRule()?.run?.();
          }
          else if (act.action_type === "insert_list") {
            const chain = getChain();
            if (act.list_type === "ordered") chain?.toggleOrderedList()?.run?.();
            else chain?.toggleBulletList()?.run?.();
          }
          else if (act.action_type === "export_document") {
            const fmt = act.export_format || "pdf";
            if (fmt === "pdf") exportToPdf(segments, "Procurement Proposal Document", pageLayoutSize, styleConfig);
            else if (fmt === "doc") exportToWord(segments, "Procurement Proposal Document", styleConfig);
            else if (fmt === "txt") exportToTxt(segments, "Procurement Proposal Document");
          }
        }

        if (res.segments && res.segments.length > 0 && (res.status === "ready" || (res as any).ribbon_action)) {
          setGeneratedDocument(
            res.document_id || documentId || "doc_current",
            res.lexical_state || {},
            res.page_titles || res.segments.map((s) => s.name),
            res.segments,
            res.style_config as any,
            res.page_layout_size as any
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

      onStreamEvent?.({
        type: "agent_thought",
        step: isExplicitSnippet ? "targeted_selection_refine" : targetScope === "segment" ? "segment_refine" : "document_agent_orchestration",
        status: "completed",
      });
    } catch (err) {
      addChatMessage({
        id: String(Date.now() + 1),
        sender: "assistant",
        text: `Error: ${err instanceof Error ? err.message : "Failed to process prompt."}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      });
    } finally {
      setLoading(false);
      onStreamStatusChange?.(false);
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
        title="Expand Copilot"
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
          title="Expand Copilot"
        >
          ▶
        </button>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: "12px", color: isDarkMode ? "#60a5fa" : "#1a73e8" }}>
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <span style={{ writingMode: "vertical-rl", textTransform: "uppercase", fontSize: "11px", fontWeight: 700, letterSpacing: "1px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
          Copilot
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
            ✨ Copilot
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
            title="Collapse Copilot"
          >
            ◀
          </button>
        )}
      </div>

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
            cursor: selectedSegmentId ? "pointer" : "not-allowed", transition: "all 0.2s",
            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap"
          }}
          title={selectedSegment?.name ? `Target: ${selectedSegment.name}` : undefined}
        >
          🎯 {selectedSegment?.name ? (selectedSegment.name.length > 14 ? selectedSegment.name.slice(0, 14) + "..." : selectedSegment.name) : "Selected Page"}
        </button>
        {selectedTextSnippet && selectedTextSnippet.trim().length > 0 && (
          <button
            onClick={() => setTargetScope("selection")}
            style={{
              flex: 1, padding: "5px 8px", fontSize: "11px", fontWeight: 600, borderRadius: "6px",
              border: targetScope === "selection" ? "1px solid #f59e0b" : "1px solid rgba(245, 158, 11, 0.4)",
              background: targetScope === "selection" ? "rgba(245, 158, 11, 0.2)" : "transparent",
              color: targetScope === "selection" ? (isDarkMode ? "#fde68a" : "#b45309") : (isDarkMode ? "#d97706" : "#b45309"),
              cursor: "pointer", transition: "all 0.2s",
              overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap"
            }}
            title={`Target highlighted snippet: "${selectedTextSnippet}"`}
          >
            ✂️ Snippet
          </button>
        )}
      </div>

      {targetScope === "selection" && selectedTextSnippet && selectedTextSnippet.trim().length > 0 && (
        <div style={{ padding: "6px 12px", background: isDarkMode ? "rgba(120, 53, 15, 0.4)" : "rgba(254, 243, 199, 0.7)", color: isDarkMode ? "#fde68a" : "#92400e", fontSize: "11px", fontWeight: 600, borderBottom: "1px solid rgba(253, 230, 138, 0.3)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span>✂️ Target Snippet: "<em>{selectedTextSnippet.slice(0, 24)}...</em>"</span>
          <button
            onClick={() => setTargetScope("global")}
            style={{ background: "transparent", border: "none", cursor: "pointer", color: "inherit", fontWeight: 700, padding: "0 4px" }}
            title="Deselect snippet and target full document"
          >
            ✕
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
                    if (activeEditor && !activeEditor.isDestroyed) {
                      activeEditor.commands?.insertContent?.(msg.text);
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

      <div className="prompt-panel__footer" style={{ padding: "14px 16px", borderTop: isDarkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(0,0,0,0.04)", background: isDarkMode ? "rgba(15, 23, 42, 0.8)" : "rgba(248, 250, 252, 0.9)" }}>
        <div style={{ display: "flex", gap: "6px", overflowX: "auto", paddingBottom: "10px", scrollbarWidth: "none" }}>
          {[
            "Change vendor response timeline across document",
            "Update pricing & payment milestone tables",
            "Add ISO 27001 & data security compliance",
            "Add brand new section: SLA & Penalties",
            "Make tone strictly formal & executive",
          ].map((promptText) => (
            <button
              key={promptText}
              type="button"
              onClick={() => setInput(promptText)}
              style={{
                whiteSpace: "nowrap",
                fontSize: "11px",
                fontWeight: 500,
                padding: "3px 8px",
                borderRadius: "10px",
                border: isDarkMode ? "1px solid rgba(255,255,255,0.12)" : "1px solid rgba(0,0,0,0.1)",
                background: isDarkMode ? "rgba(255,255,255,0.06)" : "#ffffff",
                color: isDarkMode ? "#cbd5e1" : "#475569",
                cursor: "pointer",
                transition: "all 0.15s",
                flexShrink: 0,
              }}
            >
              💡 {promptText}
            </button>
          ))}
        </div>

        {/* Docs / PDF attachment row matching user wireframe */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px", flexWrap: "wrap", gap: "6px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadingFiles}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                padding: "4px 10px",
                fontSize: "11px",
                fontWeight: 600,
                borderRadius: "6px",
                border: isDarkMode ? "1px solid #3b82f6" : "1px solid #93c5fd",
                background: isDarkMode ? "rgba(59, 130, 246, 0.2)" : "#eff6ff",
                color: isDarkMode ? "#93c5fd" : "#1d4ed8",
                cursor: uploadingFiles ? "not-allowed" : "pointer",
                transition: "all 0.15s ease",
              }}
              title="Upload reference PDF, DOCX, or text files for Copilot context"
            >
              <span>📎</span>
              <span>{uploadingFiles ? "Uploading..." : "+ Add Docs/PDF"}</span>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.md"
              style={{ display: "none" }}
              onChange={(e) => handleFileUpload(e.target.files)}
            />

            {kbFiles && kbFiles.length > 0 && (
              <span style={{ fontSize: "11px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
                {kbFiles.length} doc{kbFiles.length > 1 ? "s" : ""} active
              </span>
            )}
          </div>
        </div>

        {/* Display active doc chips if any */}
        {kbFiles && kbFiles.length > 0 && (
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginBottom: "8px", maxHeight: "50px", overflowY: "auto" }}>
            {kbFiles.map((file, i) => (
              <span
                key={file.filename || i}
                className="copilot-file-chip"
                title={`${file.filename} (${file.chunk_count} chunks)`}
              >
                <span>📄</span>
                <span style={{ maxWidth: "120px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {file.filename}
                </span>
              </span>
            ))}
          </div>
        )}

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Ask Copilot to edit, expand, or reformat..."
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
          {loading ? "Processing request..." : "Send to Copilot"}
        </button>
      </div>
    </aside>
  );
}
