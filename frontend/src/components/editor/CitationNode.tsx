import { Node, mergeAttributes } from "@tiptap/core";
import { ReactNodeViewRenderer, NodeViewWrapper, type NodeViewProps } from "@tiptap/react";
import { useState } from "react";

function CitationComponent({ node }: NodeViewProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { source_id, url, title, snippet } = node.attrs;
  const label = source_id || "1";

  return (
    <NodeViewWrapper as="span" className="citation-pill-wrapper" style={{ display: "inline-block", verticalAlign: "middle" }}>
      <span
        className="citation-pill"
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          minWidth: "18px",
          height: "18px",
          padding: "0 5px",
          margin: "0 2px",
          borderRadius: "9px",
          backgroundColor: "#e0f2fe",
          color: "#0284c7",
          fontSize: "11px",
          fontWeight: 700,
          fontFamily: "sans-serif",
          cursor: "pointer",
          border: "1px solid #bae6fd",
          userSelect: "none",
          position: "relative",
          transition: "all 0.15s ease",
        }}
        title={title ? `${title} (Source ${label})` : `Source ${label}`}
      >
        [{label}]

        {isOpen && (
          <div
            className="citation-popover-card"
            style={{
              position: "absolute",
              bottom: "calc(100% + 6px)",
              left: "50%",
              transform: "translateX(-50%)",
              width: "280px",
              padding: "10px 12px",
              backgroundColor: "#ffffff",
              color: "#1e293b",
              borderRadius: "8px",
              boxShadow: "0 8px 24px rgba(0,0,0,0.18), 0 2px 6px rgba(0,0,0,0.08)",
              border: "1px solid #e2e8f0",
              zIndex: 99999,
              textAlign: "left",
              whiteSpace: "normal",
              cursor: "default",
              lineHeight: 1.4,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
              <span style={{ fontSize: "11px", fontWeight: 700, color: "#0284c7", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                Source [{label}]
              </span>
              {url && (
                <a
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ fontSize: "11px", color: "#2563eb", textDecoration: "underline" }}
                >
                  View Link ↗
                </a>
              )}
            </div>

            {title && (
              <div style={{ fontSize: "12px", fontWeight: 600, color: "#0f172a", marginBottom: "4px" }}>
                {title}
              </div>
            )}

            {snippet && (
              <div
                style={{
                  fontSize: "11px",
                  color: "#475569",
                  background: "#f8fafc",
                  padding: "6px 8px",
                  borderRadius: "4px",
                  borderLeft: "2px solid #38bdf8",
                  fontStyle: "italic",
                  maxHeight: "80px",
                  overflowY: "auto",
                }}
              >
                "{snippet}"
              </div>
            )}
          </div>
        )}
      </span>
    </NodeViewWrapper>
  );
}

export const CitationNode = Node.create({
  name: "citation",
  group: "inline",
  inline: true,
  atom: true,

  addAttributes() {
    return {
      source_id: {
        default: "1",
        parseHTML: (element) => element.getAttribute("data-source-id"),
        renderHTML: (attributes) => ({ "data-source-id": attributes.source_id }),
      },
      url: {
        default: "",
        parseHTML: (element) => element.getAttribute("data-url"),
        renderHTML: (attributes) => ({ "data-url": attributes.url }),
      },
      title: {
        default: "",
        parseHTML: (element) => element.getAttribute("data-title"),
        renderHTML: (attributes) => ({ "data-title": attributes.title }),
      },
      snippet: {
        default: "",
        parseHTML: (element) => element.getAttribute("data-snippet"),
        renderHTML: (attributes) => ({ "data-snippet": attributes.snippet }),
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: "span[data-source-id]",
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return ["span", mergeAttributes(HTMLAttributes, { class: "citation-pill" }), `[${HTMLAttributes["data-source-id"] || 1}]`];
  },

  addNodeView() {
    return ReactNodeViewRenderer(CitationComponent);
  },
});
