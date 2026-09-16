import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { generateDocument, streamDocumentGeneration } from "../../api/client";
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
  const [clarifyingQuestion, setClarifyingQuestion] = useState<string | null>(null);
  const [answerInput, setAnswerInput] = useState("");
  const [answering, setAnswering] = useState(false);
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

    triggerInitialGeneration();
  }, []);

  function triggerInitialGeneration() {
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
    const guidedParams = useWizardStore.getState().guidedParams || {};

    let receivedDocument = false;
    let accumulatedSegments: any[] = [];

    streamDocumentGeneration(
      {
        session_id: effSessionId,
        kb_id: kbId || undefined,
        procurement_doc_type: procurementDocType,
        template_id: templateId,
        num_pages: numPages,
        prompt: prompt || "Generate procurement document according to enterprise standard specifications.",
        buyer_name: guidedParams.buyer_name,
        vendor_name: guidedParams.vendor_name,
        budget_estimate: guidedParams.budget_estimate,
        delivery_timeline: guidedParams.delivery_timeline,
        compliance_frameworks: guidedParams.compliance_frameworks,
        primary_tech: guidedParams.primary_tech,
        sla_target: guidedParams.sla_target,
      },
      (event) => {
        if (event.type === "agent_thought") {
          const stepMsg = event.step;
          if (stepMsg.includes("Super Agent")) setCurrentStageIdx(0);
          else if (stepMsg.includes("Launching parallel") || stepMsg.includes("evidence")) setCurrentStageIdx(1);
          else if (stepMsg.includes("Fact-Checking") || stepMsg.includes("audit")) setCurrentStageIdx(2);
          else if (stepMsg.includes("Drafting") || stepMsg.includes("Canvas")) setCurrentStageIdx(3);
        } else if (event.type === "canvas_patch" && event.content) {
          accumulatedSegments.push({
            segment_id: event.target_id || `seg_${accumulatedSegments.length + 1}`,
            name: `Section ${accumulatedSegments.length + 1}`,
            segment_type: "text",
            content: event.content,
          });
        } else if (event.type === "checkpoint" && event.segments && event.segments.length > 0) {
          receivedDocument = true;
          setGeneratedDocument(
            event.document_id || `doc_${effSessionId.slice(0, 8)}`,
            {},
            event.page_titles || [],
            event.segments,
            event.style_config,
            event.page_layout_size || "A4",
            event.missing_fields || []
          );

          addChatMessage({
            id: "initial_generation_success",
            sender: "assistant",
            text: `Generated ${event.segments.length} document segments grounded in Knowledge Base context!`,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          });
          navigate("/document");
        }
      },
      (err) => {
        console.warn("SSE stream failed, falling back to standard REST generate endpoint:", err);
        // Fallback to standard generate
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
          buyer_name: guidedParams.buyer_name,
          vendor_name: guidedParams.vendor_name,
          budget_estimate: guidedParams.budget_estimate,
          delivery_timeline: guidedParams.delivery_timeline,
          compliance_frameworks: guidedParams.compliance_frameworks,
          primary_tech: guidedParams.primary_tech,
          sla_target: guidedParams.sla_target,
        })
          .then((result) => {
            if (result.status === "collecting" && result.pending_question) {
              setClarifyingQuestion(result.pending_question);
              setPendingQuestion(result.document_id, result.pending_question);
              return;
            }

            setGeneratedDocument(
              result.document_id,
              result.lexical_state || {},
              result.page_titles || [],
              result.segments || [],
              result.style_config,
              result.page_layout_size,
              result.missing_fields || []
            );

            addChatMessage({
              id: "initial_generation_success",
              sender: "assistant",
              text: `Generated ${result.segments?.length || 0} document segments grounded in Knowledge Base context!`,
              timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            });
            navigate("/document");
          })
          .catch((fallbackErr) => {
            setError(fallbackErr instanceof Error ? fallbackErr.message : "Generation failed");
            setStep("prompt-intake");
          });
      },
      () => {
        if (!receivedDocument && accumulatedSegments.length > 0) {
          setGeneratedDocument(
            `doc_${effSessionId.slice(0, 8)}`,
            {},
            accumulatedSegments.map((s) => s.name),
            accumulatedSegments
          );
          navigate("/document");
        }
      }
    );
  }

  async function handleAnswerSubmit() {
    if (!answerInput.trim()) return;
    setAnswering(true);
    try {
      const userAns = answerInput.trim();
      addChatMessage({
        id: `answer_${Date.now()}`,
        sender: "user",
        text: userAns,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      });

      const effSessionId = sessionId || `session_${Date.now()}`;
      const apiConfig = useWizardStore.getState().savedApiKeyConfig;

      // Re-trigger generation with updated collected fields in session
      const result = await generateDocument({
        session_id: effSessionId,
        kb_id: kbId,
        procurement_doc_type: procurementDocType,
        template_id: templateId,
        num_pages: numPages,
        prompt: `${prompt}\n\nAdditional Clarifications & Specifics:\n${userAns}`,
        content_density: contentDensity,
        provider: apiConfig?.provider,
        model: apiConfig?.model,
        api_key: apiConfig?.key,
      });

      setGeneratedDocument(
        result.document_id,
        result.lexical_state || {},
        result.page_titles || [],
        result.segments || [],
        result.style_config,
        result.page_layout_size
      );

      navigate("/document");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resume generation");
    } finally {
      setAnswering(false);
    }
  }

  if (clarifyingQuestion) {
    return (
      <div className="wizard-step" style={{ maxWidth: "560px", margin: "0 auto" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
          <span style={{ fontSize: "28px" }}>🤖</span>
          <h2 style={{ margin: 0 }}>A quick clarification before we generate</h2>
        </div>
        <p style={{ fontSize: "14px", lineHeight: "1.6", color: "#374151", background: "#eff6ff", borderLeft: "4px solid #1a73e8", padding: "14px", borderRadius: "6px" }}>
          {clarifyingQuestion}
        </p>
        <div style={{ marginTop: "20px" }}>
          <label style={{ display: "block", fontSize: "13px", fontWeight: 600, marginBottom: "8px" }}>
            Your Answer / Specifics:
          </label>
          <textarea
            rows={3}
            value={answerInput}
            onChange={(e) => setAnswerInput(e.target.value)}
            placeholder="e.g. Budget cap is $750k, deadline is Nov 15th, or type 'proceed with defaults'..."
            style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid #cbd5e1", fontSize: "14px", boxSizing: "border-box" }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                handleAnswerSubmit();
              }
            }}
          />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "16px" }}>
          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              setAnswerInput("proceed with defaults");
              setTimeout(() => handleAnswerSubmit(), 50);
            }}
            style={{ fontSize: "13px", padding: "8px 14px", background: "none", border: "1px solid #cbd5e1", borderRadius: "6px", cursor: "pointer" }}
          >
            Use Enterprise Defaults
          </button>
          <button
            type="button"
            className="primary-button"
            disabled={answering || !answerInput.trim()}
            onClick={handleAnswerSubmit}
            style={{ padding: "10px 24px" }}
          >
            {answering ? "Generating Document..." : "Continue Generation →"}
          </button>
        </div>
      </div>
    );
  }

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
