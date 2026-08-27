import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { generateDocument } from "../../api/client";
import { useWizardStore } from "../../state/wizardStore";

const GENERATION_STAGES = [
  "🔍 Step 1/4: Parsing uploaded Knowledge Base PDFs & visual assets...",
  "🤖 Step 2/4: Running Fillup Agent & extracting mandatory fields...",
  "🖼️ Step 3/4: Executing Image Extractor Agent node...",
  "📄 Step 4/4: Building TipTap ProseMirror document segments & rendering canvas...",
];

export function StepGenerating() {
  const { sessionId, kbId, procurementDocType, templateId, numPages, prompt, contentDensity } = useWizardStore((s) => ({
    sessionId: s.sessionId,
    kbId: s.kbId,
    procurementDocType: s.procurementDocType,
    templateId: s.templateId,
    numPages: s.numPages,
    prompt: s.prompt,
    contentDensity: s.contentDensity,
  }));
  const setGeneratedDocument = useWizardStore((s) => s.setGeneratedDocument);
  const setPendingQuestion = useWizardStore((s) => s.setPendingQuestion);
  const addChatMessage = useWizardStore((s) => s.addChatMessage);
  const setError = useWizardStore((s) => s.setError);
  const setStep = useWizardStore((s) => s.setStep);
  const hasStarted = useRef(false);

  const [currentStageIdx, setCurrentStageIdx] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStageIdx((prev) => (prev < GENERATION_STAGES.length - 1 ? prev + 1 : prev));
    }, 2500);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;

    const effSessionId = sessionId || `session_${Date.now()}`;

    if (prompt) {
      addChatMessage({
        id: "initial_user_prompt",
        sender: "user",
        text: `Document Request (${procurementDocType}): ${prompt}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      });
    }

    const apiConfig = useWizardStore.getState().savedApiKeyConfig;

    generateDocument({
      session_id: effSessionId,
      kb_id: kbId,
      procurement_doc_type: procurementDocType,
      template_id: templateId,
      num_pages: numPages,
      prompt,
      content_density: contentDensity,
      provider: apiConfig?.provider,
      model: apiConfig?.model,
      api_key: apiConfig?.key,
    })
      .then((result) => {
        setGeneratedDocument(
          result.document_id,
          result.lexical_state || {},
          result.page_titles || [],
          result.segments || [],
          result.style_config,
          result.page_layout_size
        );

        if (result.pending_question) {
          addChatMessage({
            id: "missing_placeholders_notice",
            sender: "assistant",
            text: result.pending_question,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          });
        } else {
          addChatMessage({
            id: "initial_generation_success",
            sender: "assistant",
            text: `Generated ${result.segments?.length || 0} document segments grounded in Knowledge Base context!`,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          });
        }
        navigate("/document");
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Generation failed");
        setStep("template-config");
      });
  }, [sessionId, kbId, procurementDocType, numPages, prompt, setGeneratedDocument, setPendingQuestion, addChatMessage, setError, setStep, navigate]);

  return (
    <div className="wizard-step wizard-step--centered">
      <div className="spinner-large" />
      <h2>Generating {procurementDocType} Document</h2>
      <p className="wizard-step__subtitle" style={{ fontSize: "14px", color: "#1a73e8", fontWeight: 600 }}>
        {GENERATION_STAGES[currentStageIdx]}
      </p>
      <div className="loading-progress-bar">
        <div
          className="loading-progress-fill"
          style={{ width: `${((currentStageIdx + 1) / GENERATION_STAGES.length) * 100}%` }}
        />
      </div>
    </div>
  );
}
