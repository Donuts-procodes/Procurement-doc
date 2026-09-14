import { useRef, useState, type DragEvent } from "react";
import { uploadKnowledgeFiles } from "../../api/client";
import { useWizardStore } from "../../state/wizardStore";

export function StepKnowledgeBase() {
  const setKnowledgeBase = useWizardStore((s) => s.setKnowledgeBase);
  const kbId = useWizardStore((s) => s.kbId);
  const setStep = useWizardStore((s) => s.setStep);
  const setError = useWizardStore((s) => s.setError);
  const error = useWizardStore((s) => s.error);
  const isDarkMode = useWizardStore((s) => s.isDarkMode);

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFilesSelected(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) return;
    const incoming = Array.from(fileList);
    setSelectedFiles((prev) => {
      const existingKeys = new Set(prev.map((f) => `${f.name}_${f.size}`));
      const uniqueIncoming = incoming.filter((f) => !existingKeys.has(`${f.name}_${f.size}`));
      return [...prev, ...uniqueIncoming];
    });
    setError(null);
  }

  function handleRemoveFile(indexToRemove: number) {
    setSelectedFiles((prev) => prev.filter((_, idx) => idx !== indexToRemove));
  }

  function handleClearAll() {
    setSelectedFiles([]);
    if (inputRef.current) inputRef.current.value = "";
  }

  function onDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(true);
  }

  function onDragLeave(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      handleFilesSelected(e.dataTransfer.files);
    }
  }

  function formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  async function handleUpload() {
    if (selectedFiles.length === 0) {
      setError("Add at least one file, or skip this step.");
      return;
    }
    setUploading(true);
    try {
      const result = await uploadKnowledgeFiles(selectedFiles, kbId || undefined);
      setKnowledgeBase(result.kb_id, result.files);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="wizard-step">
      <h2>Add knowledge base files</h2>
      <p className="wizard-step__subtitle">
        Upload one or multiple PDF, DOCX, TXT, or MD files. The RAG pipeline indexes and cross-references all files during generation.
      </p>

      <div
        className="dropzone"
        onClick={() => inputRef.current?.click()}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        style={{
          border: isDragging
            ? "2px dashed #3b82f6"
            : isDarkMode
            ? "2px dashed rgba(255,255,255,0.2)"
            : "2px dashed #cbd5e1",
          background: isDragging
            ? isDarkMode
              ? "rgba(59, 130, 246, 0.15)"
              : "#eff6ff"
            : undefined,
          cursor: "pointer",
          transition: "all 0.2s ease",
        }}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          hidden
          accept=".pdf,.docx,.txt,.md"
          onChange={(e) => {
            handleFilesSelected(e.target.files);
            e.target.value = "";
          }}
        />
        {selectedFiles.length === 0 ? (
          <div style={{ textAlign: "center", padding: "16px 0" }}>
            <span style={{ fontSize: "28px", display: "block", marginBottom: "8px" }}>📁</span>
            <span style={{ fontWeight: 600, display: "block" }}>Click to select multiple files or drag & drop here</span>
            <span style={{ fontSize: "12px", color: isDarkMode ? "#94a3b8" : "#64748b", marginTop: "4px", display: "block" }}>
              Supports batch selection of PDF, DOCX, TXT, MD
            </span>
          </div>
        ) : (
          <div style={{ width: "100%" }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
              <span style={{ fontWeight: 700, fontSize: "13px", color: isDarkMode ? "#60a5fa" : "#2563eb" }}>
                {selectedFiles.length} {selectedFiles.length === 1 ? "file" : "files"} ready for indexing:
              </span>
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  style={{
                    background: isDarkMode ? "rgba(255,255,255,0.1)" : "#e2e8f0",
                    border: "none",
                    borderRadius: "4px",
                    padding: "4px 8px",
                    fontSize: "11px",
                    fontWeight: 600,
                    cursor: "pointer",
                    color: isDarkMode ? "#f8fafc" : "#1e293b",
                  }}
                >
                  + Add More Files
                </button>
                <button
                  type="button"
                  onClick={handleClearAll}
                  style={{
                    background: "none",
                    border: "none",
                    fontSize: "11px",
                    color: isDarkMode ? "#f87171" : "#dc2626",
                    cursor: "pointer",
                    textDecoration: "underline",
                  }}
                >
                  Clear All
                </button>
              </div>
            </div>

            <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "6px", maxHeight: "220px", overflowY: "auto" }}>
              {selectedFiles.map((f, idx) => (
                <li
                  key={`${f.name}_${idx}`}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "6px 12px",
                    borderRadius: "6px",
                    background: isDarkMode ? "rgba(255,255,255,0.06)" : "#f8fafc",
                    border: isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid #e2e8f0",
                    fontSize: "12px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", overflow: "hidden" }}>
                    <span style={{ fontSize: "10px", fontWeight: 700, padding: "2px 5px", borderRadius: "3px", background: "#3b82f6", color: "#fff" }}>
                      {f.name.split(".").pop()?.toUpperCase() || "FILE"}
                    </span>
                    <span style={{ fontWeight: 600, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>
                      {f.name}
                    </span>
                    <span style={{ color: isDarkMode ? "#94a3b8" : "#64748b", fontSize: "11px" }}>
                      ({formatBytes(f.size)})
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveFile(idx)}
                    style={{
                      background: "none",
                      border: "none",
                      color: isDarkMode ? "#f87171" : "#dc2626",
                      fontWeight: 700,
                      cursor: "pointer",
                      padding: "2px 6px",
                      fontSize: "13px",
                    }}
                    title="Remove this file"
                  >
                    ✕
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {error && <p className="error-text">{error}</p>}

      <div className="wizard-step__actions">
        <button
          className="secondary-button"
          onClick={() => setStep("template-config")}
          style={{
            color: isDarkMode ? "#f8fafc" : "#1e293b",
            background: isDarkMode ? "rgba(255,255,255,0.08)" : "#ffffff",
            borderColor: isDarkMode ? "rgba(255,255,255,0.25)" : "#cbd5e1",
            fontWeight: 600,
          }}
        >
          Skip
        </button>
        <button className="primary-button" onClick={handleUpload} disabled={uploading}>
          {uploading ? `Uploading & Indexing ${selectedFiles.length} files...` : "Continue"}
        </button>
      </div>
    </div>
  );
}
