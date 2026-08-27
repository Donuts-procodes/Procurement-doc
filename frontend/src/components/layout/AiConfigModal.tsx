import { useState } from "react";
import { createPortal } from "react-dom";
import { useWizardStore } from "../../state/wizardStore";
import type { LLMProvider } from "../../types";

interface AiConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AiConfigModal({ isOpen, onClose }: AiConfigModalProps) {
  const { savedApiKeyConfig, setApiKeyConfig, isDarkMode } = useWizardStore((s) => ({
    savedApiKeyConfig: s.savedApiKeyConfig,
    setApiKeyConfig: s.setApiKeyConfig,
    isDarkMode: s.isDarkMode,
  }));

  const [provider, setProvider] = useState<LLMProvider>(savedApiKeyConfig?.provider || "openai");
  const [model, setModel] = useState<string>(savedApiKeyConfig?.model || "gpt-4o");
  const [apiKey, setApiKey] = useState<string>(savedApiKeyConfig?.key || "");

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
          maxWidth: "480px",
          padding: "24px",
          boxShadow: "0 10px 30px rgba(0, 0, 0, 0.2)",
          border: isDarkMode ? "1px solid rgba(255, 255, 255, 0.1)" : "none",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 700, color: isDarkMode ? "#f8fafc" : "#1f2937" }}>
            ⚙️ AI Provider & API Settings
          </h3>
          <button style={{ background: "none", border: "none", fontSize: "18px", cursor: "pointer", color: isDarkMode ? "#94a3b8" : "#6b7280" }} onClick={onClose}>
            ✕
          </button>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: isDarkMode ? "#cbd5e1" : "#374151", marginBottom: "6px" }}>
              AI Provider
            </label>
            <select
              style={{ width: "100%", padding: "10px", borderRadius: "6px", border: isDarkMode ? "1px solid rgba(255, 255, 255, 0.2)" : "1px solid #d1d5db", background: isDarkMode ? "transparent" : "#fff", color: isDarkMode ? "#f8fafc" : "inherit", fontSize: "14px" }}
              value={provider}
              onChange={(e) => {
                const p = e.target.value as LLMProvider;
                setProvider(p);
                if (p === "openai") setModel("gpt-4o");
                if (p === "gemini") setModel("gemini-1.5-pro");
                if (p === "anthropic") setModel("claude-3-5-sonnet");
              }}
            >
              <option value="openai">OpenAI</option>
              <option value="gemini">Google Gemini</option>
              <option value="anthropic">Anthropic</option>
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: isDarkMode ? "#cbd5e1" : "#374151", marginBottom: "6px" }}>
              LLM Model
            </label>
            <select
              style={{ width: "100%", padding: "10px", borderRadius: "6px", border: isDarkMode ? "1px solid rgba(255, 255, 255, 0.2)" : "1px solid #d1d5db", background: isDarkMode ? "transparent" : "#fff", color: isDarkMode ? "#f8fafc" : "inherit", fontSize: "14px" }}
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              {provider === "openai" && (
                <>
                  <option value="gpt-4o">gpt-4o (Recommended)</option>
                  <option value="gpt-4-turbo">gpt-4-turbo</option>
                  <option value="gpt-4o-mini">gpt-4o-mini</option>
                </>
              )}
              {provider === "gemini" && (
                <>
                  <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                  <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                </>
              )}
              {provider === "anthropic" && (
                <>
                  <option value="claude-3-5-sonnet">claude-3-5-sonnet</option>
                  <option value="claude-3-haiku">claude-3-haiku</option>
                </>
              )}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: isDarkMode ? "#cbd5e1" : "#374151", marginBottom: "6px" }}>
              API Key
            </label>
            <input
              type="password"
              style={{ width: "100%", padding: "10px", borderRadius: "6px", border: isDarkMode ? "1px solid rgba(255, 255, 255, 0.2)" : "1px solid #d1d5db", background: isDarkMode ? "rgba(0,0,0,0.2)" : "#fff", color: isDarkMode ? "#f8fafc" : "inherit", fontSize: "14px", boxSizing: "border-box" }}
              placeholder="sk-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
            <button
              style={{ padding: "8px 16px", backgroundColor: isDarkMode ? "rgba(255, 255, 255, 0.1)" : "#f3f4f6", color: isDarkMode ? "#e2e8f0" : "#374151", border: "none", borderRadius: "6px", cursor: "pointer", fontSize: "14px" }}
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              style={{ padding: "8px 20px", backgroundColor: "#1a73e8", color: "#ffffff", border: "none", borderRadius: "6px", fontWeight: 600, cursor: "pointer", fontSize: "14px" }}
              onClick={() => {
                if (!apiKey) {
                  alert("Please enter a valid API key.");
                  return;
                }
                setApiKeyConfig(provider, model, apiKey);
                onClose();
              }}
            >
              Save Configuration
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
