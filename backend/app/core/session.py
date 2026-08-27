from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

from app.schemas.schemas import LLMProvider
from app.core.redis_client import get_redis_client


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
        chat_hist = [ChatMessageEntry(**msg) for msg in data.get("chat_history", [])]
        return cls(
            session_id=data["session_id"],
            provider=LLMProvider(data["provider"]),
            model=data["model"],
            api_key=data["api_key"],
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
        return ProcurementState(**json.loads(data))

    def save_graph_state(self, document_id: str, state: Any) -> None:
        self.redis.set(f"graph_state:{document_id}", json.dumps(state.model_dump()), ex=86400)


session_store = SessionStore()
