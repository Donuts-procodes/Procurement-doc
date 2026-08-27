from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"


PROVIDER_MODELS: dict[LLMProvider, list[str]] = {
    LLMProvider.OPENAI: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
    LLMProvider.GEMINI: ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"],
    LLMProvider.ANTHROPIC: [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
    ],
}


class ProcurementDocType(str, Enum):
    RFP = "RFP"
    RFQ = "RFQ"
    RFI = "RFI"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    VENDOR_CONTRACT = "VENDOR_CONTRACT"
    SOW = "SOW"
    VENDOR_SCORECARD = "VENDOR_SCORECARD"


class SessionCreateRequest(BaseModel):
    provider: LLMProvider
    model: str
    api_key: str = Field(min_length=8)


class SessionResponse(BaseModel):
    session_id: str
    provider: LLMProvider
    model: str


class KnowledgeFileSummary(BaseModel):
    filename: str
    chunk_count: int


class KnowledgeUploadResponse(BaseModel):
    kb_id: str
    files: list[KnowledgeFileSummary]
    total_chunks: int


class GenerateRequest(BaseModel):
    session_id: str
    kb_id: str | None = None
    procurement_doc_type: ProcurementDocType
    num_pages: int = Field(default=5, ge=1, le=40)
    page_layout_size: str = Field(default="A4")
    prompt: str = Field(min_length=3)


class GenerateResponse(BaseModel):
    document_id: str
    lexical_state: dict[str, Any]
    page_titles: list[str]


class RegenerateSectionRequest(BaseModel):
    session_id: str
    document_id: str
    section_id: str
    instruction: str
    kb_id: str | None = None


class RegenerateSectionResponse(BaseModel):
    section_id: str
    lexical_nodes: list[dict[str, Any]]
