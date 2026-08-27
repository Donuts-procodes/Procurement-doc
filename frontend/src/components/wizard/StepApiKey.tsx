import { useEffect, useState } from "react";
import { createSession, fetchProviderModels } from "../../api/client";
import { useWizardStore } from "../../state/wizardStore";
import { PROVIDER_LABELS, type LLMProvider } from "../../types";

const FALLBACK_MODELS: Record<LLMProvider, string[]> = {
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
  gemini: ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"],
  anthropic: ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
};

export function StepApiKey() {
  const setSession = useWizardStore((s) => s.setSession);
  const setError = useWizardStore((s) => s.setError);
  const error = useWizardStore((s) => s.error);

  const [providerModels, setProviderModels] = useState<Record<LLMProvider, string[]>>(FALLBACK_MODELS);
  
  // Restore saved API key and provider/model from localStorage if available
  const [provider, setProvider] = useState<LLMProvider>(
    () => (localStorage.getItem("gdocs_rag_provider") as LLMProvider) || "openai"
  );
  const [model, setModel] = useState<string>(
    () => localStorage.getItem("gdocs_rag_model") || "gpt-4o"
  );
  const [apiKey, setApiKey] = useState<string>(
    () => localStorage.getItem("gdocs_rag_api_key") || ""
  );
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchProviderModels()
      .then((data) => {
        if (data && Object.keys(data).length > 0) {
          setProviderModels(data);
        }
      })
      .catch((err) => {
        console.warn("Failed to fetch provider models from backend, using fallback list:", err);
      });
  }, []);

  useEffect(() => {
    const list = providerModels[provider] ?? FALLBACK_MODELS[provider] ?? [];
    if (list.length > 0 && !list.includes(model)) {
      setModel(list[0]);
    }
  }, [provider, providerModels, model]);

  async function handleSubmit() {
    if (!model || apiKey.trim().length < 8) {
      setError("Enter a valid API key (min 8 characters) and select a model.");
      return;
    }
    setSubmitting(true);
    try {
      const trimmedKey = apiKey.trim();
      // Persist in localStorage so user never has to re-enter
      localStorage.setItem("gdocs_rag_provider", provider);
      localStorage.setItem("gdocs_rag_model", model);
      localStorage.setItem("gdocs_rag_api_key", trimmedKey);

      const session = await createSession(provider, model, trimmedKey);
      setSession(session.provider, session.model, session.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create session");
    } finally {
      setSubmitting(false);
    }
  }

  const availableModels = providerModels[provider] ?? FALLBACK_MODELS[provider] ?? [];

  return (
    <div className="wizard-step">
      <h2>Connect your AI provider</h2>
      <p className="wizard-step__subtitle">
        Select your provider and API key. Your key is saved locally in your browser so you don't have to re-enter it.
      </p>

      <label className="field">
        <span>Provider</span>
        <select value={provider} onChange={(e) => setProvider(e.target.value as LLMProvider)}>
          {(Object.keys(PROVIDER_LABELS) as LLMProvider[]).map((key) => (
            <option key={key} value={key}>
              {PROVIDER_LABELS[key]}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>Model</span>
        <select value={model} onChange={(e) => setModel(e.target.value)}>
          {availableModels.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>API key</span>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="sk-..."
        />
      </label>

      {error && <p className="error-text">{error}</p>}

      <button className="primary-button" onClick={handleSubmit} disabled={submitting}>
        {submitting ? (
          <span style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
            <span className="spinner-small" /> Connecting to {PROVIDER_LABELS[provider]}...
          </span>
        ) : (
          "Continue"
        )}
      </button>
    </div>
  );
}
