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
    <div className="wizard" style={{ display: "flex", maxWidth: "1080px", margin: "40px auto 0", alignItems: "stretch", gap: "16px" }}>
      <IconDock />
      
      <div className="wizard__card" style={{ flex: 1, background: isDarkMode ? "rgba(30, 41, 59, 0.5)" : "rgba(255, 255, 255, 0.7)", backdropFilter: "blur(12px)", border: isDarkMode ? "1px solid rgba(255,255,255,0.05)" : "1px solid rgba(255, 255, 255, 0.5)", borderRadius: "24px", boxShadow: isDarkMode ? "0 8px 32px rgba(0,0,0,0.2)" : "0 8px 32px rgba(0, 0, 0, 0.05)", padding: "40px" }}>
        {step === "api-key" && <StepApiKey />}
        {step === "knowledge-base" && <StepKnowledgeBase />}
        {step === "template-config" && <StepTemplateConfig />}
        {step === "generating" && <StepGenerating />}
      </div>
    </div>
  );
}
