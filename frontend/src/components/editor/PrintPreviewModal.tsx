import { createPortal } from "react-dom";
import { useWizardStore } from "../../state/wizardStore";
import { extractHtmlFromSegment } from "../../utils/exportUtils";

interface PrintPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirmDownload: (format: "pdf" | "doc" | "txt") => void;
}

export function PrintPreviewModal({ isOpen, onClose, onConfirmDownload }: PrintPreviewModalProps) {
  const { documentId, segments, styleConfig, pageLayoutSize, isDarkMode } = useWizardStore((s) => ({
    documentId: s.documentId,
    segments: s.segments,
    styleConfig: s.styleConfig,
    pageLayoutSize: s.pageLayoutSize,
    isDarkMode: s.isDarkMode,
  }));

  if (!isOpen) return null;

  return createPortal(
    <div className="preview-modal-overlay">
      <div className="preview-modal">
        <div className="preview-modal__header">
          <h2>Print & Document Download Preview</h2>
          <div className="preview-modal__actions">
            <button
              className="secondary-button"
              onClick={() => onConfirmDownload("pdf")}
              style={{
                color: isDarkMode ? "#f8fafc" : "#1e293b",
                background: isDarkMode ? "rgba(255,255,255,0.08)" : "#ffffff",
                borderColor: isDarkMode ? "rgba(255,255,255,0.25)" : "#cbd5e1",
                fontWeight: 600,
              }}
            >
              Print / Download PDF
            </button>
            <button
              className="secondary-button"
              onClick={() => onConfirmDownload("doc")}
              style={{
                color: isDarkMode ? "#f8fafc" : "#1e293b",
                background: isDarkMode ? "rgba(255,255,255,0.08)" : "#ffffff",
                borderColor: isDarkMode ? "rgba(255,255,255,0.25)" : "#cbd5e1",
                fontWeight: 600,
              }}
            >
              Download Word (.doc)
            </button>
            <button
              className="secondary-button"
              onClick={() => onConfirmDownload("txt")}
              style={{
                color: isDarkMode ? "#f8fafc" : "#1e293b",
                background: isDarkMode ? "rgba(255,255,255,0.08)" : "#ffffff",
                borderColor: isDarkMode ? "rgba(255,255,255,0.25)" : "#cbd5e1",
                fontWeight: 600,
              }}
            >
              Download Text (.txt)
            </button>
            <button className="close-button" onClick={onClose}>
              Close
            </button>
          </div>
        </div>

        <div className="preview-modal__body">
          <div
            className={`preview-page page-layout-${pageLayoutSize.toLowerCase()}`}
            style={
              {
                "--doc-font-family": styleConfig.fontFamily,
                "--doc-font-size": styleConfig.fontSize,
                "--doc-accent-color": styleConfig.accentColor,
                backgroundColor: styleConfig.pageColor || "#ffffff",
                border: styleConfig.pageBorder !== "none" ? styleConfig.pageBorder : undefined,
                lineHeight: styleConfig.paragraphSpacing || "1.4",
                position: "relative",
                overflow: "hidden",
              } as React.CSSProperties
            }
          >
            {styleConfig.watermark && (
              <div
                style={{
                  position: "absolute",
                  top: "50%",
                  left: "50%",
                  transform: "translate(-50%, -50%) rotate(-45deg)",
                  fontSize: "80px",
                  fontWeight: "bold",
                  color: "rgba(0, 0, 0, 0.06)",
                  pointerEvents: "none",
                  zIndex: 10,
                  whiteSpace: "nowrap",
                  textTransform: "uppercase",
                }}
              >
                {styleConfig.watermark}
              </div>
            )}
            <div className="preview-page__header-badge">
              <span>DOCUMENT ID: {documentId || "DRAFT"}</span>
              <span>Layout: {pageLayoutSize}</span>
            </div>

            {segments.map((seg) => (
              <div key={seg.segment_id} className="preview-segment-block">
                <h3 className="preview-segment-title">{seg.name}</h3>
                <div
                  className="preview-segment-content"
                  dangerouslySetInnerHTML={{ __html: extractHtmlFromSegment(seg) }}
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
