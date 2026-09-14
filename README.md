# Procurement RAG — Enterprise AI Document Editor & RAG Agent Co-Pilot

A state-of-the-art **MS Word-like Multi-Page Document Editor & Procurement RAG System** built with **FastAPI**, **LangGraph AI Agents**, **React 18**, and **TipTap**. 

Designed specifically for enterprise merchants, engineering firms, and procurement officers to generate, edit, format, and audit complex RFP, RFQ, RFI, SOW, and Contract documents in seconds.

---

## 🌟 Key Features

### 📄 1. MS Word-Style Multi-Page Document Editor
- **Automatic Multi-Page Pagination**: Monitors printable page canvas height in real-time. When text or table content exceeds printable page limits (`980px` A4), it automatically pops overflow content into the next page or creates a new page card.
- **Interactive Drag & Resize for Images & Flowcharts**: Click any diagram or image to reveal active corner drag handles (`top-left`, `bottom-right`) and a floating quick-action alignment toolbar (`⬅️ Left Wrap`, `↔️ Center`, `➡️ Right Wrap`, `🗑️ Delete`).
- **Native TipTap Tables**: Full support for interactive tables with crisp grid borders, header styling, zebra striping, and resizable columns.
- **Auto Backspace Page Merging**: Pressing `Backspace` at position 1 of an empty page card automatically deletes the page and merges focus back to the previous page.
- **Page Layout Customization**: Real-time paper size switching (`A4`, `US Letter`, `A3`, `Legal`), zoom scaling, theme palettes, typography pairings, and custom per-page watermark overlays.

### 🤖 2. RAG Agent Co-Pilot ("Help Bot")
- **Multi-Agent LangGraph Pipeline**: Powered by specialized sub-agents:
  - **Layout Composer Agent**: Numbers headings hierarchically (`1. Scope of Work`, `1.1 Details`), injects executive summary callout cards, and structures document flow.
  - **Image & Diagram Extractor Agent**: Generates vector SVG flowcharts via QuickChart Mermaid.js and scans/extracts embedded diagrams from uploaded PDF and DOCX reference files.
  - **Aesthetic Stylist Agent**: Polishes document typography, page border accents, and corporate confidentiality watermarks.
- **Surgical Section Refinement**: Highlight text or ask Help Bot to update specific document sections without re-generating the rest of the document.
- **Quick Actions**: One-click `📥 Insert to Editor` and `📋 Copy` buttons on assistant responses.

### 📊 3. High-Resolution Diagram & Visual Scanner Engine
- **QuickChart Mermaid SVG Flowcharts**: Renders real dynamic architectural flowcharts (e.g. `iOS/Android App -> API Gateway -> FastAPI -> Vector RAG DB -> S3`).
- **Deep Reference File Scanner**: Scans uploaded `.pdf` and `.docx` reference files for embedded diagrams and images down to `1.5KB`, caching them in `KB_IMAGE_STORE` and mapping them to target document sections.

### 💾 4. Persistence & Multi-Format Exports
- **Global Keyboard Shortcuts & Auto-Save**: `Ctrl + S` / `Cmd + S` saves the full workspace session to local storage with a floating toast notification. `Ctrl + Z` / `Ctrl + Y` for document-wide Undo/Redo.
- **Multi-Format Document Export**: Export completed documents to `.docx` (Microsoft Word), `.pdf` (Print PDF), `.html`, `.txt`, and `.md`.

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite, TipTap Editor, Zustand State Management, Vanilla CSS Glassmorphism |
| **Backend API** | Python 3.11, FastAPI, Pydantic v2, Uvicorn, AsyncIO |
| **AI & RAG Orchestration**| LangGraph, LangChain, Qdrant Vector Store, OpenAI GPT-4o / Claude 3.5 Sonnet / Gemini 1.5 |
| **Diagram Engine** | QuickChart Mermaid.js SVG API, PyPDF, python-docx Image Extractor |

---

## 🚀 Getting Started & Local Installation

### Prerequisites
- **Node.js**: v18+
- **Python**: v3.10+
- **OpenAI API Key** (or Anthropic / Google Gemini key)

---

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment with uv
uv venv
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Mac/Linux:
source .venv/bin/activate

# Install dependencies using uv
uv pip install -r requirements.txt

# Launch FastAPI development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*Backend runs locally at: `http://localhost:8000`*

---

### 2. Frontend Setup

```bash
cd frontend

# Install Node dependencies
npm install

# Launch Vite development server
npm run dev
```
*Frontend runs locally at: `http://localhost:5173`*

---

## 🎹 Global Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| **`Ctrl + S` / `Cmd + S`** | Save current workspace session & prompt history to local storage |
| **`Ctrl + Enter` / `Cmd + Enter`** | Insert manual page break & auto-create new page card below |
| **`Ctrl + Z` / `Cmd + Z`** | Undo last document action |
| **`Ctrl + Y` / `Cmd + Shift + Z`** | Redo last document action |
| **`Backspace`** | Delete empty page card (when cursor is at position 1) |

---

## 📁 Repository Structure

```
gdocs-clone/
├── backend/
│   └── app/
│       ├── agents/
│       │   └── procurement_graph.py   # LangGraph Multi-Agent Document Generation Workflow
│       ├── api/
│       │   ├── routes_generate.py     # RAG document generation & surgical section editing endpoints
│       │   └── routes_knowledge.py    # Knowledge Base PDF/DOCX chunking & image extraction endpoints
│       ├── services/
│       │   ├── tiptap_engine.py       # TipTap JSON node builders & Markdown parser
│       │   ├── document_parser.py     # PDF & DOCX text/diagram extractor
│       │   └── vector_store.py        # Qdrant Vector Store retriever
│       └── main.py                    # FastAPI app entrypoint & CORS middleware
└── frontend/
    └── src/
        ├── components/
        │   ├── editor/
        │   │   ├── SegmentedDocEditor.tsx # Core multi-page TipTap canvas & auto-pagination engine
        │   │   ├── ResizableImageNode.tsx  # React NodeView for image corner dragging & alignment
        │   │   ├── EditorRibbon.tsx       # MS Word-style ribbon toolbar
        │   │   └── EditorStatusBar.tsx    # Live word count, page count, and reading time counter
        │   ├── panel/
        │   │   └── PromptPanel.tsx        # Help Bot AI Copilot chat interface
        │   └── layout/
        │       └── ConfigPanel.tsx        # Document layout, typography, and watermark controls
        ├── state/
        │   └── wizardStore.ts             # Zustand central state management & session storage
        └── index.css                      # Modern glassmorphism CSS design system
```

---

## 🛡️ License

Built with ❤️ for Enterprise Procurement & Document Automation.
