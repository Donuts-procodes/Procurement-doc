from __future__ import annotations

import logging
from fastapi import APIRouter

from app.core.session import session_store
from app.schemas.schemas import PROVIDER_MODELS, LLMProvider, SessionCreateRequest, SessionResponse

logger = logging.getLogger("gdocs.routes_session")
router = APIRouter(prefix="/session", tags=["session"])


@router.get("/providers")
def list_providers() -> dict[LLMProvider, list[str]]:
    logger.info("Listing available provider models...")
    return PROVIDER_MODELS


@router.post("", response_model=SessionResponse)
def create_session(payload: SessionCreateRequest) -> SessionResponse:
    logger.info(f"Creating session for provider='{payload.provider.value}', model='{payload.model}'")
    config = session_store.create(provider=payload.provider, model=payload.model, api_key=payload.api_key)
    logger.info(f"Session created successfully: session_id='{config.session_id}'")
    return SessionResponse(session_id=config.session_id, provider=config.provider, model=config.model)
