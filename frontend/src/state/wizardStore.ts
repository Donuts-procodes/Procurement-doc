import { create } from "zustand";
import type {
  ChatMessage,
  DocumentSegment,
  DocumentStyleConfig,
  KnowledgeFileSummary,
  LLMProvider,
  PageLayoutSize,
  ProcurementDocType,
  SavedSession,
  WizardStep,
} from "../types";
export type { PageLayoutSize };
function getSavedSessionsFromStorage(): SavedSession[] {
  try {
    const raw = localStorage.getItem("gdocs_saved_sessions");
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveSessionsToStorage(sessions: SavedSession[]) {
  try {
    localStorage.setItem("gdocs_saved_sessions", JSON.stringify(sessions));
  } catch (e) {
    console.error("Failed to save sessions to localStorage:", e);
  }
}

function getNextSessionIdNumber(sessions: SavedSession[]): number {
  if (!sessions || sessions.length === 0) return 101;
  const max = Math.max(...sessions.map((s) => s.idNumber || 100));
  return max + 1;
}

function getSavedApiKey(): { provider: LLMProvider; model: string; key: string } | null {
  try {
    const raw = localStorage.getItem("gdocs_ai_config");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

interface WizardState {
  step: WizardStep;
  provider: LLMProvider | null;
  model: string | null;
  sessionId: string | null;
  kbId: string | null;
  kbFiles: KnowledgeFileSummary[];
  procurementDocType: ProcurementDocType;
  templateId: string;
  numPages: number;
  prompt: string;
  contentDensity: "min" | "med" | "max";
  documentId: string | null;
  segments: DocumentSegment[];
  selectedSegmentId: string | null;
  promptLog: ChatMessage[];
  pendingQuestion: string | null;
  styleConfig: DocumentStyleConfig;
  pageLayoutSize: PageLayoutSize;
  historyStack: DocumentSegment[][];
  futureStack: DocumentSegment[][];
  lexicalState: Record<string, unknown> | null;
  pageTitles: string[];
  error: string | null;

  activeEditor: any | null;
  zoomLevel: number;
  layoutMode: "focus" | "print" | "web";

  savedSessions: SavedSession[];
  savedApiKeyConfig: { provider: LLMProvider; model: string; key: string } | null;

  isDarkMode: boolean;
  toggleDarkMode: () => void;

  setStep: (step: WizardStep) => void;
  setSession: (provider: LLMProvider, model: string, sessionId: string) => void;
  setKnowledgeBase: (kbId: string, files: KnowledgeFileSummary[]) => void;
  setTemplateConfig: (procurementDocType: ProcurementDocType, numPages: number, prompt: string, contentDensity: "min" | "med" | "max") => void;
  setGeneratedDocument: (
    documentId: string,
    lexicalState: Record<string, unknown>,
    pageTitles: string[],
    segments?: DocumentSegment[],
    styleConfig?: DocumentStyleConfig,
    pageLayoutSize?: PageLayoutSize
  ) => void;
  setPendingQuestion: (documentId: string, question: string) => void;
  setSelectedSegmentId: (id: string | null) => void;
  addChatMessage: (msg: ChatMessage) => void;
  setStyleConfig: (config: Partial<DocumentStyleConfig>) => void;
  setPageLayoutSize: (size: PageLayoutSize) => void;
  updateSegment: (updatedSegment: DocumentSegment) => void;
  undo: () => void;
  redo: () => void;
  setError: (error: string | null) => void;
  setActiveEditor: (editor: any | null) => void;
  setZoomLevel: (zoomLevel: number | ((z: number) => number)) => void;
  setLayoutMode: (mode: "focus" | "print" | "web") => void;
  addPage: (title?: string) => void;
  moveSegment: (segmentId: string, direction: "up" | "down") => void;
  deleteSegment: (segmentId: string) => void;

  setApiKeyConfig: (provider: LLMProvider, model: string, key: string) => void;
  saveCurrentSession: (customTitle?: string) => void;
  loadSession: (sessionId: string) => void;
  deleteSavedSession: (sessionId: string) => void;
  startNewSession: () => void;
}

const initialApiKeyConfig = getSavedApiKey();
const initialSavedSessions = getSavedSessionsFromStorage();

export const useWizardStore = create<WizardState>((set, get) => ({
  step: initialApiKeyConfig ? (initialSavedSessions.length > 0 ? "editor" : "template-config") : "api-key",
  provider: initialApiKeyConfig?.provider || null,
  model: initialApiKeyConfig?.model || null,
  sessionId: initialSavedSessions.length > 0 ? initialSavedSessions[0].sessionId : null,
  kbId: initialSavedSessions.length > 0 ? initialSavedSessions[0].kbId : null,
  kbFiles: initialSavedSessions.length > 0 ? initialSavedSessions[0].kbFiles : [],
  procurementDocType: initialSavedSessions.length > 0 ? initialSavedSessions[0].procurementDocType : "RFP",
  templateId: "rfp_enterprise",
  numPages: 5,
  prompt: initialSavedSessions.length > 0 ? initialSavedSessions[0].prompt : "",
  contentDensity: "med",
  documentId: initialSavedSessions.length > 0 ? initialSavedSessions[0].documentId : null,
  segments: initialSavedSessions.length > 0 ? initialSavedSessions[0].segments : [],
  selectedSegmentId: null,
  promptLog: initialSavedSessions.length > 0 ? initialSavedSessions[0].promptLog : [],
  pendingQuestion: null,
  styleConfig: initialSavedSessions.length > 0 && initialSavedSessions[0].styleConfig ? initialSavedSessions[0].styleConfig : {
    fontFamily: "Inter, sans-serif",
    fontSize: "15px",
    accentColor: "#1a73e8",
    theme: "Office",
    formatStyle: "modern",
    colorPalette: "Office Blue",
    fontPairing: "Inter / Roboto",
    paragraphSpacing: "1.4",
    watermark: "",
    pageColor: "#ffffff",
    pageBorder: "none",
  },
  pageLayoutSize: initialSavedSessions.length > 0 && initialSavedSessions[0].pageLayoutSize ? initialSavedSessions[0].pageLayoutSize : "A4",
  historyStack: [],
  futureStack: [],
  lexicalState: null,
  pageTitles: [],
  error: null,
  activeEditor: null,
  zoomLevel: 100,
  layoutMode: "print",

  savedSessions: initialSavedSessions,
  savedApiKeyConfig: initialApiKeyConfig,

  isDarkMode: localStorage.getItem("gdocs_dark_mode") === "true",
  toggleDarkMode: () =>
    set((state) => {
      const nextMode = !state.isDarkMode;
      try {
        localStorage.setItem("gdocs_dark_mode", String(nextMode));
      } catch (e) {
        console.error("Failed to save dark mode setting:", e);
      }
      return { isDarkMode: nextMode };
    }),

  setApiKeyConfig: (provider, model, key) => {
    const config = { provider, model, key };
    try {
      localStorage.setItem("gdocs_ai_config", JSON.stringify(config));
    } catch (e) {
      console.error("Failed to save AI config to localStorage:", e);
    }
    set({ savedApiKeyConfig: config, provider, model, step: "knowledge-base", error: null });
  },

  setStep: (step) => set({ step }),
  setSession: (provider, model, sessionId) =>
    set({ provider, model, sessionId, step: "knowledge-base", error: null }),
  setKnowledgeBase: (kbId, files) => set({ kbId, kbFiles: files, step: "template-config", error: null }),
  setTemplateConfig: (procurementDocType, numPages, prompt, contentDensity) =>
    set({ procurementDocType, numPages, prompt, contentDensity, step: "generating", error: null }),
  setGeneratedDocument: (documentId, lexicalState, pageTitles, segments = [], styleConfig, pageLayoutSize) => {
    set((state) => {
      const nextStyleConfig = styleConfig ? { ...state.styleConfig, ...styleConfig } : state.styleConfig;
      const nextLayoutSize = pageLayoutSize || state.pageLayoutSize;
      const nextState = {
        documentId,
        lexicalState,
        pageTitles,
        segments,
        styleConfig: nextStyleConfig,
        pageLayoutSize: nextLayoutSize,
        historyStack: state.segments.length ? [...state.historyStack, state.segments] : state.historyStack,
        futureStack: [],
        step: "editor" as WizardStep,
        error: null,
        pendingQuestion: null,
      };
      setTimeout(() => get().saveCurrentSession(), 100);
      return nextState;
    });
  },
  setPendingQuestion: (documentId, question) =>
    set((state) => ({
      documentId,
      pendingQuestion: question,
      step: "editor",
      promptLog: [
        ...state.promptLog,
        {
          id: String(Date.now()),
          sender: "assistant",
          text: question,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ],
    })),
  setSelectedSegmentId: (selectedSegmentId) => set({ selectedSegmentId }),
  addChatMessage: (msg) => {
    set((state) => {
      if (state.promptLog.some((m) => m.id === msg.id)) {
        return state;
      }
      return { promptLog: [...state.promptLog, msg] };
    });
    setTimeout(() => get().saveCurrentSession(), 100);
  },
  setStyleConfig: (config) => {
    set((state) => ({ styleConfig: { ...state.styleConfig, ...config } }));
    setTimeout(() => get().saveCurrentSession(), 100);
  },
  setPageLayoutSize: (pageLayoutSize) => {
    set({ pageLayoutSize });
    setTimeout(() => get().saveCurrentSession(), 100);
  },
  updateSegment: (updatedSegment) => {
    set((state) => {
      const prevSegments = state.segments;
      const nextSegments = state.segments.map((s) => (s.segment_id === updatedSegment.segment_id ? updatedSegment : s));
      return {
        segments: nextSegments,
        historyStack: [...state.historyStack, prevSegments],
        futureStack: [],
      };
    });
    setTimeout(() => get().saveCurrentSession(), 100);
  },
  undo: () =>
    set((state) => {
      if (state.historyStack.length === 0) return state;
      const previous = state.historyStack[state.historyStack.length - 1];
      const newHistory = state.historyStack.slice(0, state.historyStack.length - 1);
      return {
        segments: previous,
        historyStack: newHistory,
        futureStack: [state.segments, ...state.futureStack],
      };
    }),
  redo: () =>
    set((state) => {
      if (state.futureStack.length === 0) return state;
      const next = state.futureStack[0];
      const newFuture = state.futureStack.slice(1);
      return {
        segments: next,
        historyStack: [...state.historyStack, state.segments],
        futureStack: newFuture,
      };
    }),
  setError: (error) => set({ error }),
  setActiveEditor: (activeEditor) => set({ activeEditor }),
  setZoomLevel: (zoomLevel) =>
    set((state) => ({
      zoomLevel: typeof zoomLevel === "function" ? zoomLevel(state.zoomLevel) : zoomLevel,
    })),
  setLayoutMode: (layoutMode) => set({ layoutMode }),

  addPage: (title) =>
    set((state) => {
      const pageNum = state.segments.length + 1;
      const pageTitle = title || `Page ${pageNum}`;
      const newSeg: DocumentSegment = {
        segment_id: `seg_page_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
        name: pageTitle,
        segment_type: "text",
        content: {
          type: "doc",
          content: [
            {
              type: "heading",
              attrs: { level: 2 },
              content: [{ type: "text", text: pageTitle }],
            },
            {
              type: "paragraph",
              content: [{ type: "text", text: "" }],
            },
          ],
        },
      };
      return {
        segments: [...state.segments, newSeg],
        selectedSegmentId: newSeg.segment_id,
        historyStack: [...state.historyStack, state.segments],
        futureStack: [],
      };
    }),

  moveSegment: (segmentId, direction) =>
    set((state) => {
      const idx = state.segments.findIndex((s) => s.segment_id === segmentId);
      if (idx === -1) return state;
      const targetIdx = direction === "up" ? idx - 1 : idx + 1;
      if (targetIdx < 0 || targetIdx >= state.segments.length) return state;

      const newSegs = [...state.segments];
      const [moved] = newSegs.splice(idx, 1);
      newSegs.splice(targetIdx, 0, moved);

      return {
        segments: newSegs,
        historyStack: [...state.historyStack, state.segments],
        futureStack: [],
      };
    }),

  deleteSegment: (segmentId) =>
    set((state) => {
      const nextSegs = state.segments.filter((s) => s.segment_id !== segmentId);
      return {
        segments: nextSegs,
        selectedSegmentId: state.selectedSegmentId === segmentId ? null : state.selectedSegmentId,
        historyStack: [...state.historyStack, state.segments],
        futureStack: [],
      };
    }),

  saveCurrentSession: (customTitle) =>
    set((state) => {
      if (!state.sessionId && !state.segments.length) return state;

      const existingSessions = getSavedSessionsFromStorage();
      const currentSessionId = state.sessionId || `session_${Date.now()}`;
      const existingIdx = existingSessions.findIndex((s) => s.sessionId === currentSessionId);

      let idNum = 101;
      if (existingIdx !== -1) {
        idNum = existingSessions[existingIdx].idNumber || 101;
      } else {
        idNum = getNextSessionIdNumber(existingSessions);
      }

      const displayId = `#${idNum}`;
      const title =
        customTitle ||
        (state.prompt ? state.prompt.slice(0, 40) : "") ||
        (state.segments.length > 0 ? state.segments[0].name : `Document ${displayId}`);

      const savedDoc: SavedSession = {
        _id: `session_${idNum}`,
        idNumber: idNum,
        displayId,
        sessionId: currentSessionId,
        documentId: state.documentId || `doc_${idNum}`,
        title,
        createdAt: existingIdx !== -1 ? existingSessions[existingIdx].createdAt : new Date().toLocaleString(),
        updatedAt: new Date().toLocaleString(),
        provider: state.provider,
        model: state.model,
        kbId: state.kbId,
        kbFiles: state.kbFiles,
        procurementDocType: state.procurementDocType,
        prompt: state.prompt,
        segments: state.segments,
        promptLog: state.promptLog,
        styleConfig: state.styleConfig,
        pageLayoutSize: state.pageLayoutSize,
        docStatus: "DRAFT",
      };

      let newSessions: SavedSession[];
      if (existingIdx !== -1) {
        newSessions = [...existingSessions];
        newSessions[existingIdx] = savedDoc;
      } else {
        newSessions = [savedDoc, ...existingSessions];
      }

      saveSessionsToStorage(newSessions);
      return { savedSessions: newSessions, sessionId: currentSessionId, documentId: savedDoc.documentId };
    }),

  loadSession: (sessionId) =>
    set((state) => {
      const existingSessions = getSavedSessionsFromStorage();
      const target = existingSessions.find((s) => s.sessionId === sessionId || s._id === sessionId || s.displayId === sessionId);
      if (!target) return state;

      return {
        sessionId: target.sessionId,
        documentId: target.documentId,
        provider: target.provider || state.provider,
        model: target.model || state.model,
        kbId: target.kbId,
        kbFiles: target.kbFiles || [],
        procurementDocType: target.procurementDocType || "RFP",
        prompt: target.prompt || "",
        segments: target.segments || [],
        promptLog: target.promptLog || [],
        styleConfig: target.styleConfig || state.styleConfig,
        pageLayoutSize: target.pageLayoutSize || state.pageLayoutSize,
        step: "editor",
        selectedSegmentId: target.segments.length ? target.segments[0].segment_id : null,
      };
    }),

  deleteSavedSession: (sessionId) =>
    set(() => {
      const existing = getSavedSessionsFromStorage();
      const next = existing.filter((s) => s.sessionId !== sessionId && s._id !== sessionId && s.displayId !== sessionId);
      saveSessionsToStorage(next);
      return { savedSessions: next };
    }),

  startNewSession: () => {
    const newSessionId = `session_${Date.now()}`;
    set({
      sessionId: newSessionId,
      documentId: null,
      kbId: null,
      kbFiles: [],
      procurementDocType: "RFP",
      numPages: 5,
      prompt: "",
      segments: [],
      selectedSegmentId: null,
      promptLog: [],
      pendingQuestion: null,
      error: null,
      historyStack: [],
      futureStack: [],
      step: "knowledge-base",
    });
  },
}));
