import { useWizardStore } from "../../state/wizardStore";

export function IconDock() {
  const step = useWizardStore((s) => s.step);
  const setStep = useWizardStore((s) => s.setStep);
  const isDarkMode = useWizardStore((s) => s.isDarkMode);

  const navItems = [
    {
      id: "api-key",
      label: "API Key",
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
        </svg>
      )
    },
    {
      id: "templates",
      label: "Templates",
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="3" width="7" height="7"></rect>
          <rect x="14" y="3" width="7" height="7"></rect>
          <rect x="3" y="14" width="7" height="7"></rect>
          <rect x="14" y="14" width="7" height="7"></rect>
        </svg>
      )
    },
    {
      id: "prompt-intake",
      label: "Prompt & Files",
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      )
    },
    {
      id: "generating",
      label: "Generate",
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
        </svg>
      )
    }
  ];

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        width: "190px",
        flexShrink: 0,
        padding: "16px 10px",
        background: isDarkMode ? "rgba(30, 41, 59, 0.6)" : "#ffffff",
        backdropFilter: "blur(12px)",
        border: isDarkMode ? "1px solid rgba(255,255,255,0.08)" : "1px solid #e2e8f0",
        borderRadius: "16px",
        boxShadow: isDarkMode ? "0 8px 24px rgba(0,0,0,0.25)" : "0 4px 16px rgba(0,0,0,0.04)",
        position: "sticky",
        top: "24px",
        alignSelf: "flex-start",
        boxSizing: "border-box",
      }}
    >
      <div style={{ padding: "0 10px", marginBottom: "14px", fontSize: "11px", fontWeight: 700, color: isDarkMode ? "#94a3b8" : "#64748b", textTransform: "uppercase", letterSpacing: "1px" }}>
        Steps
      </div>
      
      {navItems.map((item) => {
        const isActive = step === item.id;
        const provider = useWizardStore.getState().provider;
        
        // Logic to restrict clicking future steps
        let isDisabled = false;
        if (item.id === "templates" && !provider) isDisabled = true;
        if (item.id === "prompt-intake" && !provider) isDisabled = true;
        // Never allow clicking directly to 'generating' from the sidebar unless we are already there, 
        // as it needs to be triggered by the form submission to start the API call.
        if (item.id === "generating" && step !== "generating") isDisabled = true;

        return (
          <button
            key={item.id}
            onClick={() => !isDisabled && setStep(item.id as any)}
            disabled={isDisabled}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
              padding: "12px 14px",
              background: isActive ? (isDarkMode ? "#1e293b" : "#ffffff") : "transparent",
              border: "1px solid",
              borderColor: isActive ? (isDarkMode ? "#334155" : "rgba(0,0,0,0.06)") : "transparent",
              borderRadius: "10px",
              width: "100%",
              textAlign: "left",
              fontSize: "14px",
              fontWeight: isActive ? 600 : 500,
              color: isDisabled ? (isDarkMode ? "#475569" : "#cbd5e1") : (isActive ? (isDarkMode ? "#fff" : "#0f172a") : (isDarkMode ? "#94a3b8" : "#475569")),
              cursor: isDisabled ? "not-allowed" : "pointer",
              transition: "all 0.2s ease",
              boxShadow: isActive ? "0 2px 8px rgba(0,0,0,0.04)" : "none",
              marginBottom: "4px",
              opacity: isDisabled ? 0.6 : 1,
            }}
          >
            <span style={{ color: isDisabled ? "inherit" : (isActive ? "#2563eb" : "inherit") }}>
              {item.icon}
            </span>
            {item.label}
          </button>
        );
      })}
    </div>
  );
}
