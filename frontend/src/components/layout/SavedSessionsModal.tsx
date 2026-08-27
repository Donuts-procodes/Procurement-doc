import { createPortal } from "react-dom";
import { useWizardStore } from "../../state/wizardStore";
import type { SavedSession } from "../../types";

interface SavedSessionsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SavedSessionsModal({ isOpen, onClose }: SavedSessionsModalProps) {
  const { savedSessions, loadSession, deleteSavedSession, startNewSession, isDarkMode } = useWizardStore((s) => ({
    savedSessions: s.savedSessions,
    loadSession: s.loadSession,
    deleteSavedSession: s.deleteSavedSession,
    startNewSession: s.startNewSession,
    isDarkMode: s.isDarkMode,
  }));

  if (!isOpen) return null;

  return createPortal(
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.7)",
        backdropFilter: "blur(6px)",
        zIndex: 999999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: isDarkMode ? "#1e293b" : "#ffffff",
          borderRadius: "12px",
          width: "100%",
          maxWidth: "750px",
          maxHeight: "85vh",
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 10px 30px rgba(0, 0, 0, 0.2)",
          border: isDarkMode ? "1px solid rgba(255, 255, 255, 0.1)" : "none",
          overflow: "hidden",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "16px 24px",
            borderBottom: isDarkMode ? "1px solid rgba(255, 255, 255, 0.1)" : "1px solid #e0e0e0",
            backgroundColor: isDarkMode ? "rgba(255, 255, 255, 0.03)" : "#f8f9fa",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "20px" }}>📁</span>
            <div>
              <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 700, color: isDarkMode ? "#f8fafc" : "#1f2937" }}>
                Saved Sessions & Workspaces
              </h3>
              <p style={{ margin: 0, fontSize: "12px", color: isDarkMode ? "#94a3b8" : "#6b7280" }}>
                Indexed by Numeric Sequence IDs (#101, #102) • CouchDB JSON Format
              </p>
            </div>
          </div>
          <button
            style={{
              background: "none",
              border: "none",
              fontSize: "18px",
              cursor: "pointer",
              color: isDarkMode ? "#94a3b8" : "#6b7280",
            }}
            onClick={onClose}
          >
            ✕
          </button>
        </div>

        {/* Modal Content / Sessions List */}
        <div style={{ padding: "20px", overflowY: "auto", flex: 1 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "16px" }}>
            <span style={{ fontSize: "13px", fontWeight: 600, color: isDarkMode ? "#e2e8f0" : "#374151" }}>
              {savedSessions.length} Workspace Session{savedSessions.length === 1 ? "" : "s"} Saved
            </span>
            <button
              style={{
                padding: "6px 12px",
                backgroundColor: "#1a73e8",
                color: "#ffffff",
                border: "none",
                borderRadius: "6px",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
              }}
              onClick={() => {
                onClose();
                startNewSession();
              }}
            >
              ➕ Start New Proposal Session
            </button>
          </div>

          {savedSessions.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px 20px", color: isDarkMode ? "#64748b" : "#9ca3af" }}>
              <p style={{ fontSize: "16px", margin: 0 }}>No saved sessions found yet.</p>
              <p style={{ fontSize: "13px", marginTop: "4px" }}>
                Workspaces and document edits auto-save as you generate and edit.
              </p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {savedSessions.map((session: SavedSession) => (
                <div
                  key={session.sessionId || session._id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "16px",
                    border: isDarkMode ? "1px solid rgba(255, 255, 255, 0.1)" : "1px solid #e5e7eb",
                    borderRadius: "8px",
                    backgroundColor: isDarkMode ? "rgba(255, 255, 255, 0.05)" : "#ffffff",
                    transition: "border-color 0.2s ease, box-shadow 0.2s ease",
                  }}
                >
                  <div style={{ flex: 1, paddingRight: "16px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
                      <span
                        style={{
                          backgroundColor: isDarkMode ? "rgba(59, 130, 246, 0.2)" : "#e8f0fe",
                          color: isDarkMode ? "#60a5fa" : "#1a73e8",
                          fontWeight: 700,
                          fontSize: "12px",
                          padding: "2px 8px",
                          borderRadius: "12px",
                        }}
                      >
                        SESSION {session.displayId || `#${session.idNumber}`}
                      </span>
                      <span style={{ fontSize: "11px", color: isDarkMode ? "#94a3b8" : "#6b7280" }}>{session.updatedAt}</span>
                    </div>
                    <div
                      style={{
                        fontSize: "15px",
                        fontWeight: 600,
                        color: isDarkMode ? "#f8fafc" : "#1f2937",
                        marginBottom: "10px",
                        whiteSpace: "nowrap",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                      }}
                    >
                      {session.title || "Untitled Document"}
                    </div>
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", fontSize: "11px" }}>
                      <span
                        style={{
                          backgroundColor: isDarkMode ? "rgba(243, 244, 246, 0.1)" : "#f3f4f6",
                          color: isDarkMode ? "#cbd5e1" : "#4b5563",
                          padding: "2px 6px",
                          borderRadius: "4px",
                        }}
                      >
                        Doc Type: {session.procurementDocType}
                      </span>
                      <span
                        style={{
                          backgroundColor: isDarkMode ? "rgba(243, 244, 246, 0.1)" : "#f3f4f6",
                          color: isDarkMode ? "#cbd5e1" : "#4b5563",
                          padding: "2px 6px",
                          borderRadius: "4px",
                        }}
                      >
                        Layout: {session.pageLayoutSize}
                      </span>
                      {session.segments && session.segments.length > 0 && (
                        <span
                          style={{
                            backgroundColor: isDarkMode ? "rgba(14, 165, 233, 0.1)" : "#e0f2fe",
                            color: isDarkMode ? "#38bdf8" : "#0369a1",
                            padding: "2px 6px",
                            borderRadius: "4px",
                          }}
                        >
                          {session.segments.length} Pages / Segments
                        </span>
                      )}
                      {session.kbFiles && session.kbFiles.length > 0 && (
                        <span
                          style={{
                            backgroundColor: isDarkMode ? "rgba(245, 158, 11, 0.1)" : "#fef3c7",
                            color: isDarkMode ? "#fbbf24" : "#b45309",
                            padding: "2px 6px",
                            borderRadius: "4px",
                          }}
                        >
                          {session.kbFiles.length} KB Files Attached
                        </span>
                      )}
                      {session.promptLog && session.promptLog.length > 0 && (
                        <span
                          style={{
                            backgroundColor: isDarkMode ? "rgba(168, 85, 247, 0.1)" : "#f3e8ff",
                            color: isDarkMode ? "#c084fc" : "#7e22ce",
                            padding: "2px 6px",
                            borderRadius: "4px",
                          }}
                        >
                          {session.promptLog.length} Chat Messages
                        </span>
                      )}
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <button
                      style={{
                        padding: "8px 16px",
                        backgroundColor: "#10b981",
                        color: "#ffffff",
                        border: "none",
                        borderRadius: "6px",
                        fontSize: "13px",
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                      onClick={() => {
                        loadSession(session.sessionId);
                        onClose();
                      }}
                    >
                      📂 Open Workspace
                    </button>
                    <button
                      style={{
                        padding: "8px 10px",
                        backgroundColor: isDarkMode ? "rgba(239, 68, 68, 0.1)" : "#fef2f2",
                        color: isDarkMode ? "#f87171" : "#ef4444",
                        border: isDarkMode ? "1px solid rgba(239, 68, 68, 0.2)" : "1px solid #fecaca",
                        borderRadius: "6px",
                        fontSize: "13px",
                        cursor: "pointer",
                      }}
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteSavedSession(session.sessionId);
                      }}
                      title="Delete Session"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}
