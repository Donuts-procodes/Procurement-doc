import React, { useState, useRef } from "react";
import { NodeViewWrapper, type NodeViewProps } from "@tiptap/react";

export function ResizableImageNode(props: NodeViewProps) {
  const { node, updateAttributes, selected, deleteNode } = props;
  const [isResizing, setIsResizing] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  const src = node.attrs.src;
  const alt = node.attrs.alt || "Document Image / Diagram";
  const alignment = node.attrs.alignment || "center";
  const width = node.attrs.width || "auto";

  const handleAlignmentChange = (newAlign: string) => {
    updateAttributes({ alignment: newAlign });
  };

  const handleMouseDown = (e: React.MouseEvent, corner: string) => {
    e.preventDefault();
    e.stopPropagation();
    setIsResizing(true);

    const startX = e.clientX;
    const startWidth = imgRef.current ? imgRef.current.clientWidth : 300;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = moveEvent.clientX - startX;
      let newWidth = startWidth;

      if (corner === "bottom-right" || corner === "top-right") {
        newWidth = Math.max(100, Math.min(700, startWidth + deltaX));
      } else {
        newWidth = Math.max(100, Math.min(700, startWidth - deltaX));
      }

      updateAttributes({ width: `${newWidth}px` });
    };

    const onMouseUp = () => {
      setIsResizing(false);
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  };

  let alignClass = "img-node-center";
  if (alignment === "left") alignClass = "img-node-left";
  if (alignment === "right") alignClass = "img-node-right";

  return (
    <NodeViewWrapper className={`resizable-image-wrapper ${alignClass}`}>
      <div
        className={`resizable-image-container ${selected ? "is-selected" : ""} ${isResizing ? "is-resizing" : ""}`}
        style={{ width: width, position: "relative", display: "inline-block", maxWidth: "100%" }}
      >
        <img
          ref={imgRef}
          src={src}
          alt={alt}
          style={{
            width: "100%",
            height: "auto",
            display: "block",
            borderRadius: "6px",
            boxShadow: selected ? "0 0 0 2px #1a73e8, 0 4px 12px rgba(0,0,0,0.15)" : "0 2px 6px rgba(0,0,0,0.08)",
            transition: isResizing ? "none" : "box-shadow 0.2s ease",
          }}
          draggable
        />

        {/* Floating Quick Action Toolbar when Selected */}
        {selected && (
          <div
            className="image-action-toolbar"
            style={{
              position: "absolute",
              top: "-42px",
              left: "50%",
              transform: "translateX(-50%)",
              background: "#1e293b",
              color: "#ffffff",
              borderRadius: "6px",
              padding: "4px 8px",
              display: "flex",
              gap: "6px",
              alignItems: "center",
              zIndex: 50,
              boxShadow: "0 4px 12px rgba(0, 0, 0, 0.25)",
              fontSize: "12px",
              whiteSpace: "nowrap",
            }}
          >
            <button
              type="button"
              style={{
                background: alignment === "left" ? "#3b82f6" : "transparent",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                padding: "2px 6px",
                cursor: "pointer",
              }}
              onClick={() => handleAlignmentChange("left")}
              title="Align Left (Wrap Text)"
            >
              ⬅️ Left
            </button>
            <button
              type="button"
              style={{
                background: alignment === "center" ? "#3b82f6" : "transparent",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                padding: "2px 6px",
                cursor: "pointer",
              }}
              onClick={() => handleAlignmentChange("center")}
              title="Center Align"
            >
              ↔️ Center
            </button>
            <button
              type="button"
              style={{
                background: alignment === "right" ? "#3b82f6" : "transparent",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                padding: "2px 6px",
                cursor: "pointer",
              }}
              onClick={() => handleAlignmentChange("right")}
              title="Align Right (Wrap Text)"
            >
              ➡️ Right
            </button>
            <div style={{ width: "1px", height: "14px", background: "#475569" }} />
            <button
              type="button"
              style={{
                background: "#ef4444",
                color: "#fff",
                border: "none",
                borderRadius: "4px",
                padding: "2px 6px",
                cursor: "pointer",
              }}
              onClick={() => deleteNode()}
              title="Delete Image"
            >
              🗑️
            </button>
          </div>
        )}

        {/* Corner Resize Handles */}
        {selected && (
          <>
            <div
              className="resize-handle top-left"
              onMouseDown={(e) => handleMouseDown(e, "top-left")}
              style={{
                position: "absolute",
                top: "-5px",
                left: "-5px",
                width: "10px",
                height: "10px",
                backgroundColor: "#1a73e8",
                border: "1px solid #ffffff",
                borderRadius: "2px",
                cursor: "nwse-resize",
                zIndex: 10,
              }}
            />
            <div
              className="resize-handle top-right"
              onMouseDown={(e) => handleMouseDown(e, "top-right")}
              style={{
                position: "absolute",
                top: "-5px",
                right: "-5px",
                width: "10px",
                height: "10px",
                backgroundColor: "#1a73e8",
                border: "1px solid #ffffff",
                borderRadius: "2px",
                cursor: "nesw-resize",
                zIndex: 10,
              }}
            />
            <div
              className="resize-handle bottom-left"
              onMouseDown={(e) => handleMouseDown(e, "bottom-left")}
              style={{
                position: "absolute",
                bottom: "-5px",
                left: "-5px",
                width: "10px",
                height: "10px",
                backgroundColor: "#1a73e8",
                border: "1px solid #ffffff",
                borderRadius: "2px",
                cursor: "nesw-resize",
                zIndex: 10,
              }}
            />
            <div
              className="resize-handle bottom-right"
              onMouseDown={(e) => handleMouseDown(e, "bottom-right")}
              style={{
                position: "absolute",
                bottom: "-5px",
                right: "-5px",
                width: "10px",
                height: "10px",
                backgroundColor: "#1a73e8",
                border: "1px solid #ffffff",
                borderRadius: "2px",
                cursor: "nwse-resize",
                zIndex: 10,
              }}
            />
          </>
        )}
      </div>
    </NodeViewWrapper>
  );
}
