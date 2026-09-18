import logging
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


class PresignedUploadDto(BaseModel):
    filename: str = Field(..., description="Target file name")
    content_type: str = Field(default="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    agent_id: Optional[str] = None


class TelemetryEventDto(BaseModel):
    session_id: str
    agent_type: str
    event_type: str
    tokens_used: int
    duration_seconds: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NestBackendService:
    """Outbound client connecting Procurement Microservice to NestJS Backend."""

    def __init__(self) -> None:
        self.base_url: str = getattr(settings, "NEST_BACKEND_URL", "https://qa-apitg.bizbyagent.com").rstrip("/")
        self.api_key: Optional[str] = getattr(settings, "NEST_API_KEY", None)
        self.bearer_token: Optional[str] = getattr(settings, "NEST_BEARER_TOKEN", None)

    def _get_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        elif self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def get_agent_knowledge(self, agent_id: str) -> List[Dict[str, Any]]:
        """GET /agents/{agentId}/knowledge: Fetches merchant policies and documents for RAG."""
        url = f"{self.base_url}/agents/{agent_id}/knowledge"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url, headers=self._get_headers())
                if res.status_code == 200:
                    data = res.json()
                    return data.get("items", data) if isinstance(data, dict) else data
                logger.warning(f"Nest GET /agents/{agent_id}/knowledge returned {res.status_code}")
        except Exception as exc:
            logger.error(f"Error fetching knowledge from NestJS: {exc}")
        return []

    async def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """GET /agents/{agentId}/config: Pulls merchant dynamic configuration."""
        url = f"{self.base_url}/agents/{agent_id}/config"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url, headers=self._get_headers())
                if res.status_code == 200:
                    return res.json()
        except Exception as exc:
            logger.error(f"Error fetching agent config from NestJS: {exc}")
        return None

    async def get_presigned_upload_url(self, payload: PresignedUploadDto) -> Optional[Dict[str, Any]]:
        """POST /documents/upload-url: Obtains presigned S3 upload URL for generated documents."""
        url = f"{self.base_url}/documents/upload-url"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=self._get_headers(), json=payload.model_dump())
                if res.status_code in (200, 201):
                    return res.json()
        except Exception as exc:
            logger.error(f"Error requesting presigned upload URL from NestJS: {exc}")
        return None

    async def log_telemetry_event(self, event: TelemetryEventDto) -> bool:
        """POST /agents/events: Sends usage metrics and generation audit logs to NestJS."""
        url = f"{self.base_url}/agents/{event.metadata.get('agent_id', 'default')}/events"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(url, headers=self._get_headers(), json=event.model_dump())
                return res.status_code in (200, 201)
        except Exception as exc:
            logger.warning(f"Failed to push telemetry event to NestJS: {exc}")
            return False


nest_backend_service = NestBackendService()

