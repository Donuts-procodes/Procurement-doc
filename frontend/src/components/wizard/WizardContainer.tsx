import { useWizardStore } from "../../state/wizardStore";
import { StepApiKey } from "./StepApiKey";
import { StepGenerating } from "./StepGenerating";
import { StepKnowledgeBase } from "./StepKnowledgeBase";
import { StepTemplateConfig } from "./StepTemplateConfig";
import { IconDock } from "../layout/IconDock";
export function WizardContainer() {
  const step = useWizardStore((s) => s.step);
  const isDarkMode = useWizardStore((s) => s.isDarkMode);

  return (
    <div
      className="wizard"
      style={{
        display: "flex",
        width: "100%",
        maxWidth: "1380px",
        margin: "0 auto",
        alignItems: "flex-start",
        gap: "20px",
        boxSizing: "border-box",
      }}
    >
      <IconDock />

      <div
        className="wizard__card"
        style={{
          flex: 1,
          minWidth: 0,
          background: isDarkMode ? "rgba(30, 41, 59, 0.5)" : "rgba(255, 255, 255, 0.9)",
          backdropFilter: "blur(12px)",
          border: isDarkMode ? "1px solid rgba(255,255,255,0.06)" : "1px solid rgba(226, 232, 240, 0.8)",
          borderRadius: "20px",
          boxShadow: isDarkMode ? "0 8px 32px rgba(0,0,0,0.2)" : "0 8px 32px rgba(0, 0, 0, 0.05)",
          padding: "clamp(20px, 2.5vw, 36px)",
          boxSizing: "border-box",
        }}
      >
        {step === "api-key" && <StepApiKey />}
        {step === "knowledge-base" && <StepKnowledgeBase />}
        {step === "template-config" && <StepTemplateConfig />}
        {step === "generating" && <StepGenerating />}
      </div>
    </div>
  );
}
