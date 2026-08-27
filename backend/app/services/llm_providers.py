from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from app.core.session import SessionConfig
from app.schemas.schemas import LLMProvider


def get_chat_model(session: SessionConfig, temperature: float = 0.4) -> BaseChatModel:
    if session.provider == LLMProvider.OPENAI:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=session.model, api_key=session.api_key, temperature=temperature)

    if session.provider == LLMProvider.GEMINI:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=session.model, google_api_key=session.api_key, temperature=temperature
        )

    if session.provider == LLMProvider.ANTHROPIC:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=session.model, api_key=session.api_key, temperature=temperature)

    raise ValueError(f"Unsupported provider: {session.provider}")
