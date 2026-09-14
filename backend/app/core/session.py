from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

from app.schemas.schemas import LLMProvider
from app.core.redis_client import get_redis_client

logger = logging.getLogger("gdocs.session")


@dataclass
class ChatMessageEntry:
    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class SessionConfig:
    session_id: str
    provider: LLMProvider
    model: str
    api_key: str
    chat_history: list[ChatMessageEntry] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        self.chat_history.append(ChatMessageEntry(role=role, content=content))
        session_store.save(self)

    def get_formatted_history(self) -> str:
        if not self.chat_history:
            return "No previous chat history."
        return "\n".join([f"{msg.role.upper()}: {msg.content}" for msg in self.chat_history])

    @classmethod
    def from_dict(cls, data: dict) -> SessionConfig:
        from app.core.config import settings
        chat_hist = [ChatMessageEntry(**msg) for msg in data.get("chat_history", [])]
        provider = LLMProvider(data["provider"])
        api_key = data.get("api_key") or ""
        
        # If stored key is empty or a placeholder, fallback to server environment key
        if not api_key or api_key.startswith("sk-test") or api_key.startswith("sk-fallback"):
            if provider == LLMProvider.OPENAI and settings.OPENAI_API_KEY:
                api_key = settings.OPENAI_API_KEY
            elif provider == LLMProvider.GEMINI and settings.GEMINI_API_KEY:
                api_key = settings.GEMINI_API_KEY
            elif provider == LLMProvider.ANTHROPIC and settings.ANTHROPIC_API_KEY:
                api_key = settings.ANTHROPIC_API_KEY

        return cls(
            session_id=data["session_id"],
            provider=provider,
            model=data["model"],
            api_key=api_key,
            chat_history=chat_hist
        )


class SessionStore:
    def __init__(self) -> None:
        self.redis = get_redis_client()

    def get(self, session_id: str) -> SessionConfig:
        data = self.redis.get(f"session:{session_id}")
        if not data:
            raise KeyError(f"Unknown session_id: {session_id}")
        return SessionConfig.from_dict(json.loads(data))
        
    def save(self, session: SessionConfig) -> None:
        data = asdict(session)
        data['provider'] = data['provider'].value
        self.redis.set(f"session:{session.session_id}", json.dumps(data), ex=86400) # 24h expire

    def create(self, provider: LLMProvider, model: str, api_key: str, session_id: str | None = None) -> SessionConfig:
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:8]}"
        session = SessionConfig(
            session_id=session_id,
            provider=provider,
            model=model,
            api_key=api_key,
        )
        self.save(session)
        return session

    def get_graph_state(self, document_id: str) -> Any:
        data = self.redis.get(f"graph_state:{document_id}")
        if not data:
            return None
        from app.agents.procurement_graph import ProcurementState
        try:
            return ProcurementState(**json.loads(data))
        except Exception as e:
            logger.warning(f"Failed to deserialize graph state for {document_id}: {e}")
            return None

    def save_graph_state(self, document_id: str, state: Any) -> None:
        if hasattr(state, "model_dump_json"):
            payload = state.model_dump_json()
        elif hasattr(state, "model_dump"):
            payload = json.dumps(state.model_dump(), default=str)
        else:
            payload = json.dumps(state, default=str)
        self.redis.set(f"graph_state:{document_id}", payload, ex=86400)


session_store = SessionStore()
