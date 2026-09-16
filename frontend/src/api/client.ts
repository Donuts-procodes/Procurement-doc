import axios from "axios";
import type {
  DocumentSegment,
  GenerateResponse,
  KnowledgeUploadResponse,
  LLMProvider,
  PreflightBlueprintResponse,
  ProcurementDocType,
  SessionResponse,
} from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "/api/v1";

const client = axios.create({
  baseURL: API_BASE,
});

export async function fetchPreflightBlueprint(params: {
  prompt: string;
  kb_id?: string | null;
  current_template_id?: string;
  current_doc_type?: string;
  session_id?: string;
}): Promise<PreflightBlueprintResponse> {
  const { data } = await client.post<PreflightBlueprintResponse>("/generate/blueprint", params);
  return data;
}

export async function fetchProviderModels(): Promise<Record<LLMProvider, string[]>> {
  const { data } = await client.get<Record<LLMProvider, string[]>>("/session/providers");
  return data;
}

export async function createSession(
  provider: LLMProvider,
  model: string,
  apiKey: string
): Promise<SessionResponse> {
  const { data } = await client.post<SessionResponse>("/session", {
    provider,
    model,
    api_key: apiKey,
  });
  return data;
}

export async function uploadKnowledgeFiles(files: File[], kbId?: string): Promise<KnowledgeUploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const url = kbId ? `/knowledge/upload?kb_id=${encodeURIComponent(kbId)}` : "/knowledge/upload";
  const { data } = await client.post<KnowledgeUploadResponse>(url, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export interface InitialGenerateRequest {
  session_id?: string;
  kb_id?: string;
  procurement_doc_type?: string;
  template_id?: string;
  num_pages?: number;
  page_layout_size?: string;
  prompt?: string;
  content_density?: "min" | "med" | "max";
  provider?: LLMProvider;
  model?: string;
  api_key?: string;
  buyer_name?: string;
  vendor_name?: string;
  budget_estimate?: string;
  delivery_timeline?: string;
  compliance_frameworks?: string[];
  primary_tech?: string;
  sla_target?: string;
}

export async function generateDocument(params: {
  session_id: string;
  kb_id: string | null;
  procurement_doc_type: ProcurementDocType;
  template_id?: string;
  num_pages?: number;
  prompt: string;
  content_density?: "min" | "med" | "max";
  provider?: LLMProvider;
  model?: string;
  api_key?: string;
  buyer_name?: string;
  vendor_name?: string;
  budget_estimate?: string;
  delivery_timeline?: string;
  compliance_frameworks?: string[];
  primary_tech?: string;
  sla_target?: string;
}): Promise<GenerateResponse> {
  const { data } = await client.post<GenerateResponse>("/generate", params);
  return data;
}

export async function answerPendingQuestion(params: {
  session_id: string;
  document_id?: string;
  answer: string;
  content_density?: "min" | "med" | "max";
}): Promise<GenerateResponse> {
  const { data } = await client.post<GenerateResponse>("/generate/answer", params);
  return data;
}

export async function refineSegment(params: {
  session_id: string;
  document_id: string;
  segment_id: string;
  instruction: string;
  content_density?: "min" | "med" | "max";
}): Promise<{ segment: DocumentSegment }> {
  const { data } = await client.post<{ segment: DocumentSegment }>("/generate/refine-segment", params);
  return data;
}

export async function refineSelection(params: {
  session_id: string;
  selection_text: string;
  instruction: string;
  content_density?: "min" | "med" | "max";
}): Promise<{ replacement_text: string }> {
  const { data } = await client.post<{ replacement_text: string }>("/generate/refine-selection", params);
  return data;
}

import type { StreamEvent } from "../types";

export async function streamDocumentGeneration(
  params: {
    session_id?: string;
    prompt: string;
    procurement_doc_type?: string;
    template_id?: string;
    num_pages?: number;
    page_layout_size?: string;
    kb_id?: string;
    buyer_name?: string;
    vendor_name?: string;
    budget_estimate?: string;
    delivery_timeline?: string;
    compliance_frameworks?: string[];
    primary_tech?: string;
    sla_target?: string;
  },
  onEvent: (event: StreamEvent) => void,
  onError?: (err: any) => void,
  onComplete?: () => void
): Promise<void> {
  const url = `${API_BASE}/generate/stream`;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error(`Streaming failed with HTTP status ${res.status}`);
    const reader = res.body?.getReader();
    if (!reader) throw new Error("No readable stream in response");
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const block of lines) {
        for (const line of block.split("\n")) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data:")) {
            try {
              const data = JSON.parse(trimmed.slice(5).trim());
              onEvent(data as StreamEvent);
            } catch (e) {
              console.warn("Error parsing SSE line:", trimmed, e);
            }
          }
        }
      }
    }
    onComplete?.();
  } catch (err) {
    onError?.(err);
  }
}

export async function streamTargetedSelectionEdit(
  params: {
    session_id: string;
    prompt: string;
    target_node_id?: string;
    selection_text: string;
    context_window?: string;
  },
  onEvent: (event: StreamEvent) => void,
  onError?: (err: any) => void,
  onComplete?: () => void
): Promise<void> {
  const url = `${API_BASE}/generate/stream-selection`;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error(`Targeted stream failed: ${res.status}`);
    const reader = res.body?.getReader();
    if (!reader) throw new Error("No readable stream");
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const block of lines) {
        for (const line of block.split("\n")) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data:")) {
            try {
              const data = JSON.parse(trimmed.slice(5).trim());
              onEvent(data as StreamEvent);
            } catch (e) {
              console.warn("Parse error:", trimmed, e);
            }
          }
        }
      }
    }
    onComplete?.();
  } catch (err) {
    onError?.(err);
  }
}

