import { useState } from "react";
import { uploadKnowledgeFiles } from "../../api/client";
import { useWizardStore } from "../../state/wizardStore";

interface ConfigPanelProps {
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

function extractHeadingsFromSegment(segment: any): { text: string; level: number }[] {
  const headings: { text: string; level: number }[] = [];
  if (!segment.content || typeof segment.content !== "object") return headings;
  const nodes = (segment.content as any).content || [];
  for (const node of nodes) {
    if (node.type === "heading" && node.content && Array.isArray(node.content)) {
      const text = node.content.map((c: any) => c.text || "").join("").trim();
      if (text) {
        headings.push({ text, level: node.attrs?.level || 2 });
      }
    }
  }
  return headings;
}

export function ConfigPanel({ isCollapsed, onToggleCollapse }: ConfigPanelProps) {
  const { kbFiles, segments, selectedSegmentId, setSelectedSegmentId, setKnowledgeBase, isDarkMode } = useWizardStore((s) => ({
    kbFiles: s.kbFiles,
    segments: s.segments,
    selectedSegmentId: s.selectedSegmentId,
    setSelectedSegmentId: s.setSelectedSegmentId,
    setKnowledgeBase: s.setKnowledgeBase,
    isDarkMode: s.isDarkMode,
  }));

  const addPage = useWizardStore((s) => s.addPage);
  const [uploading, setUploading] = useState(false);
  const [activeTab] = useState("Tab 1");

  async function handleFileUpload(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      const res = await uploadKnowledgeFiles(Array.from(files));
      setKnowledgeBase(res.kb_id, res.files);
    } catch (err) {
      console.error("Failed to upload additional KB files:", err);
    } finally {
      setUploading(false);
    }
  }

  function handleJumpToSegment(segmentId: string) {
    setSelectedSegmentId(segmentId);
    const element = document.querySelector(`[data-segment-id="${segmentId}"]`);
    element?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  if (isCollapsed) {
    return (
      <aside
        className="config-panel config-panel--collapsed"
        style={{
          background: isDarkMode ? "#0f172a" : "#ffffff",
          borderRadius: "12px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          padding: "16px 8px",
          cursor: "pointer",
        }}
        onClick={onToggleCollapse}
        title="Expand Document Tabs & Outline"
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
          ▶
        </button>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: "12px", color: isDarkMode ? "#60a5fa" : "#1a73e8" }}>
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="16" y1="13" x2="8" y2="13"></line>
          <line x1="16" y1="17" x2="8" y2="17"></line>
        </svg>
        <span style={{ writingMode: "vertical-rl", textTransform: "uppercase", fontSize: "11px", fontWeight: 700, letterSpacing: "1px", color: isDarkMode ? "#94a3b8" : "#64748b" }}>
          Doc Tabs & Context
        </span>
      </aside>
    );
  }

  return (
    <aside className="config-panel">
      {/* Google Docs Document Tabs Header */}
      <div className="doc-tabs-header">
        <div className="doc-tabs-title-row">
          <span className="doc-tabs-title">Document tabs</span>
          <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
            <button className="add-tab-btn" title="Add new document section" onClick={() => addPage("New Document Section")}>
              +
            </button>
            {onToggleCollapse && (
              <button
                onClick={onToggleCollapse}
                style={{
                  background: "transparent",
                  border: "none",
                  color: isDarkMode ? "#94a3b8" : "#64748b",
                  fontSize: "14px",
                  cursor: "pointer",
                  padding: "2px 6px",
                  borderRadius: "4px",
                }}
                title="Collapse Sidebar"
              >
                ◀
              </button>
            )}
          </div>
        </div>

        <div className="doc-tab-pill active">
          <span className="tab-icon">📑</span>
          <span className="tab-name">{activeTab}</span>
          <span className="tab-options">⋮</span>
        </div>
      </div>

      {/* Dynamic Outline & Table of Contents (ToC) Tree */}
      <div className="doc-outline-tree" style={{ maxHeight: "320px", overflowY: "auto" }}>
        <div className="outline-heading-master" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span>TABLE OF CONTENTS</span>
          <span style={{ fontSize: "10px", opacity: 0.7 }}>{segments.length} Pages</span>
        </div>
        {segments.map((seg, index) => {
          const subHeadings = extractHeadingsFromSegment(seg);
          const isSelected = selectedSegmentId === seg.segment_id;
          return (
            <div key={seg.segment_id} style={{ marginBottom: "4px" }}>
              <div
                className={`outline-item ${isSelected ? "active" : ""}`}
                onClick={() => handleJumpToSegment(seg.segment_id)}
                style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}
              >
                <span style={{ fontSize: "10px", fontWeight: 700, opacity: 0.7 }}>P{index + 1}</span>
                <span className="outline-title" style={{ fontWeight: isSelected ? 700 : 500 }}>
                  {seg.name}
                </span>
                {seg.compliance_flag && (
                  <span title="Compliance warning" style={{ marginLeft: "auto", fontSize: "10px" }}>⚠️</span>
                )}
              </div>
              {/* Nested H2 / H3 sub-headings */}
              {subHeadings.length > 0 && (
                <div style={{ paddingLeft: "16px", display: "flex", flexDirection: "column", gap: "2px" }}>
                  {subHeadings.map((h, hIdx) => (
                    <div
                      key={hIdx}
                      onClick={() => handleJumpToSegment(seg.segment_id)}
                      style={{
                        fontSize: "11px",
                        color: isDarkMode ? "#94a3b8" : "#64748b",
                        cursor: "pointer",
                        padding: "2px 4px",
                        borderRadius: "3px",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        borderLeft: isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid #e2e8f0",
                        paddingLeft: "6px",
                      }}
                      title={h.text}
                    >
                      {h.text}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="config-panel__divider" />

      {/* Knowledge Base Section */}
      <div className="config-panel__section">
        <h3>Knowledge Base & Context</h3>
        <div className="config-panel__dropzone">
          <input
            type="file"
            id="panel-kb-upload"
            multiple
            style={{ display: "none" }}
            onChange={(e) => handleFileUpload(e.target.files)}
          />
          <label htmlFor="panel-kb-upload" className="config-panel__drop-label">
            {uploading ? "Uploading..." : "+ Add PDF / DOCX to KB"}
          </label>
        </div>

        {kbFiles.length > 0 ? (
          <ul className="config-panel__file-list">
            {kbFiles.map((f) => (
              <li key={f.filename}>
                <span>📄 {f.filename}</span>
                <span className="file-chunks">({f.chunk_count} chunks)</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="empty-text">No custom documents attached.</p>
        )}
      </div>
    </aside>
  );
}
