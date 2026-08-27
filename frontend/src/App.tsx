import { Routes, Route, useNavigate, useLocation } from "react-router-dom";
import { ConfigPanel } from "./components/layout/ConfigPanel";
import { SegmentedDocEditor } from "./components/editor/SegmentedDocEditor";
import { EditorRibbon } from "./components/editor/EditorRibbon";
import { EditorStatusBar } from "./components/editor/EditorStatusBar";
import { PromptPanel } from "./components/panel/PromptPanel";
import { WizardContainer } from "./components/wizard/WizardContainer";
import { SavedSessionsModal } from "./components/layout/SavedSessionsModal";
import { AiConfigModal } from "./components/layout/AiConfigModal";
import { useWizardStore } from "./state/wizardStore";
import { useState } from "react";
import { useKeyboardShortcuts } from "./hooks/useKeyboardShortcuts";

export default function App() {
  const documentId = useWizardStore((s) => s.documentId);
  const setStep = useWizardStore((s) => s.setStep);
  const [isSavedSessionsOpen, setIsSavedSessionsOpen] = useState(false);
  const [isAiConfigOpen, setIsAiConfigOpen] = useState(false);
  const [isLeftCollapsed, setIsLeftCollapsed] = useState(false);
  const [isRightCollapsed, setIsRightCollapsed] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();

  const segments = useWizardStore((s) => s.segments);
  const saveCurrentSession = useWizardStore((s) => s.saveCurrentSession);
  const startNewSession = useWizardStore((s) => s.startNewSession);
  const isDarkMode = useWizardStore((s) => s.isDarkMode);
  const toggleDarkMode = useWizardStore((s) => s.toggleDarkMode);

  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Global Keyboard Shortcuts (Ctrl+S for Save, Ctrl+Z for Undo, Ctrl+Y for Redo)
  useKeyboardShortcuts(setToastMessage);

  function handleNewProposalClick() {
    if (segments && segments.length > 0) {
      const shouldSave = window.confirm(
        "Would you like to save your current workspace session before starting a new proposal?"
      );
      if (shouldSave) {
        saveCurrentSession();
      }
    }
    startNewSession();
    navigate("/");
  }

  return (
    <div className={`app ${isDarkMode ? "app--dark" : ""}`} style={{ position: "relative" }}>
      {toastMessage && (
        <div
          style={{
            position: "fixed",
            top: "16px",
            left: "50%",
            transform: "translateX(-50%)",
            background: "#1e293b",
            color: "#38bdf8",
            border: "1px solid #38bdf8",
            padding: "8px 18px",
            borderRadius: "20px",
            fontSize: "13px",
            fontWeight: 600,
            zIndex: 9999999,
            boxShadow: "0 10px 25px rgba(0,0,0,0.3)",
            animation: "fadeIn 0.2s ease",
          }}
        >
          {toastMessage}
        </div>
      )}
      <header
        className="app__header"
        style={{
          padding: "0 16px",
          height: "46px",
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: isDarkMode ? "#0f172a" : "#ffffff",
          borderBottom: isDarkMode ? "1px solid rgba(255,255,255,0.1)" : "1px solid #e2e8f0",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span
            className="app__logo"
            onClick={handleNewProposalClick}
            style={{ cursor: "pointer", fontSize: "14px", fontWeight: 700, whiteSpace: "nowrap", color: isDarkMode ? "#38bdf8" : "#0284c7" }}
          >
            Procurement RAG
          </span>

          <nav style={{ display: "flex", gap: "6px", fontSize: "12px" }}>
            <button
              style={{
                background: isDarkMode ? "#1e293b" : "#f1f5f9",
                border: isDarkMode ? "1px solid #334155" : "1px solid #cbd5e1",
                padding: "4px 8px",
                borderRadius: "6px",
                cursor: "pointer",
                fontWeight: 600,
                color: isDarkMode ? "#f8fafc" : "#1e293b",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
              onClick={toggleDarkMode}
              title="Toggle Dark Mode / Light Mode"
            >
              <span>{isDarkMode ? "☀️" : "🌙"}</span>
              <span>{isDarkMode ? "Light" : "Dark"}</span>
            </button>

            <button
              style={{
                background: isDarkMode ? "#242428" : "#f1f5f9",
                border: isDarkMode ? "1px solid #3a3a3c" : "1px solid #cbd5e1",
                padding: "4px 8px",
                borderRadius: "6px",
                cursor: "pointer",
                fontWeight: 600,
                color: isDarkMode ? "#ffffff" : "#1e293b",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
              onClick={() => setIsAiConfigOpen(true)}
              title="AI Provider Settings & API Keys"
            >
              <span>⚙️</span>
              <span>AI Config</span>
            </button>

            <button
              style={{
                background: isDarkMode ? "#1e293b" : "#e0f2fe",
                border: isDarkMode ? "1px solid #334155" : "1px solid #bae6fd",
                padding: "4px 8px",
                borderRadius: "6px",
                cursor: "pointer",
                fontWeight: 600,
                color: isDarkMode ? "#60a5fa" : "#0369a1",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
              onClick={() => setIsSavedSessionsOpen(true)}
              title="View & Open Saved Sessions"
            >
              <span>📁</span>
              <span>Sessions</span>
            </button>

            <button
              style={{
                background: location.pathname === "/" ? (isDarkMode ? "#334155" : "#e2e8f0") : "transparent",
                border: "none",
                padding: "4px 8px",
                borderRadius: "6px",
                cursor: "pointer",
                fontWeight: 600,
                color: isDarkMode ? "#f8fafc" : "#1e293b",
              }}
              onClick={handleNewProposalClick}
            >
              ➕ New Proposal
            </button>
            <button
              style={{
                background: location.pathname === "/document" ? (isDarkMode ? "#334155" : "#e2e8f0") : "transparent",
                border: "none",
                padding: "4px 8px",
                borderRadius: "6px",
                cursor: "pointer",
                fontWeight: 600,
                color: isDarkMode ? "#f8fafc" : "#1e293b",
              }}
              onClick={() => {
                setStep("editor");
                navigate("/document");
              }}
            >
              📄 Document Editor
            </button>
          </nav>
        </div>

        {location.pathname === "/document" && (
          <div className="app__header-status" style={{ marginLeft: "auto", paddingLeft: "16px" }}>
            <span
              className="doc-id-badge"
              style={{
                fontSize: "11px",
                fontFamily: "monospace",
                fontWeight: 600,
                color: isDarkMode ? "#94a3b8" : "#64748b",
                background: isDarkMode ? "rgba(255, 255, 255, 0.05)" : "#f1f5f9",
                border: isDarkMode ? "1px solid rgba(255, 255, 255, 0.1)" : "1px solid #e2e8f0",
                padding: "3px 8px",
                borderRadius: "6px",
              }}
            >
              ID: {documentId ? documentId.slice(0, 8) : "Draft"}
            </span>
          </div>
        )}
      </header>

      <Routes>
        <Route
          path="/"
          element={
            <main className="app__main">
              <WizardContainer />
            </main>
          }
        />
        <Route
          path="/document"
          element={
            <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", width: "100%", overflow: "hidden" }}>
              <EditorRibbon onOpenSavedSessions={() => setIsSavedSessionsOpen(true)} />
              <main style={{ flex: 1, minHeight: 0, overflow: "hidden", display: "flex", width: "100%" }}>
                <div
                  className="three-pane-layout"
                  style={{
                    gridTemplateColumns: `${isLeftCollapsed ? "44px" : "260px"} 1fr ${isRightCollapsed ? "44px" : "320px"}`,
                    transition: "grid-template-columns 0.25s ease",
                  }}
                >
                  <ConfigPanel isCollapsed={isLeftCollapsed} onToggleCollapse={() => setIsLeftCollapsed(!isLeftCollapsed)} />
                  <div
                    className="canvas-container"
                    onClick={(e) => {
                      const targetClass = (e.target as HTMLElement).className;
                      if (
                        typeof targetClass === "string" &&
                        (targetClass.includes("canvas-container") || targetClass.includes("segmented-doc-editor"))
                      ) {
                        useWizardStore.getState().setSelectedSegmentId(null);
                        const ed = useWizardStore.getState().activeEditor;
                        if (ed) ed.commands.blur();
                      }
                    }}
                  >
                    <SegmentedDocEditor />
                  </div>
                  <PromptPanel isCollapsed={isRightCollapsed} onToggleCollapse={() => setIsRightCollapsed(!isRightCollapsed)} />
                </div>
              </main>
              <EditorStatusBar />
            </div>
          }
        />
      </Routes>

      <SavedSessionsModal isOpen={isSavedSessionsOpen} onClose={() => setIsSavedSessionsOpen(false)} />
      <AiConfigModal isOpen={isAiConfigOpen} onClose={() => setIsAiConfigOpen(false)} />
    </div>
  );
}
