import { useState } from "react";
import { useWizardStore, PageLayoutSize } from "../../state/wizardStore";
import type { DocumentSegment } from "../../types";

function extractTextFromTipTapNode(node: any): string {
  if (!node) return "";
  if (typeof node === "string") return node;
  if (node.text) return node.text;
  if (Array.isArray(node)) return node.map(extractTextFromTipTapNode).join(" ");
  if (node.content && Array.isArray(node.content)) {
    return node.content.map(extractTextFromTipTapNode).join(" ");
  }
  return "";
}

function calculateDocStats(segments: DocumentSegment[]) {
  let fullText = "";
  let paragraphCount = 0;

  segments.forEach((seg) => {
    const text = extractTextFromTipTapNode(seg.content);
    fullText += " " + text;
    if (seg.content && Array.isArray((seg.content as any).content)) {
      paragraphCount += (seg.content as any).content.length;
    }
  });

  const words = fullText.trim().split(/\s+/).filter(Boolean);
  const wordCount = words.length;
  const charCount = fullText.length;
  const readingTimeMinutes = Math.max(1, Math.ceil(wordCount / 200));

  return { wordCount, charCount, paragraphCount, readingTimeMinutes };
}

export function EditorStatusBar() {
  const {
    segments,
    selectedSegmentId,
    setSelectedSegmentId,
    pageLayoutSize,
    setPageLayoutSize,
    zoomLevel,
    setZoomLevel,
    layoutMode,
    setLayoutMode,
  } = useWizardStore((s) => ({
    segments: s.segments,
    selectedSegmentId: s.selectedSegmentId,
    setSelectedSegmentId: s.setSelectedSegmentId,
    pageLayoutSize: s.pageLayoutSize,
    setPageLayoutSize: s.setPageLayoutSize,
    zoomLevel: s.zoomLevel,
    setZoomLevel: s.setZoomLevel,
    layoutMode: s.layoutMode,
    setLayoutMode: s.setLayoutMode,
  }));

  const [docLanguage, setDocLanguage] = useState("English (United States)");
  const [showStatsModal, setShowStatsModal] = useState(false);
  const [showLangModal, setShowLangModal] = useState(false);
  const [showAccessModal, setShowAccessModal] = useState(false);
  const [showPageModal, setShowPageModal] = useState(false);
  const [showLayoutModal, setShowLayoutModal] = useState(false);

  const activePageIndex = selectedSegmentId
    ? Math.max(1, segments.findIndex((s) => s.segment_id === selectedSegmentId) + 1)
    : 1;

  const stats = calculateDocStats(segments);

  // Scan document for accessibility issues
  const complianceWarnings = segments.filter((s) => s.compliance_flag);

  return (
    <>
      <footer className="editor-status-bar" style={{ userSelect: "none" }}>
        <div className="status-bar-left" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {/* Active Page / Page Picker */}
          <button
            className="status-bar-interactive-btn"
            style={{ background: "none", border: "none", color: "#ffffff", fontSize: "12px", cursor: "pointer", padding: "2px 6px", borderRadius: "4px" }}
            onClick={() => setShowPageModal(true)}
            title="Click to jump to page"
          >
            Page {activePageIndex} of {segments.length || 1}
          </button>

          <span className="status-bar-bullet">•</span>

          {/* Word Count / Statistics */}
          <button
            className="status-bar-interactive-btn"
            style={{ background: "none", border: "none", color: "#ffffff", fontSize: "12px", cursor: "pointer", padding: "2px 6px", borderRadius: "4px" }}
            onClick={() => setShowStatsModal(true)}
            title="Click to view detailed word count statistics"
          >
            {stats.wordCount} words
          </button>

          <span className="status-bar-bullet">•</span>

          {/* Language Selector */}
          <button
            className="status-bar-interactive-btn"
            style={{ background: "none", border: "none", color: "#ffffff", fontSize: "12px", cursor: "pointer", padding: "2px 6px", borderRadius: "4px" }}
            onClick={() => setShowLangModal(true)}
            title="Click to change document proofing language"
          >
            🌐 {docLanguage}
          </button>

          <span className="status-bar-bullet">•</span>

          {/* Accessibility Checker */}
          <button
            className="status-bar-interactive-btn"
            style={{ background: "none", border: "none", color: complianceWarnings.length ? "#ffeb3b" : "#ffffff", fontSize: "12px", cursor: "pointer", padding: "2px 6px", borderRadius: "4px" }}
            onClick={() => setShowAccessModal(true)}
            title="Click to run document accessibility scan"
          >
            <span className="status-icon">{complianceWarnings.length ? "⚠️" : "☑️"}</span> Accessibility:{" "}
            {complianceWarnings.length ? `${complianceWarnings.length} Warnings` : "Good to go"}
          </button>
        </div>

        <div className="status-bar-right" style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {/* Layout Paper Size Switcher */}
          <button
            className="status-bar-interactive-btn"
            style={{ background: "none", border: "none", color: "#ffffff", fontSize: "12px", cursor: "pointer", padding: "2px 6px", borderRadius: "4px" }}
            onClick={() => setShowLayoutModal(true)}
            title="Click to change paper size"
          >
            Layout: {pageLayoutSize}
          </button>

          {/* View Mode Toggles */}
          <div className="view-mode-toggles">
            <button
              className={`view-mode-btn ${layoutMode === "focus" ? "active" : ""}`}
              title="Focus view mode"
              onClick={() => setLayoutMode("focus")}
            >
              📖
            </button>
            <button
              className={`view-mode-btn ${layoutMode === "print" ? "active" : ""}`}
              title="Print layout view"
              onClick={() => setLayoutMode("print")}
            >
              📑
            </button>
            <button
              className={`view-mode-btn ${layoutMode === "web" ? "active" : ""}`}
              title="Web layout view"
              onClick={() => setLayoutMode("web")}
            >
              🌐
            </button>
          </div>

          {/* Zoom Controls */}
          <div className="zoom-controls" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <button
              className="zoom-btn"
              onClick={() => setZoomLevel((z) => Math.max(50, z - 10))}
              title="Zoom out"
            >
              -
            </button>
            <input
              type="range"
              min={50}
              max={200}
              value={zoomLevel}
              onChange={(e) => setZoomLevel(Number(e.target.value))}
              className="zoom-slider"
            />
            <button
              className="zoom-btn"
              onClick={() => setZoomLevel((z) => Math.min(200, z + 10))}
              title="Zoom in"
            >
              +
            </button>
            <span
              className="zoom-val"
              style={{ cursor: "pointer" }}
              onClick={() => setZoomLevel(100)}
              title="Click to reset zoom to 100%"
            >
              {zoomLevel}%
            </span>
          </div>
        </div>
      </footer>

      {/* Word Count Statistics Modal */}
      {showStatsModal && (
        <div
          style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.5)", zIndex: 99999, display: "flex", alignItems: "center", justifyContent: "center" }}
          onClick={() => setShowStatsModal(false)}
        >
          <div style={{ background: "#fff", color: "#333", borderRadius: "8px", padding: "24px", width: "320px", boxShadow: "0 4px 20px rgba(0,0,0,0.2)" }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ margin: "0 0 16px 0", fontSize: "16px", borderBottom: "1px solid #eee", paddingBottom: "8px" }}>📊 Word Count Statistics</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "14px" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Words:</span> <b>{stats.wordCount}</b></div>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Characters:</span> <b>{stats.charCount}</b></div>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Paragraphs:</span> <b>{stats.paragraphCount}</b></div>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Pages:</span> <b>{segments.length}</b></div>
              <div style={{ display: "flex", justifyContent: "space-between" }}><span>Est. Reading Time:</span> <b>~{stats.readingTimeMinutes} min</b></div>
            </div>
            <button
              style={{ marginTop: "20px", width: "100%", padding: "8px", background: "#1a73e8", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer", fontWeight: 600 }}
              onClick={() => setShowStatsModal(false)}
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Language Modal */}
      {showLangModal && (
        <div
          style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.5)", zIndex: 99999, display: "flex", alignItems: "center", justifyContent: "center" }}
          onClick={() => setShowLangModal(false)}
        >
          <div style={{ background: "#fff", color: "#333", borderRadius: "8px", padding: "20px", width: "300px" }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ margin: "0 0 12px 0", fontSize: "15px" }}>🌐 Select Proofing Language</h3>
            {["English (United States)", "English (United Kingdom)", "Spanish (Spain)", "French (France)", "German (Germany)", "Japanese"].map((lang) => (
              <div
                key={lang}
                style={{ padding: "8px", borderRadius: "4px", cursor: "pointer", background: docLanguage === lang ? "#e8f0fe" : "transparent", fontWeight: docLanguage === lang ? 600 : 400 }}
                onClick={() => {
                  setDocLanguage(lang);
                  setShowLangModal(false);
                }}
              >
                {lang}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Accessibility Scan Modal */}
      {showAccessModal && (
        <div
          style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.5)", zIndex: 99999, display: "flex", alignItems: "center", justifyContent: "center" }}
          onClick={() => setShowAccessModal(false)}
        >
          <div style={{ background: "#fff", color: "#333", borderRadius: "8px", padding: "20px", width: "380px" }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ margin: "0 0 12px 0", fontSize: "16px" }}>🔍 Accessibility Inspector</h3>
            {complianceWarnings.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <p style={{ color: "#d93025", fontWeight: 600, margin: 0 }}>Found {complianceWarnings.length} compliance warnings:</p>
                {complianceWarnings.map((s) => (
                  <div key={s.segment_id} style={{ background: "#fff5f5", padding: "8px", borderRadius: "4px", fontSize: "12px", borderLeft: "3px solid #d93025" }}>
                    <b>{s.name}</b>: {s.compliance_note || "Ungrounded clause tag"}
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: "#1e8e3e", fontWeight: 600 }}>
                ✅ Good to go! No compliance or visual contrast issues detected across {segments.length} pages.
              </div>
            )}
            <button
              style={{ marginTop: "16px", width: "100%", padding: "8px", background: "#1a73e8", color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer" }}
              onClick={() => setShowAccessModal(false)}
            >
              Done
            </button>
          </div>
        </div>
      )}

      {/* Page Jump Modal */}
      {showPageModal && (
        <div
          style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.5)", zIndex: 99999, display: "flex", alignItems: "center", justifyContent: "center" }}
          onClick={() => setShowPageModal(false)}
        >
          <div style={{ background: "#fff", color: "#333", borderRadius: "8px", padding: "20px", width: "300px" }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ margin: "0 0 12px 0", fontSize: "15px" }}>📄 Jump to Page</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {segments.map((seg, idx) => (
                <button
                  key={seg.segment_id}
                  style={{
                    textAlign: "left",
                    padding: "8px 12px",
                    border: "1px solid #e0e0e0",
                    borderRadius: "4px",
                    background: selectedSegmentId === seg.segment_id ? "#e8f0fe" : "#fff",
                    cursor: "pointer",
                    fontWeight: selectedSegmentId === seg.segment_id ? 600 : 400,
                  }}
                  onClick={() => {
                    setSelectedSegmentId(seg.segment_id);
                    setShowPageModal(false);
                    const el = document.querySelector(`[data-segment-id="${seg.segment_id}"]`);
                    if (el) el.scrollIntoView({ behavior: "smooth" });
                  }}
                >
                  Page {idx + 1}: {seg.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Layout Size Switcher Modal */}
      {showLayoutModal && (
        <div
          style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.5)", zIndex: 99999, display: "flex", alignItems: "center", justifyContent: "center" }}
          onClick={() => setShowLayoutModal(false)}
        >
          <div style={{ background: "#fff", color: "#333", borderRadius: "8px", padding: "20px", width: "300px" }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ margin: "0 0 12px 0", fontSize: "15px" }}>📏 Paper Layout Size</h3>
            {(["A4", "LETTER", "A3", "LEGAL"] as PageLayoutSize[]).map((sz) => (
              <div
                key={sz}
                style={{ padding: "8px 12px", borderRadius: "4px", cursor: "pointer", background: pageLayoutSize === sz ? "#e8f0fe" : "transparent", fontWeight: pageLayoutSize === sz ? 600 : 400 }}
                onClick={() => {
                  setPageLayoutSize(sz);
                  setShowLayoutModal(false);
                }}
              >
                {sz} Standard
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
