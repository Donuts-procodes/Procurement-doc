import axios from "axios";
import type {
  DocumentSegment,
  GenerateResponse,
  KnowledgeUploadResponse,
  LLMProvider,
  ProcurementDocType,
  SessionResponse,
} from "../types";

const client = axios.create({
  baseURL: "http://localhost:8000/api/v1",
});

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

export async function uploadKnowledgeFiles(files: File[]): Promise<KnowledgeUploadResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const { data } = await client.post<KnowledgeUploadResponse>("/knowledge/upload", formData, {
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
