import { useState } from "react";
import { useWizardStore } from "../../state/wizardStore";
import { exportToPdf, exportToWord, exportToTxt } from "../../utils/exportUtils";
import { PrintPreviewModal } from "./PrintPreviewModal";
import { InsertItemModal, ModalType } from "./InsertItemModal";
import { FindReplaceModal } from "./FindReplaceModal";
import { WordCountModal } from "./WordCountModal";

interface EditorRibbonProps {
  onOpenSavedSessions?: () => void;
}

export function EditorRibbon({ onOpenSavedSessions }: EditorRibbonProps) {
  const [activeTab, setActiveTab] = useState<"File" | "Home" | "Insert" | "Design" | "Layout">("Home");
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isFindReplaceOpen, setIsFindReplaceOpen] = useState(false);
  const [isWordCountOpen, setIsWordCountOpen] = useState(false);
  const [modalType, setModalType] = useState<ModalType>(null);

  const segments = useWizardStore((s) => s.segments);
  const styleConfig = useWizardStore((s) => s.styleConfig);
  const setStyleConfig = useWizardStore((s) => s.setStyleConfig);
  const isDarkMode = useWizardStore((s) => s.isDarkMode);
  const pageLayoutSize = useWizardStore((s) => s.pageLayoutSize);
  const setPageLayoutSize = useWizardStore((s) => s.setPageLayoutSize);
  const activeEditor = useWizardStore((s) => s.activeEditor);
  const addPage = useWizardStore((s) => s.addPage);
  const startNewSession = useWizardStore((s) => s.startNewSession);

  function handleModalConfirm(data: any) {
    if (!activeEditor && modalType !== "header") return;

    if (modalType === "picture" && data.url) {
      execCmd("insertImage", data.url);
    } else if (modalType === "custom-table" && data.rows && data.cols) {
      activeEditor.chain().focus().insertTable({ rows: data.rows, cols: data.cols, withHeaderRow: true }).run();
    } else if (modalType === "cover-page") {
      if (data.style === "corporate") {
        activeEditor.chain().focus().insertContent(`<div style="background: linear-gradient(135deg, #0f4c81, #1a73e8); color: white; padding: 40px; border-radius: 8px; text-align: center; margin-bottom: 24px;"><h1 style="color: white; font-size: 28px; margin-bottom: 8px;">EXECUTIVE PROCUREMENT PROPOSAL</h1><p style="font-size: 16px; opacity: 0.9;">ENTERPRISE SPECIFICATION & TECHNICAL BLUEPRINT</p><div style="margin-top: 20px; font-size: 13px; opacity: 0.8;">Date: ${new Date().toLocaleDateString()} • Status: Confidential</div></div>`).run();
      } else if (data.style === "minimal") {
        activeEditor.chain().focus().insertContent(`<div style="text-align: center; padding: 40px 0; border-bottom: 2px solid #333;"><h1 style="letter-spacing: 2px;">PROCUREMENT PROPOSAL SPECIFICATION</h1><p>Confidential Tender Document</p></div>`).run();
      } else {
        activeEditor.chain().focus().insertContent(`<div style="border-left: 8px solid #2563eb; padding: 24px; background: #eff6ff; margin-bottom: 24px;"><h1 style="color: #1e40af; margin: 0;">TECHNICAL PROPOSAL BLUEPRINT</h1><p style="margin-top: 6px; color: #1e3a8a;">RFP Technical Submission</p></div>`).run();
      }
    } else if (modalType === "icons" && data.icon) {
      activeEditor.chain().focus().insertContent(` ${data.icon} `).run();
    } else if (modalType === "symbols" && data.symbol) {
      activeEditor.chain().focus().insertContent(` ${data.symbol} `).run();
    } else if (modalType === "video" && data.url) {
      activeEditor.chain().focus().insertContent(`<div style="margin: 16px 0; text-align: center; background: #f8fafc; padding: 16px; border-radius: 8px;"><p style="margin:0;">🎥 <strong>Embedded Video Stream:</strong> <a href="${data.url}" target="_blank">${data.url}</a></p></div>`).run();
    } else if (modalType === "link" && data.url) {
      activeEditor.chain().focus().insertContent(`<a href="${data.url}" target="_blank">${data.text || data.url}</a>`).run();
    } else if (modalType === "bookmark" && data.name) {
      activeEditor.chain().focus().insertContent(`<span id="${data.name}" style="color: #2563eb; font-weight: 600;">🚩 [${data.name}]</span>`).run();
    } else if (modalType === "comment" && data.text) {
      activeEditor.chain().focus().insertContent(`<div style="background: #fff8e1; border-left: 4px solid #ffb300; padding: 10px; margin: 12px 0; font-size: 13px; color: #78350f;">💬 <strong>Reviewer Note:</strong> ${data.text}</div>`).run();
    } else if (modalType === "header" && data.title) {
      setStyleConfig({ headerText: data.title, showHeaderFooter: true });
    } else if (modalType === "wordart" && data.text) {
      activeEditor.chain().focus().insertContent(`<h1 style="background: linear-gradient(45deg, #1a73e8, #9c27b0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 32px; font-weight: 800; text-align: center; margin: 20px 0;">${data.text}</h1>`).run();
    }
  }

  function execCmd(command: string, value: string | undefined = undefined) {
    if (!activeEditor) return;

    const chain = activeEditor.chain().focus();

    switch (command) {
      case "bold":
        chain.toggleBold().run();
        break;
      case "italic":
        chain.toggleItalic().run();
        break;
      case "underline":
        chain.toggleUnderline().run();
        break;
      case "strikeThrough":
        chain.toggleStrike().run();
        break;
      case "subscript":
        chain.toggleSubscript().run();
        break;
      case "superscript":
        chain.toggleSuperscript().run();
        break;
      case "insertUnorderedList":
        chain.toggleBulletList().run();
        break;
      case "insertOrderedList":
        chain.toggleOrderedList().run();
        break;
      case "justifyLeft":
        chain.setTextAlign("left").run();
        break;
      case "justifyCenter":
        chain.setTextAlign("center").run();
        break;
      case "justifyRight":
        chain.setTextAlign("right").run();
        break;
      case "foreColor":
        if (value) chain.setColor(value).run();
        break;
      case "formatBlock":
        if (value === "p") chain.setParagraph().run();
        else if (value === "h1") chain.toggleHeading({ level: 1 }).run();
        else if (value === "h2") chain.toggleHeading({ level: 2 }).run();
        break;
      case "insertImage":
        if (value) chain.setImage({ src: value }).run();
        break;
      case "insertTable":
        chain.insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run();
        break;
      case "insertHorizontalRule":
        chain.setHorizontalRule().run();
        break;
      case "insertHTML":
        chain.insertContent(value).run();
        break;
      default:
        console.warn("Unsupported command:", command);
    }
  }

  function handleConfirmDownload(format: string) {
    if (format === "pdf") {
      exportToPdf(segments, "Procurement Proposal Document", pageLayoutSize, styleConfig);
    } else if (format === "doc") {
      exportToWord(segments, "Procurement Proposal Document", styleConfig);
    } else if (format === "txt") {
      exportToTxt(segments, "Procurement Proposal Document");
    }
  }

  return (
    <div className={`editor-ribbon-wrapper ${isCollapsed ? "ribbon-collapsed" : ""}`}>
      {/* Top Ribbon Tabs Header */}
      <div className="ribbon-tabs-bar">
        <div className="ribbon-tabs">
          <button className={`ribbon-tab-btn ${activeTab === "File" ? "active" : ""}`} onClick={() => setActiveTab("File")}>
            File
          </button>
          <button className={`ribbon-tab-btn ${activeTab === "Home" ? "active" : ""}`} onClick={() => setActiveTab("Home")}>
            Home
          </button>
          <button className={`ribbon-tab-btn ${activeTab === "Insert" ? "active" : ""}`} onClick={() => setActiveTab("Insert")}>
            Insert
          </button>
          <button className={`ribbon-tab-btn ${activeTab === "Design" ? "active" : ""}`} onClick={() => setActiveTab("Design")}>
            Design
          </button>
          <button className={`ribbon-tab-btn ${activeTab === "Layout" ? "active" : ""}`} onClick={() => setActiveTab("Layout")}>
            Layout
          </button>
        </div>

        <div className="ribbon-right-controls">
          <button
            className="ribbon-collapse-toggle"
            onClick={() => setIsCollapsed(!isCollapsed)}
            title={isCollapsed ? "Expand Ribbon (Ctrl+F1)" : "Collapse Ribbon (Ctrl+F1)"}
          >
            {isCollapsed ? "▼" : "▲"}
          </button>
        </div>
      </div>

      {/* Tab Panels */}
      {!isCollapsed && (
        <div className="ribbon-content-panel">
          {/* HOME TAB - AUTHENTIC OFFICE 365 RIBBON */}
          {activeTab === "Home" && (
            <div className="ribbon-group-row" style={{ overflowX: "auto", flexWrap: "nowrap" }}>
              {/* 1. CLIPBOARD GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-buttons">
                  <button className="ribbon-large-btn" onClick={() => execCmd("paste")} title="Paste (Ctrl+V)">
                    <span className="btn-icon" style={{ fontSize: "16px", fontWeight: 700 }}>📋</span>
                    <span>Paste</span>
                  </button>
                  <div className="ribbon-btn-stack">
                    <button className="ribbon-sm-btn" onClick={() => execCmd("cut")} title="Cut (Ctrl+X)">
                      Cut
                    </button>
                    <button className="ribbon-sm-btn" onClick={() => execCmd("copy")} title="Copy (Ctrl+C)">
                      Copy
                    </button>
                    <button
                      className="ribbon-sm-btn"
                      onClick={() => {
                        if (activeEditor) activeEditor.chain().focus().selectAll().run();
                      }}
                      title="Format Painter"
                    >
                      Painter
                    </button>
                  </div>
                </div>
                <div className="ribbon-group-label">Clipboard</div>
              </div>

              <div className="ribbon-divider" />

              {/* 2. FONT GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-controls">
                  <div className="controls-row">
                    <select
                      className="ribbon-select"
                      value={styleConfig.fontFamily}
                      onChange={(e) => setStyleConfig({ fontFamily: e.target.value })}
                      title="Font Family (50+ Google Fonts)"
                    >
                      <optgroup label="Sans-Serif (Modern)">
                        <option value="Inter, sans-serif">Inter</option>
                        <option value="Roboto, sans-serif">Roboto</option>
                        <option value="Open Sans, sans-serif">Open Sans</option>
                        <option value="Lato, sans-serif">Lato</option>
                        <option value="Montserrat, sans-serif">Montserrat</option>
                        <option value="Poppins, sans-serif">Poppins</option>
                        <option value="Raleway, sans-serif">Raleway</option>
                        <option value="Outfit, sans-serif">Outfit</option>
                        <option value="Ubuntu, sans-serif">Ubuntu</option>
                        <option value="Nunito, sans-serif">Nunito</option>
                        <option value="Work Sans, sans-serif">Work Sans</option>
                        <option value="Quicksand, sans-serif">Quicksand</option>
                        <option value="Arial, sans-serif">Arial</option>
                        <option value="Calibri, sans-serif">Calibri</option>
                        <option value="Trebuchet MS, sans-serif">Trebuchet MS</option>
                        <option value="Verdana, sans-serif">Verdana</option>
                      </optgroup>
                      <optgroup label="Serif (Editorial & Executive)">
                        <option value="Georgia, serif">Georgia</option>
                        <option value="Times New Roman, serif">Times New Roman</option>
                        <option value="Merriweather, serif">Merriweather</option>
                        <option value="Playfair Display, serif">Playfair Display</option>
                        <option value="Lora, serif">Lora</option>
                        <option value="PT Serif, serif">PT Serif</option>
                        <option value="Cormorant Garamond, serif">Cormorant Garamond</option>
                        <option value="EB Garamond, serif">EB Garamond</option>
                        <option value="Bodoni Moda, serif">Bodoni Moda</option>
                        <option value="Cinzel, serif">Cinzel</option>
                        <option value="Garamond, serif">Garamond</option>
                        <option value="Baskerville, serif">Baskerville</option>
                      </optgroup>
                      <optgroup label="Monospace (Code & Technical)">
                        <option value="Fira Code, monospace">Fira Code</option>
                        <option value="JetBrains Mono, monospace">JetBrains Mono</option>
                        <option value="Roboto Mono, monospace">Roboto Mono</option>
                        <option value="Source Code Pro, monospace">Source Code Pro</option>
                        <option value="Inconsolata, monospace">Inconsolata</option>
                        <option value="Space Mono, monospace">Space Mono</option>
                        <option value="Courier New, monospace">Courier New</option>
                      </optgroup>
                      <optgroup label="Display & Headline">
                        <option value="Oswald, sans-serif">Oswald</option>
                        <option value="Bebas Neue, sans-serif">Bebas Neue</option>
                        <option value="Abril Fatface, cursive">Abril Fatface</option>
                        <option value="Righteous, cursive">Righteous</option>
                        <option value="Fredoka, sans-serif">Fredoka</option>
                        <option value="Amatic SC, cursive">Amatic SC</option>
                      </optgroup>
                      <optgroup label="Handwriting & Script">
                        <option value="Caveat, cursive">Caveat</option>
                        <option value="Dancing Script, cursive">Dancing Script</option>
                        <option value="Pacifico, cursive">Pacifico</option>
                        <option value="Lobster, cursive">Lobster</option>
                        <option value="Great Vibes, cursive">Great Vibes</option>
                        <option value="Sacramento, cursive">Sacramento</option>
                        <option value="Satisfy, cursive">Satisfy</option>
                        <option value="Kaushan Script, cursive">Kaushan Script</option>
                        <option value="Shadows Into Light, cursive">Shadows Into Light</option>
                      </optgroup>
                    </select>

                    <select
                      className="ribbon-select ribbon-select-sm"
                      value={styleConfig.fontSize}
                      onChange={(e) => setStyleConfig({ fontSize: e.target.value })}
                      title="Font Size"
                    >
                      <option value="11px">11</option>
                      <option value="12px">12</option>
                      <option value="14px">14</option>
                      <option value="16px">16</option>
                      <option value="18px">18</option>
                      <option value="24px">24</option>
                      <option value="32px">32</option>
                    </select>

                    <button
                      className="ribbon-icon-btn"
                      onClick={() => {
                        const cur = parseInt(styleConfig.fontSize) || 14;
                        setStyleConfig({ fontSize: `${cur + 2}px` });
                      }}
                      title="Grow Font Size"
                    >
                      A⁺
                    </button>
                    <button
                      className="ribbon-icon-btn"
                      onClick={() => {
                        const cur = parseInt(styleConfig.fontSize) || 14;
                        setStyleConfig({ fontSize: `${Math.max(8, cur - 2)}px` });
                      }}
                      title="Shrink Font Size"
                    >
                      A⁻
                    </button>

                    <select
                      className="ribbon-select ribbon-select-sm"
                      title="Change Case"
                      style={{ minWidth: "75px" }}
                      onChange={(e) => {
                        const mode = e.target.value;
                        if (!activeEditor) return;
                        const selText = activeEditor.state.doc.textBetween(activeEditor.state.selection.from, activeEditor.state.selection.to);
                        if (!selText) return;
                        if (mode === "upper") activeEditor.chain().focus().insertContent(selText.toUpperCase()).run();
                        else if (mode === "lower") activeEditor.chain().focus().insertContent(selText.toLowerCase()).run();
                      }}
                    >
                      <option value="">Aa Case</option>
                      <option value="upper">UPPERCASE</option>
                      <option value="lower">lowercase</option>
                    </select>

                    <button
                      className="ribbon-icon-btn"
                      onClick={() => {
                        if (activeEditor) activeEditor.chain().focus().unsetAllMarks().run();
                      }}
                      title="Clear All Formatting"
                    >
                      ⌫ Clear
                    </button>
                  </div>

                  <div className="controls-row">
                    <button className="ribbon-icon-btn" onClick={() => execCmd("bold")} title="Bold (Ctrl+B)">
                      <b>B</b>
                    </button>
                    <button className="ribbon-icon-btn" onClick={() => execCmd("italic")} title="Italic (Ctrl+I)">
                      <i>I</i>
                    </button>
                    <button className="ribbon-icon-btn" onClick={() => execCmd("underline")} title="Underline (Ctrl+U)">
                      <u>U</u>
                    </button>
                    <button className="ribbon-icon-btn" onClick={() => execCmd("strikeThrough")} title="Strikethrough">
                      <s>S</s>
                    </button>
                    <button className="ribbon-icon-btn" onClick={() => execCmd("subscript")} title="Subscript">
                      X₂
                    </button>
                    <button className="ribbon-icon-btn" onClick={() => execCmd("superscript")} title="Superscript">
                      X²
                    </button>
                    <input
                      type="color"
                      className="ribbon-color-picker"
                      value={styleConfig.accentColor}
                      onChange={(e) => setStyleConfig({ accentColor: e.target.value })}
                      title="Font Text Color"
                    />
                    <select
                      className="ribbon-select ribbon-select-sm"
                      title="Text Highlight Color"
                      style={{ minWidth: "85px" }}
                      onChange={(e) => {
                        const bg = e.target.value;
                        if (activeEditor) {
                          activeEditor.chain().focus().setMark("textStyle", { style: `background-color: ${bg}` }).run();
                        }
                      }}
                    >
                      <option value="transparent">Highlight</option>
                      <option value="#fef08a">Yellow</option>
                      <option value="#bbf7d0">Green</option>
                      <option value="#a5f3fc">Cyan</option>
                      <option value="#fbcfe8">Pink</option>
                    </select>
                  </div>
                </div>
                <div className="ribbon-group-label">Font</div>
              </div>

              <div className="ribbon-divider" />

              {/* 3. PARAGRAPH GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-controls">
                  <div className="controls-row">
                    <button
                      className={`ribbon-icon-btn ${activeEditor?.isActive("bulletList") ? "active" : ""}`}
                      onClick={() => execCmd("insertUnorderedList")}
                      title="Bulleted List"
                    >
                      <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor">
                        <circle cx="2.5" cy="4" r="1.2" /><rect x="5.5" y="3" width="9" height="2" rx="0.5" />
                        <circle cx="2.5" cy="8" r="1.2" /><rect x="5.5" y="7" width="9" height="2" rx="0.5" />
                        <circle cx="2.5" cy="12" r="1.2" /><rect x="5.5" y="11" width="9" height="2" rx="0.5" />
                      </svg>
                    </button>
                    <select
                      className="ribbon-select"
                      title="Bullet Style"
                      style={{ padding: "0 2px", fontSize: "10px" }}
                      onChange={(e) => {
                        execCmd("insertUnorderedList");
                        if (activeEditor) activeEditor.chain().focus().updateAttributes("bulletList", { style: e.target.value }).run();
                      }}
                    >
                      <option value="disc">•</option>
                      <option value="circle">◦</option>
                      <option value="square">▪</option>
                      <option value="arrow">➢</option>
                      <option value="check">✓</option>
                    </select>

                    <button
                      className={`ribbon-icon-btn ${activeEditor?.isActive("orderedList") ? "active" : ""}`}
                      onClick={() => execCmd("insertOrderedList")}
                      title="Numbered List"
                    >
                      <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor">
                        <text x="0.5" y="5" fontSize="5.5" fontWeight="bold">1.</text><rect x="5.5" y="3" width="9" height="2" rx="0.5" />
                        <text x="0.5" y="9" fontSize="5.5" fontWeight="bold">2.</text><rect x="5.5" y="7" width="9" height="2" rx="0.5" />
                        <text x="0.5" y="13" fontSize="5.5" fontWeight="bold">3.</text><rect x="5.5" y="11" width="9" height="2" rx="0.5" />
                      </svg>
                    </button>
                    <select
                      className="ribbon-select"
                      title="Numbering Style"
                      style={{ padding: "0 2px", fontSize: "10px" }}
                      onChange={(e) => {
                        execCmd("insertOrderedList");
                        if (activeEditor) activeEditor.chain().focus().updateAttributes("orderedList", { type: e.target.value }).run();
                      }}
                    >
                      <option value="1">1.2.3</option>
                      <option value="a">a.b.c</option>
                      <option value="A">A.B.C</option>
                      <option value="i">i.ii.iii</option>
                    </select>

                    <button
                      className="ribbon-icon-btn"
                      onClick={() => {
                        if (activeEditor) activeEditor.chain().focus().setNode("paragraph", { style: "margin-left: 0cm" }).run();
                      }}
                      title="Decrease Indent"
                    >
                      <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M1 3h14v1.8H1V3zm4 3.8h10v1.8H5V6.8zm0 3.8h10v1.8H5v-1.8zM1.5 5.5L4 8 1.5 10.5V5.5z"/>
                      </svg>
                    </button>
                    <button
                      className="ribbon-icon-btn"
                      onClick={() => {
                        if (activeEditor) activeEditor.chain().focus().setNode("paragraph", { style: "margin-left: 1cm" }).run();
                      }}
                      title="Increase Indent"
                    >
                      <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M1 3h14v1.8H1V3zm0 3.8h10v1.8H1V6.8zm0 3.8h10v1.8H1v-1.8zM14.5 5.5L12 8l2.5 2.5V5.5z"/>
                      </svg>
                    </button>
                  </div>

                  <div className="controls-row">
                    <button
                      className={`ribbon-icon-btn ${activeEditor?.isActive({ textAlign: "left" }) ? "active" : ""}`}
                      onClick={() => execCmd("justifyLeft")}
                      title="Align Left"
                    >
                      <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor">
                        <rect x="2" y="3" width="12" height="1.8" rx="0.4" />
                        <rect x="2" y="6.5" width="8" height="1.8" rx="0.4" />
                        <rect x="2" y="10" width="12" height="1.8" rx="0.4" />
                        <rect x="2" y="13.5" width="6" height="1.8" rx="0.4" />
                      </svg>
                    </button>
                    <button
                      className={`ribbon-icon-btn ${activeEditor?.isActive({ textAlign: "center" }) ? "active" : ""}`}
                      onClick={() => execCmd("justifyCenter")}
                      title="Center"
                    >
                      <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor">
                        <rect x="2" y="3" width="12" height="1.8" rx="0.4" />
                        <rect x="4" y="6.5" width="8" height="1.8" rx="0.4" />
                        <rect x="2" y="10" width="12" height="1.8" rx="0.4" />
                        <rect x="5" y="13.5" width="6" height="1.8" rx="0.4" />
                      </svg>
                    </button>
                    <button
                      className={`ribbon-icon-btn ${activeEditor?.isActive({ textAlign: "right" }) ? "active" : ""}`}
                      onClick={() => execCmd("justifyRight")}
                      title="Align Right"
                    >
                      <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor">
                        <rect x="2" y="3" width="12" height="1.8" rx="0.4" />
                        <rect x="6" y="6.5" width="8" height="1.8" rx="0.4" />
                        <rect x="2" y="10" width="12" height="1.8" rx="0.4" />
                        <rect x="8" y="13.5" width="6" height="1.8" rx="0.4" />
                      </svg>
                    </button>
                    <button
                      className={`ribbon-icon-btn ${activeEditor?.isActive({ textAlign: "justify" }) ? "active" : ""}`}
                      onClick={() => execCmd("justifyFull")}
                      title="Justify"
                    >
                      <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor">
                        <rect x="2" y="3" width="12" height="1.8" rx="0.4" />
                        <rect x="2" y="6.5" width="12" height="1.8" rx="0.4" />
                        <rect x="2" y="10" width="12" height="1.8" rx="0.4" />
                        <rect x="2" y="13.5" width="12" height="1.8" rx="0.4" />
                      </svg>
                    </button>

                    <div style={{ display: "flex", alignItems: "center", gap: "2px" }}>
                      <span title="Line & Paragraph Spacing" style={{ display: "inline-flex", opacity: 0.8 }}>
                        <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">
                          <path d="M2.5 4L4 1.5 5.5 4H4v8h1.5L4 14.5 2.5 12H4V4H2.5z"/>
                          <rect x="7" y="3" width="7" height="1.8" rx="0.4" />
                          <rect x="7" y="7" width="7" height="1.8" rx="0.4" />
                          <rect x="7" y="11" width="7" height="1.8" rx="0.4" />
                        </svg>
                      </span>
                      <select
                        className="ribbon-select"
                        title="Line Spacing"
                        style={{ padding: "0 4px", fontSize: "11px" }}
                        value={styleConfig.paragraphSpacing || "1.4"}
                        onChange={(e) => setStyleConfig({ paragraphSpacing: e.target.value })}
                      >
                        <option value="1.0">1.0</option>
                        <option value="1.15">1.15</option>
                        <option value="1.4">1.4</option>
                        <option value="1.6">1.6</option>
                        <option value="2.0">2.0</option>
                      </select>
                    </div>
                  </div>
                </div>
                <div className="ribbon-group-label">Paragraph</div>
              </div>

              <div className="ribbon-divider" />

              {/* 4. STYLES GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-controls">
                  <div style={{ display: "flex", gap: "6px" }}>
                    {[
                      { label: "Normal", val: "p", preview: "AaBbCc" },
                      { label: "Heading 1", val: "h1", preview: "AaBb" },
                      { label: "Heading 2", val: "h2", preview: "AaBb" },
                      { label: "Heading 3", val: "h3", preview: "AaBb" },
                    ].map((s) => (
                      <button
                        key={s.val}
                        onClick={() => execCmd("formatBlock", s.val)}
                        className="ribbon-icon-btn"
                        style={{
                          height: "44px",
                          flexDirection: "column",
                          padding: "4px 8px",
                          fontSize: "11px",
                          textAlign: "center",
                        }}
                      >
                        <div style={{ fontSize: "12px", fontWeight: 700, color: "#2563eb" }}>{s.preview}</div>
                        <div style={{ fontSize: "10px", opacity: 0.8 }}>{s.label}</div>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="ribbon-group-label">Styles</div>
              </div>

              <div className="ribbon-divider" />

              {/* 5. EDITING GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-buttons">
                  <div className="ribbon-btn-stack">
                    <button
                      className="ribbon-sm-btn"
                      onClick={() => setIsFindReplaceOpen(true)}
                      title="Find and Replace (Ctrl+H)"
                    >
                      Find & Replace
                    </button>
                    <button
                      className="ribbon-sm-btn"
                      onClick={() => setIsWordCountOpen(true)}
                      title="Word Count & Statistics"
                    >
                      Word Count
                    </button>
                    <button
                      className="ribbon-sm-btn"
                      onClick={() => {
                        if (activeEditor) activeEditor.chain().focus().selectAll().run();
                      }}
                      title="Select All Content"
                    >
                      Select All
                    </button>
                  </div>
                </div>
                <div className="ribbon-group-label">Editing</div>
              </div>

              <div className="ribbon-divider ribbon-optional" />

              {/* 6. ADOBE ACROBAT GROUP (Optional on large screens) */}
              <div className="ribbon-group ribbon-optional">
                <div className="ribbon-group-buttons">
                  <div className="ribbon-btn-stack">
                    <button
                      className="ribbon-sm-btn"
                      onClick={() => exportToPdf(segments, "Procurement Proposal Document", pageLayoutSize, styleConfig)}
                      title="Create & Share PDF"
                    >
                      Acrobat PDF
                    </button>
                    <button
                      className="ribbon-sm-btn"
                      onClick={() => setModalType("comment")}
                      title="Request Signatures / Notes"
                    >
                      Signatures
                    </button>
                  </div>
                </div>
                <div className="ribbon-group-label">Acrobat & Add-ins</div>
              </div>
            </div>
          )}

          {/* INSERT TAB - AUTHENTIC OFFICE 365 RIBBON */}
          {activeTab === "Insert" && (
            <div className="ribbon-group-row">
              {/* 1. PAGES GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-buttons">
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <button className="ribbon-large-btn" onClick={() => setModalType("cover-page")}>
                      <span className="btn-icon">📘</span>
                      <span>Cover Page</span>
                    </button>
                    <select
                      className="ribbon-select"
                      style={{ fontSize: "10px", padding: "1px 4px", maxWidth: "80px" }}
                      onChange={(e) => {
                        const style = e.target.value;
                        if (activeEditor) {
                          if (style === "corporate") {
                            activeEditor.chain().focus().insertContent(`<div style="border-left: 6px solid #1a73e8; padding: 20px; background: #f8fafc; margin-bottom: 20px;"><h2>Corporate Proposal Cover</h2><p>Enterprise RFP Specification</p></div>`).run();
                          } else if (style === "minimal") {
                            activeEditor.chain().focus().insertContent(`<div style="text-align: center; padding: 40px 0; border-bottom: 2px solid #333;"><h1 style="letter-spacing: 2px;">PROCUREMENT PROPOSAL</h1></div>`).run();
                          }
                        }
                      }}
                    >
                      <option value="corporate">Corporate</option>
                      <option value="minimal">Minimal</option>
                      <option value="tech">Tech</option>
                    </select>
                  </div>
                  <button className="ribbon-large-btn" onClick={() => addPage()}>
                    <span className="btn-icon">📄</span>
                    <span>Blank Page</span>
                  </button>
                  <button className="ribbon-large-btn" onClick={() => execCmd("insertHorizontalRule")}>
                    <span className="btn-icon">⟾</span>
                    <span>Page Break</span>
                  </button>
                </div>
                <div className="ribbon-group-label">Pages</div>
              </div>

              <div className="ribbon-divider" />

              {/* 2. TABLES GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-buttons">
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <button className="ribbon-large-btn" onClick={() => execCmd("insertTable")}>
                      <span className="btn-icon">📊</span>
                      <span>Table</span>
                    </button>
                    <select
                      className="ribbon-select"
                      style={{ fontSize: "10px", padding: "1px 4px", maxWidth: "75px" }}
                      onChange={(e) => {
                        const val = e.target.value;
                        if (!activeEditor) return;
                        if (val === "2x2") activeEditor.chain().focus().insertTable({ rows: 2, cols: 2, withHeaderRow: true }).run();
                        else if (val === "3x3") activeEditor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run();
                        else if (val === "4x4") activeEditor.chain().focus().insertTable({ rows: 4, cols: 4, withHeaderRow: true }).run();
                        else if (val === "5x5") activeEditor.chain().focus().insertTable({ rows: 5, cols: 5, withHeaderRow: true }).run();
                        else if (val === "custom") setModalType("custom-table");
                      }}
                    >
                      <option value="3x3">3x3 Grid</option>
                      <option value="2x2">2x2</option>
                      <option value="4x4">4x4</option>
                      <option value="5x5">5x5</option>
                      <option value="custom">Custom...</option>
                    </select>
                  </div>
                </div>
                <div className="ribbon-group-label">Tables</div>
              </div>

              <div className="ribbon-divider" />

              {/* 3. ILLUSTRATIONS GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-buttons">
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <button className="ribbon-large-btn" onClick={() => setModalType("picture")}>
                      <span className="btn-icon">🖼️</span>
                      <span>Pictures</span>
                    </button>
                    <select
                      className="ribbon-select"
                      style={{ fontSize: "10px", padding: "1px 4px", maxWidth: "80px" }}
                      title="Image Text Wrap"
                      onChange={(e) => {
                        const align = e.target.value;
                        if (activeEditor) {
                          activeEditor.chain().focus().updateAttributes("image", { alignment: align }).run();
                        }
                      }}
                    >
                      <option value="center">Center</option>
                      <option value="left">Left Wrap</option>
                      <option value="right">Right Wrap</option>
                    </select>
                  </div>

                  <div className="ribbon-btn-stack">
                    <button
                      className="ribbon-sm-btn"
                      onClick={() => {
                        if (activeEditor) {
                          activeEditor.chain().focus().insertContent(`<div style="width: 100%; height: 2px; background: var(--doc-accent-color, #1a73e8); margin: 16px 0;"></div>`).run();
                        }
                      }}
                      title="Insert Shapes"
                    >
                      Shapes
                    </button>
                    <button className="ribbon-sm-btn" onClick={() => setModalType("icons")} title="Insert Icons">
                      Icons
                    </button>
                  </div>

                  <div className="ribbon-btn-stack">
                    <button
                      className="ribbon-sm-btn"
                      onClick={() => {
                        if (activeEditor) {
                          activeEditor.chain().focus().insertContent(`
                            <div style="display: flex; gap: 12px; margin: 16px 0;">
                              <div style="flex: 1; padding: 12px; background: #e8f0fe; border-radius: 6px; text-align: center; font-weight: 600;">Phase 1</div>
                              <div style="flex: 1; padding: 12px; background: #e6f4ea; border-radius: 6px; text-align: center; font-weight: 600;">Phase 2</div>
                              <div style="flex: 1; padding: 12px; background: #fef7e0; border-radius: 6px; text-align: center; font-weight: 600;">Phase 3</div>
                            </div>
                          `).run();
                        }
                      }}
                      title="Insert SmartArt"
                    >
                      SmartArt
                    </button>
                    <button
                      className="ribbon-sm-btn"
                      onClick={() => {
                        if (activeEditor) {
                          activeEditor.chain().focus().insertTable({ rows: 4, cols: 3, withHeaderRow: true }).run();
                        }
                      }}
                      title="Insert Chart"
                    >
                      Chart
                    </button>
                  </div>
                </div>
                <div className="ribbon-group-label">Illustrations</div>
              </div>

              <div className="ribbon-divider" />

              {/* 4. MEDIA & LINKS GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-buttons">
                  <div className="ribbon-btn-stack">
                    <button className="ribbon-sm-btn" onClick={() => setModalType("video")} title="Insert Video">
                      Video
                    </button>
                    <button className="ribbon-sm-btn" onClick={() => setModalType("link")} title="Insert Link">
                      Link
                    </button>
                    <button className="ribbon-sm-btn" onClick={() => setModalType("bookmark")} title="Insert Bookmark">
                      Bookmark
                    </button>
                  </div>
                </div>
                <div className="ribbon-group-label">Media & Links</div>
              </div>

              <div className="ribbon-divider" />

              {/* 5. COMMENTS GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-buttons">
                  <button className="ribbon-large-btn" onClick={() => setModalType("comment")}>
                    <span className="btn-icon">💬</span>
                    <span>Comment</span>
                  </button>
                </div>
                <div className="ribbon-group-label">Comments</div>
              </div>

              <div className="ribbon-divider" />

              {/* 6. HEADER & FOOTER GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-buttons">
                  <div className="ribbon-btn-stack">
                    <button className="ribbon-sm-btn" onClick={() => setModalType("header")}>
                      Header
                    </button>
                    <button className="ribbon-sm-btn" onClick={() => setStyleConfig({ showHeaderFooter: true })}>
                      Footer
                    </button>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <button className="ribbon-large-btn" onClick={() => setStyleConfig({ showPageNumbers: true, pageNumberPosition: "bottom-right" })}>
                      <span className="btn-icon">🔢</span>
                      <span>Page Number</span>
                    </button>
                    <select
                      className="ribbon-select"
                      style={{ fontSize: "10px", padding: "1px 4px", maxWidth: "90px" }}
                      value={styleConfig.pageNumberPosition || "bottom-right"}
                      onChange={(e) => {
                        const val = e.target.value as any;
                        if (val === "none") setStyleConfig({ showPageNumbers: false, pageNumberPosition: "none" });
                        else setStyleConfig({ showPageNumbers: true, pageNumberPosition: val });
                      }}
                    >
                      <option value="bottom-right">Bottom-Right</option>
                      <option value="bottom-center">Bottom-Center</option>
                      <option value="top-right">Top-Right</option>
                      <option value="none">Hide</option>
                    </select>
                  </div>
                </div>
                <div className="ribbon-group-label">Header & Footer</div>
              </div>

              <div className="ribbon-divider" />

              {/* 7. TEXT GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-buttons">
                  <div className="ribbon-btn-stack">
                    <button
                      className="ribbon-sm-btn"
                      onClick={() => {
                        if (activeEditor) {
                          activeEditor.chain().focus().insertContent(`
                            <div style="border: 2px dashed #1a73e8; background: #f8fafc; padding: 16px; border-radius: 8px; margin: 16px 0;">
                              <p style="margin: 0; font-weight: 600; color: #1a73e8;">📦 Floating Callout Text Box</p>
                              <p style="margin-top: 4px; font-size: 13px;">Type key notes or scope summaries here...</p>
                            </div>
                          `).run();
                        }
                      }}
                    >
                      Text Box
                    </button>
                    <button className="ribbon-sm-btn" onClick={() => setModalType("wordart")}>
                      WordArt
                    </button>
                  </div>

                  <div className="ribbon-btn-stack">
                    <button
                      className="ribbon-sm-btn"
                      onClick={() => {
                        if (activeEditor) {
                          activeEditor.chain().focus().insertContent(`
                            <table border="1" style="width:100%; border-collapse:collapse; margin:20px 0;">
                              <tr>
                                <th style="padding:10px; background:#f1f5f9;">Purchaser Authorized Officer</th>
                                <th style="padding:10px; background:#f1f5f9;">Vendor Authorized Officer</th>
                              </tr>
                              <tr>
                                <td style="padding:20px;">Signature: ____________________<br>Name: Gulmira Abdullaeva<br>Date: ${new Date().toLocaleDateString()}</td>
                                <td style="padding:20px;">Signature: ____________________<br>Name: Abdalah Jadaan<br>Seal: [ Corporate Seal ]</td>
                              </tr>
                            </table>
                          `).run();
                        }
                      }}
                    >
                      Signature Line
                    </button>
                    <button
                      className="ribbon-sm-btn"
                      onClick={() => {
                        if (activeEditor) {
                          activeEditor.chain().focus().insertContent(` ${new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })} `).run();
                        }
                      }}
                    >
                      Date & Time
                    </button>
                  </div>
                </div>
                <div className="ribbon-group-label">Text & Signatures</div>
              </div>

              <div className="ribbon-divider" />

              {/* 8. SYMBOLS GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-buttons">
                  <div className="ribbon-btn-stack">
                    <button
                      className="ribbon-sm-btn"
                      onClick={() => {
                        if (activeEditor) {
                          activeEditor.chain().focus().insertContent(` <span style="font-family: math, serif; font-style: italic; background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">T_res ≤ 2h • Uptime ≥ 99.9%</span> `).run();
                        }
                      }}
                    >
                      Equation
                    </button>
                    <button
                      className="ribbon-sm-btn"
                      onClick={() => setModalType("symbols")}
                    >
                      Symbol
                    </button>
                  </div>
                </div>
                <div className="ribbon-group-label">Symbols</div>
              </div>
            </div>
          )}

          {/* DESIGN TAB */}
          {activeTab === "Design" && (
            <div className="ribbon-group-row">
              {/* Themes Group */}
              <div className="ribbon-group">
                <div className="ribbon-group-controls">
                  <select
                    className="ribbon-select"
                    value={styleConfig.theme || "Office"}
                    onChange={(e) => {
                      const theme = e.target.value;
                      let accent = "#1a73e8";
                      let font = "Inter, sans-serif";
                      if (theme === "Corporate") { accent = "#0f4c81"; font = "Calibri, sans-serif"; }
                      if (theme === "Creative") { accent = "#9c27b0"; font = "Outfit, sans-serif"; }
                      if (theme === "Minimalist") { accent = "#333333"; font = "Arial, sans-serif"; }
                      if (theme === "Tech") { accent = "#0070f3"; font = "Roboto, sans-serif"; }
                      if (theme === "Elegant") { accent = "#8e24aa"; font = "Georgia, serif"; }
                      setStyleConfig({ theme, accentColor: accent, fontFamily: font });
                    }}
                  >
                    <option value="Office">Office (Classic)</option>
                    <option value="Corporate">Corporate Navy</option>
                    <option value="Creative">Creative Purple</option>
                    <option value="Minimalist">Minimalist Dark</option>
                    <option value="Tech">Tech Modern</option>
                    <option value="Elegant">Elegant Serif</option>
                  </select>
                </div>
                <div className="ribbon-group-label">Themes</div>
              </div>

              <div className="ribbon-divider" />

              {/* Color Palette & Font Pairs */}
              <div className="ribbon-group">
                <div className="ribbon-group-controls">
                  <div className="controls-row">
                    <label style={{ fontSize: "11px", display: "flex", alignItems: "center", gap: "6px" }}>
                      Palette:
                      <select
                        className="ribbon-select"
                        value={styleConfig.colorPalette || "Office Blue"}
                        onChange={(e) => {
                          const palette = e.target.value;
                          let color = "#1a73e8";
                          if (palette === "Emerald") color = "#0f9d58";
                          if (palette === "Crimson") color = "#ea4335";
                          if (palette === "Violet") color = "#673ab7";
                          if (palette === "Sunset") color = "#ff6d00";
                          if (palette === "Slate") color = "#455a64";
                          setStyleConfig({ colorPalette: palette, accentColor: color });
                        }}
                      >
                        <option value="Office Blue">Office Blue</option>
                        <option value="Emerald">Emerald Green</option>
                        <option value="Crimson">Crimson Red</option>
                        <option value="Violet">Purple Violet</option>
                        <option value="Sunset">Sunset Orange</option>
                        <option value="Slate">Dark Slate</option>
                      </select>
                    </label>

                    <label style={{ fontSize: "11px", display: "flex", alignItems: "center", gap: "6px" }}>
                      Font Pair:
                      <select
                        className="ribbon-select"
                        value={styleConfig.fontPairing || "Inter / Roboto"}
                        onChange={(e) => {
                          const pairing = e.target.value;
                          let mainFont = "Inter, sans-serif";
                          if (pairing === "Calibri / Arial") mainFont = "Calibri, sans-serif";
                          if (pairing === "Georgia / Garamond") mainFont = "Georgia, serif";
                          if (pairing === "Outfit / Inter") mainFont = "Outfit, sans-serif";
                          setStyleConfig({ fontPairing: pairing, fontFamily: mainFont });
                        }}
                      >
                        <option value="Inter / Roboto">Inter / Roboto</option>
                        <option value="Calibri / Arial">Calibri / Arial</option>
                        <option value="Georgia / Garamond">Georgia / Garamond</option>
                        <option value="Outfit / Inter">Outfit / Inter</option>
                      </select>
                    </label>
                  </div>
                </div>
                <div className="ribbon-group-label">Color & Font System</div>
              </div>

              <div className="ribbon-divider" />

              {/* Spacing Group */}
              <div className="ribbon-group">
                <div className="ribbon-group-controls">
                  <label style={{ fontSize: "11px", display: "flex", alignItems: "center", gap: "6px" }}>
                    Spacing:
                    <select
                      className="ribbon-select"
                      value={styleConfig.paragraphSpacing || "1.4"}
                      onChange={(e) => setStyleConfig({ paragraphSpacing: e.target.value })}
                    >
                      <option value="1.0">Compact (1.0)</option>
                      <option value="1.15">Tight (1.15)</option>
                      <option value="1.4">Standard (1.4)</option>
                      <option value="1.6">Relaxed (1.6)</option>
                      <option value="2.0">Double (2.0)</option>
                    </select>
                  </label>
                </div>
                <div className="ribbon-group-label">Paragraph Spacing</div>
              </div>

              <div className="ribbon-divider" />

              {/* Page Background Group */}
              <div className="ribbon-group">
                <div className="ribbon-group-controls">
                  <div className="controls-row">
                    <label style={{ fontSize: "11px", display: "flex", alignItems: "center", gap: "6px" }}>
                      Watermark:
                      <select
                        className="ribbon-select"
                        value={["", "DRAFT", "CONFIDENTIAL", "URGENT", "SAMPLE"].includes(styleConfig.watermark || "") ? styleConfig.watermark || "" : "CUSTOM"}
                        onChange={(e) => {
                          if (e.target.value === "CUSTOM") {
                            setStyleConfig({ watermark: "CONFIDENTIAL PROPOSAL" });
                          } else {
                            setStyleConfig({ watermark: e.target.value });
                          }
                        }}
                      >
                        <option value="">(None)</option>
                        <option value="DRAFT">DRAFT</option>
                        <option value="CONFIDENTIAL">CONFIDENTIAL</option>
                        <option value="URGENT">URGENT</option>
                        <option value="SAMPLE">SAMPLE</option>
                        <option value="CUSTOM">Custom...</option>
                      </select>
                      {styleConfig.watermark && (
                        <input
                          type="text"
                          value={styleConfig.watermark}
                          onChange={(e) => setStyleConfig({ watermark: e.target.value })}
                          placeholder="Watermark text..."
                          style={{
                            fontSize: "11px",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            width: "110px",
                            border: "1px solid #cbd5e1",
                            background: isDarkMode ? "rgba(255,255,255,0.08)" : "#ffffff",
                            color: isDarkMode ? "#f8fafc" : "#0f172a",
                          }}
                        />
                      )}
                    </label>

                    <label style={{ fontSize: "11px", display: "flex", alignItems: "center", gap: "6px" }}>
                      Page Color:
                      <select
                        className="ribbon-select"
                        value={styleConfig.pageColor || "#ffffff"}
                        onChange={(e) => setStyleConfig({ pageColor: e.target.value })}
                      >
                        <option value="#ffffff">Pure White</option>
                        <option value="#f8f9fa">Off White</option>
                        <option value="#faf8f5">Cream</option>
                        <option value="#f0f2f5">Soft Gray</option>
                        <option value="#1e1e2e">Dark Mode</option>
                      </select>
                    </label>

                    <label style={{ fontSize: "11px", display: "flex", alignItems: "center", gap: "6px" }}>
                      Border:
                      <select
                        className="ribbon-select"
                        value={styleConfig.pageBorder || "none"}
                        onChange={(e) => setStyleConfig({ pageBorder: e.target.value })}
                      >
                        <option value="none">None</option>
                        <option value="1px solid #dadce0">Solid Box</option>
                        <option value="3px double #1a73e8">Double Line</option>
                        <option value="2px dashed #1a73e8">Dashed Accent</option>
                      </select>
                    </label>
                  </div>
                </div>
                <div className="ribbon-group-label">Page Background</div>
              </div>
            </div>
          )}

          {/* LAYOUT TAB - AUTHENTIC OFFICE RIBBON */}
          {activeTab === "Layout" && (
            <div className="ribbon-group-row" style={{ overflowX: "auto", flexWrap: "nowrap" }}>
              {/* 1. PAGE SETUP GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-controls">
                  <div className="controls-row" style={{ gap: "10px" }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                      <button
                        className="ribbon-large-btn"
                        onClick={() => {
                          const elements = document.querySelectorAll<HTMLElement>(".segment-block");
                          elements.forEach((el) => (el.style.padding = "48px 56px"));
                        }}
                      >
                        <span className="btn-icon">📐</span>
                        <span>Margins</span>
                      </button>
                      <select
                        className="ribbon-select ribbon-select-sm"
                        style={{ fontSize: "10px", padding: "1px 4px" }}
                        onChange={(e) => {
                          const m = e.target.value;
                          const elements = document.querySelectorAll<HTMLElement>(".segment-block");
                          elements.forEach((el) => {
                            if (m === "narrow") el.style.padding = "24px 32px";
                            else if (m === "wide") el.style.padding = "64px 80px";
                            else el.style.padding = "48px 56px";
                          });
                        }}
                      >
                        <option value="normal">Normal (1 in)</option>
                        <option value="narrow">Narrow (0.5 in)</option>
                        <option value="wide">Wide (1.5 in)</option>
                      </select>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                      <button
                        className="ribbon-large-btn"
                        onClick={() => {
                          const elements = document.querySelectorAll<HTMLElement>(".segment-block");
                          elements.forEach((el) => {
                            el.style.width = "794px";
                            el.style.minHeight = "1123px";
                          });
                        }}
                      >
                        <span className="btn-icon">🔄</span>
                        <span>Orientation</span>
                      </button>
                      <select
                        className="ribbon-select ribbon-select-sm"
                        style={{ fontSize: "10px", padding: "1px 4px" }}
                        onChange={(e) => {
                          const o = e.target.value;
                          const elements = document.querySelectorAll<HTMLElement>(".segment-block");
                          elements.forEach((el) => {
                            if (o === "landscape") {
                              el.style.width = "1123px";
                              el.style.minHeight = "794px";
                            } else {
                              el.style.width = "794px";
                              el.style.minHeight = "1123px";
                            }
                          });
                        }}
                      >
                        <option value="portrait">Portrait</option>
                        <option value="landscape">Landscape</option>
                      </select>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                      <button className="ribbon-large-btn">
                        <span className="btn-icon">📜</span>
                        <span>Size</span>
                      </button>
                      <select
                        className="ribbon-select ribbon-select-sm"
                        style={{ fontSize: "10px", padding: "1px 4px" }}
                        value={pageLayoutSize}
                        onChange={(e) => setPageLayoutSize(e.target.value as any)}
                      >
                        <option value="A4">A4 (210 x 297 mm)</option>
                        <option value="Letter">Letter (8.5 x 11 in)</option>
                        <option value="A3">A3 (297 x 420 mm)</option>
                        <option value="Legal">Legal (8.5 x 14 in)</option>
                      </select>
                    </div>

                    <div className="ribbon-btn-stack">
                      <button
                        className="ribbon-sm-btn"
                        onClick={() => {
                          if (activeEditor) {
                            activeEditor.chain().focus().insertContent(`<div style="column-count: 2; column-gap: 20px;"><p>Two-column text column section begins here...</p></div>`).run();
                          }
                        }}
                      >
                        🏛️ Columns
                      </button>
                      <button className="ribbon-sm-btn" onClick={() => execCmd("insertHorizontalRule")}>
                        ⟾ Breaks
                      </button>
                      <button
                        className="ribbon-sm-btn"
                        onClick={() => {
                          if (activeEditor) activeEditor.chain().focus().insertContent(`<ol style="list-style-type: decimal;"><li>Numbered line item</li></ol>`).run();
                        }}
                      >
                        🔢 Line Numbers
                      </button>
                    </div>
                  </div>
                </div>
                <div className="ribbon-group-label">Page Setup</div>
              </div>

              <div className="ribbon-divider" />

              {/* 2. PARAGRAPH GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-controls">
                  <div style={{ display: "flex", flexDirection: "column", gap: "4px", fontSize: "11px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span>Indent:</span>
                      <label style={{ display: "flex", alignItems: "center", gap: "2px" }}>
                        Left:
                        <select
                          className="ribbon-select ribbon-select-sm"
                          style={{ fontSize: "10px", padding: "1px 4px" }}
                          onChange={(e) => {
                            if (activeEditor) activeEditor.chain().focus().setNode("paragraph", { style: `margin-left: ${e.target.value}` }).run();
                          }}
                        >
                          <option value="0cm">0 cm</option>
                          <option value="0.5cm">0.5 cm</option>
                          <option value="1cm">1 cm</option>
                          <option value="1.5cm">1.5 cm</option>
                        </select>
                      </label>
                      <label style={{ display: "flex", alignItems: "center", gap: "2px" }}>
                        Right:
                        <select
                          className="ribbon-select ribbon-select-sm"
                          style={{ fontSize: "10px", padding: "1px 4px" }}
                          onChange={(e) => {
                            if (activeEditor) activeEditor.chain().focus().setNode("paragraph", { style: `margin-right: ${e.target.value}` }).run();
                          }}
                        >
                          <option value="0cm">0 cm</option>
                          <option value="0.5cm">0.5 cm</option>
                          <option value="1cm">1 cm</option>
                        </select>
                      </label>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span>Spacing:</span>
                      <label style={{ display: "flex", alignItems: "center", gap: "2px" }}>
                        Before:
                        <select
                          className="ribbon-select ribbon-select-sm"
                          style={{ fontSize: "10px", padding: "1px 4px" }}
                          onChange={(e) => {
                            if (activeEditor) activeEditor.chain().focus().setNode("paragraph", { style: `margin-top: ${e.target.value}` }).run();
                          }}
                        >
                          <option value="0pt">0 pt</option>
                          <option value="6pt">6 pt</option>
                          <option value="12pt">12 pt</option>
                        </select>
                      </label>
                      <label style={{ display: "flex", alignItems: "center", gap: "2px" }}>
                        After:
                        <select
                          className="ribbon-select ribbon-select-sm"
                          style={{ fontSize: "10px", padding: "1px 4px" }}
                          value={styleConfig.paragraphSpacing || "8pt"}
                          onChange={(e) => setStyleConfig({ paragraphSpacing: e.target.value })}
                        >
                          <option value="0pt">0 pt</option>
                          <option value="6pt">6 pt</option>
                          <option value="8pt">8 pt</option>
                          <option value="12pt">12 pt</option>
                        </select>
                      </label>
                    </div>
                  </div>
                </div>
                <div className="ribbon-group-label">Paragraph</div>
              </div>

              <div className="ribbon-divider" />

              {/* 3. ARRANGE GROUP */}
              <div className="ribbon-group">
                <div className="ribbon-group-controls">
                  <div className="controls-row" style={{ gap: "8px" }}>
                    <div className="ribbon-btn-stack">
                      <button
                        className="ribbon-sm-btn"
                        onClick={() => {
                          if (activeEditor) activeEditor.chain().focus().updateAttributes("image", { alignment: "center" }).run();
                        }}
                      >
                        📌 Position
                      </button>
                      <button
                        className="ribbon-sm-btn"
                        onClick={() => {
                          if (activeEditor) activeEditor.chain().focus().updateAttributes("image", { alignment: "left" }).run();
                        }}
                      >
                        🔄 Wrap Text
                      </button>
                    </div>

                    <div className="ribbon-btn-stack">
                      <button className="ribbon-sm-btn" onClick={() => execCmd("justifyCenter")}>
                        🎯 Align Center
                      </button>
                      <button className="ribbon-sm-btn" onClick={() => execCmd("justifyLeft")}>
                        ⬅️ Align Left
                      </button>
                    </div>
                  </div>
                </div>
                <div className="ribbon-group-label">Arrange</div>
              </div>
            </div>
          )}

          {/* FILE TAB */}
          {activeTab === "File" && (
            <div className="ribbon-group-row">
              <div className="ribbon-group">
                <div className="ribbon-group-buttons">
                  <button className="ribbon-large-btn" onClick={() => startNewSession()}>
                    <span className="btn-icon">📄</span>
                    <span>New Document</span>
                  </button>
                  <button className="ribbon-large-btn" onClick={() => onOpenSavedSessions?.()}>
                    <span className="btn-icon">📂</span>
                    <span>Open Session</span>
                  </button>
                  <button className="ribbon-large-btn" onClick={() => setIsPreviewOpen(true)}>
                    <span className="btn-icon">🖨️</span>
                    <span>Print & Export</span>
                  </button>
                  <button
                    className="ribbon-large-btn"
                    onClick={() => exportToPdf(segments, "Procurement Proposal Document", pageLayoutSize, styleConfig)}
                  >
                    <span className="btn-icon">📄</span>
                    <span>Download PDF</span>
                  </button>
                  <button
                    className="ribbon-large-btn"
                    onClick={() => exportToWord(segments, "Procurement Proposal Document", styleConfig)}
                  >
                    <span className="btn-icon">📝</span>
                    <span>Download Word</span>
                  </button>
                  <button
                    className="ribbon-large-btn"
                    onClick={() => exportToTxt(segments, "Procurement Proposal Document")}
                  >
                    <span className="btn-icon">📥</span>
                    <span>Download Text</span>
                  </button>
                </div>
                <div className="ribbon-group-label">Document Actions & Exports</div>
              </div>
            </div>
          )}
        </div>
      )}

      <PrintPreviewModal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        onConfirmDownload={handleConfirmDownload}
      />

      <InsertItemModal
        type={modalType}
        onClose={() => setModalType(null)}
        onConfirm={handleModalConfirm}
      />

      <FindReplaceModal
        isOpen={isFindReplaceOpen}
        onClose={() => setIsFindReplaceOpen(false)}
      />

      <WordCountModal
        isOpen={isWordCountOpen}
        onClose={() => setIsWordCountOpen(false)}
      />
    </div>
  );
}
