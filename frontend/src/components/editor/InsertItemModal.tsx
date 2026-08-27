import React, { useState } from "react";
import { createPortal } from "react-dom";
import { useWizardStore } from "../../state/wizardStore";

export type ModalType =
  | "picture"
  | "custom-table"
  | "cover-page"
  | "icons"
  | "symbols"
  | "video"
  | "link"
  | "bookmark"
  | "comment"
  | "header"
  | "wordart"
  | null;

interface InsertItemModalProps {
  type: ModalType;
  onClose: () => void;
  onConfirm: (data: any) => void;
}

export function InsertItemModal({ type, onClose, onConfirm }: InsertItemModalProps) {
  const isDarkMode = useWizardStore((s) => s.isDarkMode);

  // Field states
  const [url, setUrl] = useState("https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&q=80");
  const [rows, setRows] = useState(4);
  const [cols, setCols] = useState(4);
  const [coverStyle, setCoverStyle] = useState("corporate");
  const [selectedIcon, setSelectedIcon] = useState("✓");
  const [selectedSymbol, setSelectedSymbol] = useState("§");
  const [videoUrl, setVideoUrl] = useState("https://www.youtube.com/watch?v=dQw4w9WgXcQ");
  const [linkText, setLinkText] = useState("Enterprise Security SLA");
  const [linkUrl, setLinkUrl] = useState("https://example.com/sla");
  const [bookmarkName, setBookmarkName] = useState("Section_Compliance");
  const [commentText, setCommentText] = useState("Verify compliance against DLD & RFP Section 4.");
  const [headerTitle, setHeaderTitle] = useState("EXECUTIVE PROCUREMENT PROPOSAL");
  const [wordArtText, setWordArtText] = useState("MASTER SPECIFICATION");

  if (!type) return null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (type === "picture") onConfirm({ url });
    else if (type === "custom-table") onConfirm({ rows, cols });
    else if (type === "cover-page") onConfirm({ style: coverStyle });
    else if (type === "icons") onConfirm({ icon: selectedIcon });
    else if (type === "symbols") onConfirm({ symbol: selectedSymbol });
    else if (type === "video") onConfirm({ url: videoUrl });
    else if (type === "link") onConfirm({ text: linkText, url: linkUrl });
    else if (type === "bookmark") onConfirm({ name: bookmarkName });
    else if (type === "comment") onConfirm({ text: commentText });
    else if (type === "header") onConfirm({ title: headerTitle });
    else if (type === "wordart") onConfirm({ text: wordArtText });
    onClose();
  }

  const iconOptions = ["✓", "⚠️", "🔒", "⚡", "🏢", "⭐", "🚀", "🛡️", "📜", "💼", "📊", "🏆"];
  const symbolOptions = ["§", "®", "™", "©", "AED", "$", "€", "¥", "£", "π", "±", "≠"];

  return createPortal(
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: "rgba(0, 0, 0, 0.7)",
        backdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 999999,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: isDarkMode ? "#18181b" : "#ffffff",
          color: isDarkMode ? "#ffffff" : "#1f2937",
          border: isDarkMode ? "1px solid #27272a" : "1px solid #e5e7eb",
          borderRadius: "12px",
          width: "440px",
          maxWidth: "90vw",
          padding: "24px",
          boxShadow: "0 20px 45px rgba(0, 0, 0, 0.4)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 700 }}>
            {type === "picture" && "🖼️ Insert Picture / Image"}
            {type === "custom-table" && "📊 Insert Custom Table"}
            {type === "cover-page" && "📘 Choose Cover Page Preset"}
            {type === "icons" && "🐤 Select Icon"}
            {type === "symbols" && "Ω Select Symbol"}
            {type === "video" && "🎥 Embed Online Video"}
            {type === "link" && "🔗 Insert Hyperlink"}
            {type === "bookmark" && "🚩 Add Bookmark Anchor"}
            {type === "comment" && "💬 Add Reviewer Comment"}
            {type === "header" && "📑 Document Header Title"}
            {type === "wordart" && "🎨 Insert Executive WordArt"}
          </h3>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              fontSize: "18px",
              cursor: "pointer",
              color: isDarkMode ? "#a1a1aa" : "#6b7280",
            }}
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {type === "picture" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <label style={{ fontSize: "13px", fontWeight: 600 }}>Image Source URL:</label>
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: isDarkMode ? "1px solid #3f3f46" : "1px solid #d1d5db",
                  background: isDarkMode ? "#27272a" : "#f9fafb",
                  color: isDarkMode ? "#ffffff" : "#111827",
                  boxSizing: "border-box",
                }}
              />
            </div>
          )}

          {type === "custom-table" && (
            <div style={{ display: "flex", gap: "16px" }}>
              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "13px", fontWeight: 600 }}>Rows:</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={rows}
                  onChange={(e) => setRows(Number(e.target.value))}
                  style={{
                    padding: "8px 12px",
                    borderRadius: "6px",
                    border: isDarkMode ? "1px solid #3f3f46" : "1px solid #d1d5db",
                    background: isDarkMode ? "#27272a" : "#f9fafb",
                    color: isDarkMode ? "#ffffff" : "#111827",
                  }}
                />
              </div>
              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "13px", fontWeight: 600 }}>Columns:</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={cols}
                  onChange={(e) => setCols(Number(e.target.value))}
                  style={{
                    padding: "8px 12px",
                    borderRadius: "6px",
                    border: isDarkMode ? "1px solid #3f3f46" : "1px solid #d1d5db",
                    background: isDarkMode ? "#27272a" : "#f9fafb",
                    color: isDarkMode ? "#ffffff" : "#111827",
                  }}
                />
              </div>
            </div>
          )}

          {type === "cover-page" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <label style={{ fontSize: "13px", fontWeight: 600 }}>Cover Page Template:</label>
              {[
                { id: "corporate", label: "Corporate Executive Blue Banner" },
                { id: "minimal", label: "Minimalist Legal Specification" },
                { id: "tech", label: "Modern Tech Gradient Hero" },
              ].map((item) => (
                <div
                  key={item.id}
                  onClick={() => setCoverStyle(item.id)}
                  style={{
                    padding: "10px 14px",
                    borderRadius: "8px",
                    cursor: "pointer",
                    border: coverStyle === item.id ? "2px solid #2563eb" : isDarkMode ? "1px solid #3f3f46" : "1px solid #e5e7eb",
                    background: coverStyle === item.id ? (isDarkMode ? "#1e293b" : "#eff6ff") : isDarkMode ? "#27272a" : "#f9fafb",
                    fontWeight: coverStyle === item.id ? 600 : 400,
                  }}
                >
                  {item.label}
                </div>
              ))}
            </div>
          )}

          {(type === "icons" || type === "symbols") && (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "10px" }}>
              {(type === "icons" ? iconOptions : symbolOptions).map((item) => {
                const isSelected = type === "icons" ? selectedIcon === item : selectedSymbol === item;
                return (
                  <button
                    key={item}
                    type="button"
                    onClick={() => (type === "icons" ? setSelectedIcon(item) : setSelectedSymbol(item))}
                    style={{
                      fontSize: "20px",
                      padding: "12px",
                      borderRadius: "8px",
                      cursor: "pointer",
                      border: isSelected ? "2px solid #2563eb" : isDarkMode ? "1px solid #3f3f46" : "1px solid #e5e7eb",
                      background: isSelected ? (isDarkMode ? "#1e293b" : "#eff6ff") : isDarkMode ? "#27272a" : "#f9fafb",
                      color: isDarkMode ? "#ffffff" : "#111827",
                    }}
                  >
                    {item}
                  </button>
                );
              })}
            </div>
          )}

          {type === "video" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <label style={{ fontSize: "13px", fontWeight: 600 }}>Video URL (YouTube / Vimeo):</label>
              <input
                type="text"
                value={videoUrl}
                onChange={(e) => setVideoUrl(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: isDarkMode ? "1px solid #3f3f46" : "1px solid #d1d5db",
                  background: isDarkMode ? "#27272a" : "#f9fafb",
                  color: isDarkMode ? "#ffffff" : "#111827",
                  boxSizing: "border-box",
                }}
              />
            </div>
          )}

          {type === "link" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={{ fontSize: "13px", fontWeight: 600 }}>Link Text:</label>
                <input
                  type="text"
                  value={linkText}
                  onChange={(e) => setLinkText(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
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
                <label style={{ fontSize: "13px", fontWeight: 600 }}>Target URL:</label>
                <input
                  type="text"
                  value={linkUrl}
                  onChange={(e) => setLinkUrl(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    marginTop: "4px",
                    borderRadius: "6px",
                    border: isDarkMode ? "1px solid #3f3f46" : "1px solid #d1d5db",
                    background: isDarkMode ? "#27272a" : "#f9fafb",
                    color: isDarkMode ? "#ffffff" : "#111827",
                    boxSizing: "border-box",
                  }}
                />
              </div>
            </div>
          )}

          {type === "bookmark" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <label style={{ fontSize: "13px", fontWeight: 600 }}>Bookmark Anchor Name:</label>
              <input
                type="text"
                value={bookmarkName}
                onChange={(e) => setBookmarkName(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: isDarkMode ? "1px solid #3f3f46" : "1px solid #d1d5db",
                  background: isDarkMode ? "#27272a" : "#f9fafb",
                  color: isDarkMode ? "#ffffff" : "#111827",
                  boxSizing: "border-box",
                }}
              />
            </div>
          )}

          {type === "comment" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <label style={{ fontSize: "13px", fontWeight: 600 }}>Reviewer Note / Comment:</label>
              <textarea
                rows={3}
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: isDarkMode ? "1px solid #3f3f46" : "1px solid #d1d5db",
                  background: isDarkMode ? "#27272a" : "#f9fafb",
                  color: isDarkMode ? "#ffffff" : "#111827",
                  boxSizing: "border-box",
                }}
              />
            </div>
          )}

          {type === "header" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <label style={{ fontSize: "13px", fontWeight: 600 }}>Document Page Header Title:</label>
              <input
                type="text"
                value={headerTitle}
                onChange={(e) => setHeaderTitle(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: isDarkMode ? "1px solid #3f3f46" : "1px solid #d1d5db",
                  background: isDarkMode ? "#27272a" : "#f9fafb",
                  color: isDarkMode ? "#ffffff" : "#111827",
                  boxSizing: "border-box",
                }}
              />
            </div>
          )}

          {type === "wordart" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <label style={{ fontSize: "13px", fontWeight: 600 }}>WordArt Heading Text:</label>
              <input
                type="text"
                value={wordArtText}
                onChange={(e) => setWordArtText(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  borderRadius: "6px",
                  border: isDarkMode ? "1px solid #3f3f46" : "1px solid #d1d5db",
                  background: isDarkMode ? "#27272a" : "#f9fafb",
                  color: isDarkMode ? "#ffffff" : "#111827",
                  boxSizing: "border-box",
                }}
              />
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginTop: "24px" }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                border: isDarkMode ? "1px solid #3f3f46" : "1px solid #d1d5db",
                background: isDarkMode ? "#27272a" : "#f3f4f6",
                color: isDarkMode ? "#ffffff" : "#374151",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{
                padding: "8px 18px",
                borderRadius: "6px",
                border: "none",
                background: "#2563eb",
                color: "#ffffff",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              Insert
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
}
