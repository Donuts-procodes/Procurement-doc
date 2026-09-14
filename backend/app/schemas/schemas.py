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
    research_findings: list[dict[str, Any]] | None = None
    audit_report: dict[str, Any] | None = None
    sandbox_computations: dict[str, Any] | None = None


class RegenerateSectionRequest(BaseModel):
    session_id: str
    document_id: str
    section_id: str
    instruction: str
    kb_id: str | None = None


class RegenerateSectionResponse(BaseModel):
    section_id: str
    lexical_nodes: list[dict[str, Any]]


class SubagentStatusDTO(BaseModel):
    subagent_id: str
    name: str
    icon: str
    role: str
    status: str
    current_activity: str | None = None
    last_active_timestamp: float | None = None
    total_runs: int = 0
    average_duration_ms: float = 0.0
    error_count: int = 0


class SubagentActivityEventDTO(BaseModel):
    event_id: str
    timestamp: float
    subagent_id: str
    subagent_name: str
    icon: str
    activity_type: str
    message: str
    session_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float | None = None
    status: str = "RUNNING"


class SubagentLiveSummaryResponse(BaseModel):
    active_count: int
    subagents: list[SubagentStatusDTO]
    recent_events: list[SubagentActivityEventDTO]


class ImageSpatialAnchor(BaseModel):
    image_id: str
    url_or_base64: str
    width: int = 0
    height: int = 0
    aspect_ratio: float = 1.0
    preceding_heading: str | None = None
    surrounding_text: str | None = None
    original_page_index: int | None = None


class ImageSemanticProfile(BaseModel):
    image_id: str
    visual_type: str = "general_reference"
    title: str = "Extracted Visual Asset"
    caption: str = "Verified Document Visual Asset"
    extracted_concepts: list[str] = Field(default_factory=list)
    recommended_section: str = "Cover Page"


