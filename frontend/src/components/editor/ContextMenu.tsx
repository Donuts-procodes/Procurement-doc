import { useState, useEffect } from "react";
import { useWizardStore } from "../../state/wizardStore";

interface ContextMenuState {
  x: number;
  y: number;
  selectedText: string;
}

interface ContextMenuProps {
  onClose: () => void;
}

export function ContextMenu({ onClose }: ContextMenuProps) {
  const activeEditor = useWizardStore((s) => s.activeEditor);
  const [menuPos, setMenuPos] = useState<ContextMenuState | null>(null);

  useEffect(() => {
    function handleContextMenu(e: MouseEvent) {
      // Check if context menu triggered inside editor canvas
      const target = e.target as HTMLElement;
      if (target.closest(".segmented-doc-editor")) {
        e.preventDefault();
        const selectedText = window.getSelection()?.toString() || "";
        setMenuPos({ x: e.clientX, y: e.clientY, selectedText });
      } else {
        setMenuPos(null);
      }
    }

    function handleClickOutside() {
      setMenuPos(null);
      onClose();
    }

    window.addEventListener("contextmenu", handleContextMenu);
    window.addEventListener("click", handleClickOutside);
    return () => {
      window.removeEventListener("contextmenu", handleContextMenu);
      window.removeEventListener("click", handleClickOutside);
    };
  }, [onClose]);

  if (!menuPos) return null;

  const wordQuery = menuPos.selectedText.trim() ? menuPos.selectedText.trim().slice(0, 15) : "Selection";

  async function handleCut() {
    try {
      const selected = window.getSelection()?.toString() || "";
      if (selected) {
        await navigator.clipboard.writeText(selected);
        document.execCommand("delete");
      }
    } catch {
      document.execCommand("cut");
    }
    setMenuPos(null);
  }

  async function handleCopy() {
    try {
      const selected = window.getSelection()?.toString() || "";
      if (selected) {
        await navigator.clipboard.writeText(selected);
      }
    } catch {
      document.execCommand("copy");
    }
    setMenuPos(null);
  }

  async function handlePaste() {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        document.execCommand("insertText", false, text);
      }
    } catch {
      alert("Press Ctrl + V to paste clipboard content.");
    }
    setMenuPos(null);
  }

  async function handlePasteWithoutFormatting() {
    try {
      const text = await navigator.clipboard.readText();
      const plainText = text.replace(/<[^>]*>?/gm, "");
      document.execCommand("insertText", false, plainText);
    } catch {
      alert("Press Ctrl + Shift + V to paste plain text.");
    }
    setMenuPos(null);
  }

  function handleDelete() {
    document.execCommand("delete");
    setMenuPos(null);
  }

  return (
    <div
      className="gdocs-context-menu"
      style={{ top: `${menuPos.y}px`, left: `${menuPos.x}px` }}
      onClick={(e) => e.stopPropagation()}
    >
      <button className="context-menu-item" onClick={handleCut}>
        <span>✂️ Cut</span>
        <span className="shortcut-key">Ctrl+X</span>
      </button>

      <button className="context-menu-item" onClick={handleCopy}>
        <span>📋 Copy</span>
        <span className="shortcut-key">Ctrl+C</span>
      </button>

      <button className="context-menu-item" onClick={handlePaste}>
        <span>📥 Paste</span>
        <span className="shortcut-key">Ctrl+V</span>
      </button>

      <button className="context-menu-item" onClick={handlePasteWithoutFormatting}>
        <span>Paste without formatting</span>
        <span className="shortcut-key">Ctrl+Shift+V</span>
      </button>

      <button className="context-menu-item" onClick={handleDelete}>
        <span>Delete selection</span>
        <span className="shortcut-key">Delete</span>
      </button>

      <div className="menu-divider" />

      <button
        className="context-menu-item"
        onClick={() => {
          if (activeEditor) {
            activeEditor.chain?.()?.focus()?.toggleHighlight({ color: "#fef08a" })?.run();
          }
          onClose();
        }}
      >
        <span>Add Comment / Highlight</span>
        <span className="shortcut-key">Ctrl+Alt+M</span>
      </button>

      <button
        className="context-menu-item"
        onClick={() => {
          if (activeEditor) {
            activeEditor.chain?.()?.focus()?.toggleItalic()?.run();
          }
          onClose();
        }}
      >
        <span>Suggest Edits</span>
      </button>

      <div className="menu-divider" />

      <button
        className="context-menu-item"
        onClick={() => {
          if (wordQuery) {
            window.open(`https://en.wiktionary.org/wiki/${encodeURIComponent(wordQuery)}`, "_blank");
          }
          onClose();
        }}
      >
        <span>Define '{wordQuery}'</span>
        <span className="shortcut-key">Ctrl+Shift+Y</span>
      </button>

      <button
        className="context-menu-item"
        onClick={() => {
          navigator.clipboard.writeText(window.location.href);
          onClose();
        }}
      >
        <span>Copy Section Link</span>
      </button>

      <div className="menu-divider" />

      <button
        className="context-menu-item"
        onClick={() => {
          if (activeEditor) {
            activeEditor.chain?.()?.focus()?.unsetAllMarks()?.clearNodes()?.run();
          }
          onClose();
        }}
      >
        <span>Clear Formatting</span>
        <span className="shortcut-key">Ctrl+\</span>
      </button>
    </div>
  );
}
