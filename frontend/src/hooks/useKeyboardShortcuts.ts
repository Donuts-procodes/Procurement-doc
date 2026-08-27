import { useEffect } from "react";
import { useWizardStore } from "../state/wizardStore";

export function useKeyboardShortcuts(setToastMessage: (msg: string | null) => void) {
  const saveCurrentSession = useWizardStore((s) => s.saveCurrentSession);
  const undo = useWizardStore((s) => s.undo);
  const redo = useWizardStore((s) => s.redo);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        saveCurrentSession();
        setToastMessage("💾 Workspace Session Saved Successfully!");
        setTimeout(() => setToastMessage(null), 2500);
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z" && !e.shiftKey) {
        undo();
      } else if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === "y" || (e.shiftKey && e.key.toLowerCase() === "z"))) {
        redo();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [saveCurrentSession, undo, redo, setToastMessage]);
}
