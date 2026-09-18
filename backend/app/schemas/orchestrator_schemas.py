from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ChatTurnRequest(BaseModel):
    """Wire contract from NestJS Orchestrator on session initialization."""
    model_config = ConfigDict(extra="allow")

    session_id: str = Field(..., description="Unique session ID")
    text: str = Field(default="", description="Initial text payload")
    agent_type: str = Field(default="procurement_doc", description="Agent type routing key")
    api_key: str = Field(default="", description="Merchant API token")

    provider: str = Field(default="", description="LLM provider: openai | anthropic | gemini")
    model: str = Field(default="", description="Model name")
    ciphertext_blob: str = Field(default="", description="AWS KMS ciphertext for LLM API key")

    milvus_database: str = Field(default="default", description="Milvus database name")
    milvus_collection: str = Field(default="procurement_docs", description="Milvus collection name")

    agent_id: str = Field(default="", description="Agent ID")
    display_name: str = Field(default="Procurement Document Agent", description="Agent display name")
    system_prompt: str = Field(default="", description="Custom system prompt override")
    closing_line: str = Field(default="", description="Closing line")
    company_name: str = Field(default="", description="Merchant organization name")
    blocked_words: List[str] = Field(default_factory=list, description="List of blocked keywords")
    mandatory_fields: Optional[Any] = Field(default=None, description="Optional merchant custom fields")


class ChatInput(BaseModel):
    """Input payload for user turns sent on POST /chat."""
    model_config = ConfigDict(extra="allow")

    session_id: str = Field(..., description="Active session ID")
    text: str = Field(..., description="User input text")
    chat_id: str = Field(default="", description="Conversation isolation ID")


class DocumentArtifact(BaseModel):
    """Generated document metadata returned to Orchestrator."""
    model_config = ConfigDict(extra="allow")

    doc_type: str = Field(..., description="rfq | rfp")
    document_id: str = Field(..., description="Document identifier")
    download_url: str = Field(..., description="Download endpoint")
    status: str = Field(default="ready", description="ready | processing | failed")
    fields: Dict[str, str] = Field(default_factory=dict, description="Collected form slots")


class ChatTurnResponse(BaseModel):
    """Response returned to NestJS Orchestrator."""
    model_config = ConfigDict(extra="allow")

    session_id: str
    agent_type: str
    response: str
    intent: str = Field(..., description="session_started | collecting | clarify_type | document_ready")
    missing: List[str] = Field(default_factory=list, description="Missing required field keys")
    document: Optional[DocumentArtifact] = None
    timing: Optional[Dict[str, float]] = None

