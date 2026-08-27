import { useRef, useState } from "react";
import { uploadKnowledgeFiles } from "../../api/client";
import { useWizardStore } from "../../state/wizardStore";

export function StepKnowledgeBase() {
  const setKnowledgeBase = useWizardStore((s) => s.setKnowledgeBase);
  const setStep = useWizardStore((s) => s.setStep);
  const setError = useWizardStore((s) => s.setError);
  const error = useWizardStore((s) => s.error);
  const isDarkMode = useWizardStore((s) => s.isDarkMode);

  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFilesSelected(fileList: FileList | null) {
    if (!fileList) return;
    setSelectedFiles(Array.from(fileList));
  }

  async function handleUpload() {
    if (selectedFiles.length === 0) {
      setError("Add at least one file, or skip this step.");
      return;
    }
    setUploading(true);
    try {
      const result = await uploadKnowledgeFiles(selectedFiles);
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
        PDF, DOCX, TXT, or MD files. The RAG pipeline retrieves from these while writing your document.
      </p>

      <div className="dropzone" onClick={() => inputRef.current?.click()}>
        <input
          ref={inputRef}
          type="file"
          multiple
          hidden
          accept=".pdf,.docx,.txt,.md"
          onChange={(e) => handleFilesSelected(e.target.files)}
        />
        {selectedFiles.length === 0 ? (
          <span>Click to choose files</span>
        ) : (
          <ul>
            {selectedFiles.map((f) => (
              <li key={f.name}>{f.name}</li>
            ))}
          </ul>
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
          {uploading ? "Uploading..." : "Continue"}
        </button>
      </div>
    </div>
  );
}
