# Backward-compatible re-exports from canonical location
# Legacy code importing from app.models.schemas will still resolve correctly
from app.schemas.schemas import (  # noqa: F401
    LLMProvider,
    ProcurementDocType,
    SessionCreateRequest,
    SessionResponse,
    KnowledgeFileSummary,
    KnowledgeUploadResponse,
    GenerateRequest,
    GenerateResponse,
    RegenerateSectionRequest,
    RegenerateSectionResponse,
    PROVIDER_MODELS,
)
