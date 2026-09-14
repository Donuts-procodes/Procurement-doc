import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Table } from "@tiptap/extension-table";
import { TableRow } from "@tiptap/extension-table-row";
import { TableCell } from "@tiptap/extension-table-cell";
import { TableHeader } from "@tiptap/extension-table-header";
import { Image } from "@tiptap/extension-image";
import Subscript from "@tiptap/extension-subscript";
import Superscript from "@tiptap/extension-superscript";
import { Color } from "@tiptap/extension-color";
import { TextStyle } from "@tiptap/extension-text-style";
import TextAlign from "@tiptap/extension-text-align";
import { useEffect, useState, memo, useRef } from "react";
import { useWizardStore } from "../../state/wizardStore";
import { ContextMenu } from "./ContextMenu";
import { DocRuler } from "./DocRuler";
import { CitationNode } from "./CitationNode";
import { InlineFloatingToolbar } from "./InlineFloatingToolbar";
import { extractPlainTextFromSegment } from "../../utils/exportUtils";
import type { DocumentSegment } from "../../types";

interface SegmentBlockProps {
  segment: DocumentSegment;
  index: number;
  totalSegments: number;
  isSelected: boolean;
  onSelect: (id: string) => void;
  moveSegment: (id: string, dir: "up" | "down") => void;
  deleteSegment: (id: string) => void;
  addPage: (title?: string) => void;
}

import { ReactNodeViewRenderer } from "@tiptap/react";
import { ResizableImageNode } from "./ResizableImageNode";

const CustomImage = Image.extend({
  draggable: true,
  addAttributes() {
    return {
      ...this.parent?.(),
      alignment: {
        default: "center",
        parseHTML: (element) => element.getAttribute("data-alignment") || "center",
        renderHTML: (attributes) => {
          return {
            "data-alignment": attributes.alignment,
            class: `img-align-${attributes.alignment}`,
          };
        },
      },
      width: {
        default: "100%",
        parseHTML: (element) => element.getAttribute("data-width") || element.style.width || "100%",
        renderHTML: (attributes) => {
          return {
            "data-width": attributes.width,
            style: `width: ${attributes.width}`,
          };
        },
      },
    };
  },
  addNodeView() {
    return ReactNodeViewRenderer(ResizableImageNode);
  },
});

const TIPTAP_EXTENSIONS = [
  StarterKit,
  Table.configure({ resizable: true }),
  TableRow,
  TableCell,
  TableHeader,
  CustomImage,
  CitationNode,
  Subscript,
  Superscript,
  TextStyle,
  Color,
  TextAlign.configure({ types: ["heading", "paragraph"] }),
];

const SegmentBlock = memo(function SegmentBlock({
  segment,
  index,
  totalSegments,
  isSelected,
  onSelect,
  moveSegment,
  deleteSegment,
  addPage,
}: SegmentBlockProps) {
  const bodyRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<any>(null);
  const setActiveEditor = useWizardStore((s) => s.setActiveEditor);
  const updateSegment = useWizardStore((s) => s.updateSegment);
  const dismissComplianceWarning = useWizardStore((s) => s.dismissComplianceWarning);

  const updateTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isInternalUpdateRef = useRef(false);

  const editor = useEditor({
    extensions: TIPTAP_EXTENSIONS,
    content: segment.content,
    editable: true,
    onFocus: ({ editor }) => setActiveEditor(editor),
    onUpdate: ({ editor }) => {
      isInternalUpdateRef.current = true;
      if (updateTimeoutRef.current) clearTimeout(updateTimeoutRef.current);
      updateTimeoutRef.current = setTimeout(() => {
        const updatedJson = editor.getJSON();
        updateSegment({
          ...segment,
          content: updatedJson,
        });
        isInternalUpdateRef.current = false;
      }, 250);
    },
    onBlur: ({ editor }) => {
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }
      const updatedJson = editor.getJSON();
      updateSegment({
        ...segment,
        content: updatedJson,
      });
      isInternalUpdateRef.current = false;
    },
  });

  editorRef.current = editor;

  useEffect(() => {
    return () => {
      if (updateTimeoutRef.current) {
        clearTimeout(updateTimeoutRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (editor && !editor.isDestroyed) {
      const currentActive = useWizardStore.getState().activeEditor;
      if (isSelected || (index === 0 && (!currentActive || currentActive.isDestroyed))) {
        setActiveEditor(editor);
      }
    }
  }, [editor, isSelected, index, setActiveEditor]);

  useEffect(() => {
    if (editor && segment.content && !isInternalUpdateRef.current) {
      if (typeof segment.content === "string") {
        const currentHTML = editor.getHTML();
        if (segment.content !== currentHTML) {
          editor.commands.setContent(segment.content);
        }
      } else if (typeof segment.content === "object") {
        const currentJSON = editor.getJSON();
        if (JSON.stringify(currentJSON) !== JSON.stringify(segment.content)) {
          editor.commands.setContent(segment.content);
        }
      }
    }
  }, [editor, segment.content]);

  const styleConfig = useWizardStore((s) => s.styleConfig);

  const showNumbers = styleConfig.showPageNumbers !== false;
  const numPos = styleConfig.pageNumberPosition || "bottom-right";

  return (
    <div
      className={`segment-block ${isSelected ? "segment-block--selected" : ""}`}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(segment.segment_id);
        if (editor) {
          setActiveEditor(editor);
          if (!editor.isFocused) {
            editor.commands.focus();
          }
        }
      }}
      onKeyDown={(e) => {
        if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault();
          addPage();
        } else if (e.key === "Backspace" && editor && editor.state.selection.empty && editor.state.selection.from === 1 && index > 0) {
          // If page is empty or backspacing at position 1 of non-first page, delete empty page
          const textLength = editor.getText().trim().length;
          if (textLength === 0) {
            e.preventDefault();
            deleteSegment(segment.segment_id);
          }
        }
      }}
      data-segment-id={segment.segment_id}
      style={{
        position: "relative",
        overflow: "visible",
        height: "auto",
        backgroundColor: styleConfig.pageColor || "#ffffff",
        border: styleConfig.pageBorder && styleConfig.pageBorder !== "none" ? styleConfig.pageBorder : undefined,
      }}
    >
      {/* PER-PAGE WATERMARK OVERLAY - VISIBLE ON EVERY PAGE CARD */}
      {styleConfig.watermark && (
        <div
          className="page-watermark-overlay"
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%) rotate(-30deg)",
            fontSize: "54px",
            fontWeight: "800",
            color: styleConfig.pageColor === "#1e1e2e" ? "rgba(255, 255, 255, 0.12)" : "rgba(15, 23, 42, 0.09)",
            pointerEvents: "none",
            zIndex: 3,
            whiteSpace: "nowrap",
            textTransform: "uppercase",
            userSelect: "none",
            letterSpacing: "6px",
            width: "100%",
            textAlign: "center",
          }}
        >
          {styleConfig.watermark}
        </div>
      )}

      <div className="page-card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 12px", background: "#f8f9fa", borderBottom: "1px solid #e0e0e0", borderRadius: "8px 8px 0 0", marginBottom: "8px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "11px", fontWeight: 700, background: "#e8f0fe", color: "#1a73e8", padding: "2px 8px", borderRadius: "10px" }}>
            PAGE {index + 1}
          </span>
          <span style={{ fontSize: "12px", fontWeight: 600, color: "#3c4043" }}>{segment.name}</span>
        </div>

        {/* Top Right Page Number Option */}
        {showNumbers && numPos === "top-right" && (
          <span style={{ fontSize: "11px", fontWeight: 600, color: "#6b7280", background: "#f1f5f9", padding: "2px 6px", borderRadius: "4px" }}>
            Page {index + 1} of {totalSegments}
          </span>
        )}

        <div style={{ display: "flex", gap: "4px" }}>
          <button
            style={{ padding: "2px 8px", fontSize: "11px", cursor: index === 0 ? "default" : "pointer", opacity: index === 0 ? 0.4 : 1, background: "#fff", border: "1px solid #ccc", borderRadius: "4px" }}
            disabled={index === 0}
            onClick={(e) => {
              e.stopPropagation();
              moveSegment(segment.segment_id, "up");
            }}
            title="Move Page Up"
          >
            ▲ Up
          </button>
          <button
            style={{ padding: "2px 8px", fontSize: "11px", cursor: index === totalSegments - 1 ? "default" : "pointer", opacity: index === totalSegments - 1 ? 0.4 : 1, background: "#fff", border: "1px solid #ccc", borderRadius: "4px" }}
            disabled={index === totalSegments - 1}
            onClick={(e) => {
              e.stopPropagation();
              moveSegment(segment.segment_id, "down");
            }}
            title="Move Page Down"
          >
            ▼ Down
          </button>
          {totalSegments > 1 && (
            <button
              style={{ padding: "2px 8px", fontSize: "11px", cursor: "pointer", background: "#fff5f5", color: "#d93025", border: "1px solid #fce8e6", borderRadius: "4px" }}
              onClick={(e) => {
                e.stopPropagation();
                if (confirm(`Delete Page ${index + 1} (${segment.name})?`)) {
                  deleteSegment(segment.segment_id);
                }
              }}
              title="Delete Page"
            >
              ✕ Delete
            </button>
          )}
        </div>
      </div>

      {segment.compliance_flag && (
        <div
          className="compliance-banner"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "12px",
          }}
        >
          <span>⚠️ <strong>Compliance Warning:</strong> {segment.compliance_note || "Ungrounded clause detected."}</span>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              dismissComplianceWarning(segment.segment_id);
            }}
            style={{
              background: "rgba(146, 64, 14, 0.12)",
              border: "1px solid rgba(146, 64, 14, 0.3)",
              color: "#92400e",
              borderRadius: "4px",
              padding: "2px 8px",
              fontSize: "11px",
              fontWeight: 600,
              cursor: "pointer",
              whiteSpace: "nowrap",
            }}
            title="Dismiss this warning"
          >
            ✕ Dismiss
          </button>
        </div>
      )}

      <div className="segment-block__body" ref={bodyRef} style={{ position: "relative", zIndex: 2 }}>
        <InlineFloatingToolbar editor={editor} segmentId={segment.segment_id} />
        <EditorContent editor={editor} />
      </div>

      {/* PAGE FOOTER - CUSTOMIZABLE PAGE NUMBERING */}
      {showNumbers && numPos !== "none" && numPos !== "top-right" && (
        <div
          className="page-card-footer"
          style={{
            display: "flex",
            justifyContent:
              numPos === "bottom-left"
                ? "flex-start"
                : numPos === "bottom-center"
                ? "center"
                : "flex-end",
            alignItems: "center",
            padding: "8px 16px",
            marginTop: "16px",
            borderTop: "1px solid #f1f3f4",
            fontSize: "11px",
            color: "#6b7280",
            fontWeight: 500,
          }}
        >
          <span>
            Procurement Proposal Document • Page {index + 1} of {totalSegments}
          </span>
        </div>
      )}
    </div>
  );
});

export function SegmentedDocEditor() {
  const {
    segments,
    selectedSegmentId,
    setSelectedSegmentId,
    styleConfig,
    pageLayoutSize,
    zoomLevel,
    layoutMode,
    addPage,
    moveSegment,
    deleteSegment,
    checkpoints,
    selectedVersionId,
    canvasViewMode,
    setCanvasViewMode,
    rollbackToCheckpoint,
    missingFields,
    dismissMissingField,
    updateSegment,
  } = useWizardStore((s) => ({
    segments: s.segments,
    selectedSegmentId: s.selectedSegmentId,
    setSelectedSegmentId: s.setSelectedSegmentId,
    styleConfig: s.styleConfig,
    pageLayoutSize: s.pageLayoutSize,
    zoomLevel: s.zoomLevel,
    layoutMode: s.layoutMode,
    addPage: s.addPage,
    moveSegment: s.moveSegment,
    deleteSegment: s.deleteSegment,
    checkpoints: s.checkpoints,
    selectedVersionId: s.selectedVersionId,
    canvasViewMode: s.canvasViewMode,
    setCanvasViewMode: s.setCanvasViewMode,
    rollbackToCheckpoint: s.rollbackToCheckpoint,
    missingFields: s.missingFields,
    dismissMissingField: s.dismissMissingField,
    updateSegment: s.updateSegment,
  }));

  const [editingField, setEditingField] = useState<string | null>(null);
  const [fieldValue, setFieldValue] = useState("");

  function handleOpenFieldEdit(field: string) {
    setEditingField(field);
    setFieldValue("");
  }

  function handleSaveFieldEdit() {
    if (!editingField || !fieldValue.trim()) return;
    const val = fieldValue.trim();
    const readableField = editingField.replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase());

    // Recursively replace field placeholders in segment AST
    const updatedSegments = segments.map((seg) => {
      if (!seg.content || typeof seg.content !== "object") return seg;
      const rawJson = JSON.stringify(seg.content);
      // Replace variations like "[Buyer Organization]", "[Submission Deadline]", or specific field names
      const regexPatterns = [
        new RegExp(`\\[${editingField}\\]`, "gi"),
        new RegExp(`\\[${readableField}\\]`, "gi"),
        new RegExp(`\\[${editingField.replace(/_/g, " ")}\\]`, "gi"),
      ];
      let replacedJson = rawJson;
      for (const rx of regexPatterns) {
        replacedJson = replacedJson.replace(rx, val);
      }
      if (replacedJson !== rawJson) {
        try {
          return {
            ...seg,
            content: JSON.parse(replacedJson),
          };
        } catch {
          return seg;
        }
      }
      return seg;
    });

    for (const seg of updatedSegments) {
      updateSegment(seg);
    }

    dismissMissingField(editingField);
    setEditingField(null);
    setFieldValue("");
  }

  if (!segments || segments.length === 0) {
    return (
      <div className="editor-empty" style={{ textAlign: "center", padding: "40px" }}>
        <p>No document pages generated yet.</p>
        <button
          style={{ padding: "8px 16px", backgroundColor: "#1a73e8", color: "#fff", border: "none", borderRadius: "6px", cursor: "pointer", fontSize: "14px", marginTop: "12px" }}
          onClick={() => addPage("Page 1")}
        >
          ➕ Create First Page
        </button>
      </div>
    );
  }

  return (
    <div
      className={`segmented-doc-editor page-layout-${pageLayoutSize.toLowerCase()} view-mode-${layoutMode}`}
      onClick={() => {
        setSelectedSegmentId(null);
        const ed = useWizardStore.getState().activeEditor;
        if (ed) ed.commands.blur();
      }}
      style={
        {
          "--doc-font-family": styleConfig.fontFamily,
          "--doc-font-size": styleConfig.fontSize,
          "--doc-accent-color": styleConfig.accentColor,
          lineHeight: styleConfig.paragraphSpacing || "1.4",
          position: "relative",
          transform: `scale(${zoomLevel / 100})`,
          transformOrigin: "top center",
          transition: "transform 0.2s ease-in-out",
        } as React.CSSProperties
      }
    >
      {styleConfig.watermark && (
        <div
          className="document-watermark-overlay"
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%) rotate(-45deg)",
            fontSize: "90px",
            fontWeight: "800",
            color: "rgba(0, 0, 0, 0.05)",
            pointerEvents: "none",
            zIndex: 10,
            whiteSpace: "nowrap",
            textTransform: "uppercase",
            userSelect: "none",
          }}
        >
          {styleConfig.watermark}
        </div>
      )}
      <div
        className="canvas-top-control-bar"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "8px 14px",
          backgroundColor: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: "8px",
          marginBottom: "16px",
          boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Visual Rich Text vs. Formatted Markdown Toggle */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span style={{ fontSize: "12px", fontWeight: 600, color: "#64748b" }}>Mode:</span>
          <div
            style={{
              display: "inline-flex",
              backgroundColor: "#e2e8f0",
              borderRadius: "6px",
              padding: "2px",
            }}
          >
            <button
              style={{
                padding: "3px 10px",
                fontSize: "12px",
                fontWeight: 600,
                borderRadius: "4px",
                border: "none",
                cursor: "pointer",
                backgroundColor: canvasViewMode === "visual" ? "#ffffff" : "transparent",
                color: canvasViewMode === "visual" ? "#0284c7" : "#64748b",
                boxShadow: canvasViewMode === "visual" ? "0 1px 2px rgba(0,0,0,0.1)" : "none",
              }}
              onClick={() => setCanvasViewMode("visual")}
            >
              👁️ Visual Rich Text
            </button>
            <button
              style={{
                padding: "3px 10px",
                fontSize: "12px",
                fontWeight: 600,
                borderRadius: "4px",
                border: "none",
                cursor: "pointer",
                backgroundColor: canvasViewMode === "markdown" ? "#ffffff" : "transparent",
                color: canvasViewMode === "markdown" ? "#0284c7" : "#64748b",
                boxShadow: canvasViewMode === "markdown" ? "0 1px 2px rgba(0,0,0,0.1)" : "none",
              }}
              onClick={() => setCanvasViewMode("markdown")}
            >
              📝 Formatted Markdown
            </button>
          </div>
        </div>

        {/* Document Version Checkpoints Timeline Selector */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "12px", fontWeight: 600, color: "#64748b" }}>Version Checkpoints:</span>
          <select
            value={selectedVersionId || (checkpoints[0]?.version_id ?? "")}
            onChange={(e) => rollbackToCheckpoint(e.target.value)}
            disabled={checkpoints.length === 0}
            style={{
              fontSize: "12px",
              padding: "4px 8px",
              borderRadius: "6px",
              border: "1px solid #cbd5e1",
              backgroundColor: "#ffffff",
              color: "#1e293b",
              fontWeight: 500,
              cursor: checkpoints.length > 0 ? "pointer" : "default",
            }}
          >
            {checkpoints.length === 0 ? (
              <option value="">No checkpoints yet</option>
            ) : (
              checkpoints.map((cp) => (
                <option key={cp.version_id} value={cp.version_id}>
                  {cp.label} ({new Date(cp.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}) [{cp.trigger}]
                </option>
              ))
            )}
          </select>
        </div>
      </div>

      {/* Missing Ground-Truth Fields Review Banner */}
      {missingFields && missingFields.length > 0 && (
        <div
          style={{
            backgroundColor: "#fffbeb",
            border: "1px solid #fef3c7",
            borderLeft: "4px solid #f59e0b",
            borderRadius: "8px",
            padding: "10px 14px",
            marginBottom: "16px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            boxShadow: "0 1px 3px rgba(245, 158, 11, 0.1)",
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
            <span style={{ fontSize: "16px" }}>⚠️</span>
            <div>
              <span style={{ fontSize: "12px", fontWeight: 700, color: "#92400e" }}>
                Human Review Recommended:
              </span>
              <span style={{ fontSize: "12px", color: "#b45309", marginLeft: "6px" }}>
                The following required parameters were unmentioned in the prompt and assigned standard enterprise defaults:
              </span>
            </div>
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
              {missingFields.map((field: string) => (
                <span
                  key={field}
                  onClick={() => handleOpenFieldEdit(field)}
                  title="Click to fill in real value and auto-update canvas"
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "3px 8px",
                    borderRadius: "12px",
                    fontSize: "11px",
                    fontWeight: 600,
                    backgroundColor: "#fef3c7",
                    color: "#78350f",
                    border: "1px solid #fde68a",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                >
                  <span>✏️ {field.replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase())}</span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      dismissMissingField(field);
                    }}
                    title="Dismiss warning"
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "#92400e",
                      cursor: "pointer",
                      padding: 0,
                      fontSize: "11px",
                      lineHeight: 1,
                    }}
                  >
                    ✕
                  </button>
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Quick-Edit Modal for Missing Field */}
      {editingField && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(15, 23, 42, 0.6)",
            backdropFilter: "blur(4px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 99999,
          }}
          onClick={() => setEditingField(null)}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: "12px",
              padding: "24px",
              width: "420px",
              maxWidth: "90vw",
              boxShadow: "0 20px 40px rgba(0,0,0,0.25)",
              border: "1px solid #e2e8f0",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ margin: "0 0 8px 0", fontSize: "16px", fontWeight: 700, color: "#0f172a" }}>
              Update Parameter: {editingField.replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase())}
            </h3>
            <p style={{ margin: "0 0 16px 0", fontSize: "12px", color: "#64748b", lineHeight: 1.4 }}>
              Enter the exact value to replace default placeholders across all document segments on the canvas.
            </p>
            <input
              type="text"
              autoFocus
              value={fieldValue}
              placeholder={`Enter real ${editingField.replace(/_/g, " ")}...`}
              onChange={(e) => setFieldValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSaveFieldEdit();
                if (e.key === "Escape") setEditingField(null);
              }}
              style={{
                width: "100%",
                padding: "8px 12px",
                fontSize: "13px",
                borderRadius: "6px",
                border: "1px solid #cbd5e1",
                marginBottom: "16px",
                boxSizing: "border-box",
              }}
            />
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
              <button
                type="button"
                onClick={() => setEditingField(null)}
                style={{
                  padding: "6px 12px",
                  fontSize: "12px",
                  borderRadius: "6px",
                  border: "1px solid #cbd5e1",
                  background: "#f8fafc",
                  color: "#475569",
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveFieldEdit}
                disabled={!fieldValue.trim()}
                style={{
                  padding: "6px 14px",
                  fontSize: "12px",
                  fontWeight: 600,
                  borderRadius: "6px",
                  border: "none",
                  background: "#2563eb",
                  color: "#ffffff",
                  cursor: fieldValue.trim() ? "pointer" : "not-allowed",
                  opacity: fieldValue.trim() ? 1 : 0.6,
                }}
              >
                Apply to Canvas
              </button>
            </div>
          </div>
        </div>
      )}

      {canvasViewMode === "markdown" ? (
        <div
          className="canvas-markdown-preview"
          style={{
            backgroundColor: "#ffffff",
            padding: "24px 32px",
            borderRadius: "8px",
            border: "1px solid #e2e8f0",
            fontFamily: "monospace",
            whiteSpace: "pre-wrap",
            fontSize: "13px",
            lineHeight: 1.6,
            color: "#0f172a",
            minHeight: "400px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
          }}
        >
          {segments.map((seg) => extractPlainTextFromSegment(seg)).join("\n\n---\n\n")}
        </div>
      ) : (
        <>
          <DocRuler />
          {segments.map((segment: DocumentSegment, idx: number) => (
            <SegmentBlock
              key={segment.segment_id}
              segment={segment}
              index={idx}
              totalSegments={segments.length}
              isSelected={selectedSegmentId === segment.segment_id}
              onSelect={setSelectedSegmentId}
              moveSegment={moveSegment}
              deleteSegment={deleteSegment}
              addPage={addPage}
            />
          ))}
        </>
      )}

      {/* Add New Page Button Canvas Controls */}
      <div style={{ display: "flex", justifyContent: "center", margin: "24px 0" }}>
        <button
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 24px",
            backgroundColor: "#1a73e8",
            color: "#ffffff",
            border: "none",
            borderRadius: "24px",
            fontSize: "14px",
            fontWeight: 600,
            cursor: "pointer",
            boxShadow: "0 2px 6px rgba(26, 115, 232, 0.3)",
            transition: "all 0.2s ease",
          }}
          onClick={(e) => {
            e.stopPropagation();
            addPage();
          }}
        >
          <span>➕</span>
          <span>Add New Page</span>
        </button>
      </div>

      <ContextMenu onClose={() => {}} />
    </div>
  );
}
