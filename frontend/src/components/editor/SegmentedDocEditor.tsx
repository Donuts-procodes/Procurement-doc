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
import { useEffect, memo, useRef, useCallback } from "react";
import { useWizardStore } from "../../state/wizardStore";
import { ContextMenu } from "./ContextMenu";
import { DocRuler } from "./DocRuler";
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
  const segments = useWizardStore((s) => s.segments);
  const pageLayoutSize = useWizardStore((s) => s.pageLayoutSize);

  const checkOverflowAndPaginate = useCallback(() => {
    const ed = editorRef.current;
    if (!bodyRef.current || !ed) return;
    
    // Dynamic pagination thresholds based on CSS min-heights (with ~143px padding allowance)
    let maxBodyHeight = 980; // A4 default (1123 - 143)
    const layout = pageLayoutSize?.toLowerCase() || "a4";
    if (layout === "letter") maxBodyHeight = 913; // (1056 - 143)
    else if (layout === "legal") maxBodyHeight = 1201; // (1344 - 143)
    else if (layout === "a3") maxBodyHeight = 1444; // (1587 - 143)
    
    const bodyHeight = bodyRef.current.scrollHeight;

    if (bodyHeight > maxBodyHeight) {
      const json = ed.getJSON();
      const contentNodes = json.content || [];
      if (contentNodes.length > 1) {
        const overflowNode = contentNodes.pop();
        ed.commands.setContent({ type: "doc", content: contentNodes });

        if (index < totalSegments - 1) {
          const nextPage = segments[index + 1];
          const nextJSON = typeof nextPage.content === "object" && nextPage.content ? nextPage.content : { type: "doc", content: [] };
          const nextContent = (nextJSON as any).content || [];
          updateSegment({
            ...nextPage,
            content: { type: "doc", content: [overflowNode, ...nextContent] },
          });
        } else {
          addPage();
        }
      }
    }
  }, [segment, index, totalSegments, segments, updateSegment, addPage, pageLayoutSize]);

  const editor = useEditor({
    extensions: TIPTAP_EXTENSIONS,
    content: segment.content,
    editable: true,
    onFocus: ({ editor }) => setActiveEditor(editor),
    onUpdate: () => {
      checkOverflowAndPaginate();
    },
  });

  editorRef.current = editor;

  useEffect(() => {
    if (editor && isSelected) {
      setActiveEditor(editor);
    }
  }, [editor, isSelected, setActiveEditor]);

  useEffect(() => {
    if (editor && segment.content) {
      const currentHTML = editor.getHTML();
      if (typeof segment.content === "string" && segment.content !== currentHTML) {
        editor.commands.setContent(segment.content);
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
        if (editor) setActiveEditor(editor);
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
        overflow: "hidden",
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
        <div className="compliance-banner">
          ⚠️ Compliance Warning: {segment.compliance_note || "Ungrounded clause detected."}
        </div>
      )}

      <div className="segment-block__body" ref={bodyRef} style={{ position: "relative", zIndex: 2 }}>
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
  }));

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
