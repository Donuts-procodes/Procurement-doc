import logging
from typing import Dict, List
import openai

logger = logging.getLogger(__name__)


async def chat_complete(
    provider: str,
    model: str,
    api_key: str,
    messages: List[Dict[str, str]],
    max_tokens: int = 500,
    temperature: float = 0.0,
    session_id: str = "",
    agent_type: str = "procurement_doc",
) -> str:
    """Executes chat completions across supported LLM providers."""
    try:
        client = openai.AsyncOpenAI(api_key=api_key or "sk-dummy")
        response = await client.chat.completions.create(
            model=model or "gpt-4o-mini",
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        logger.error(f"LLM chat completion failed for {provider}/{model}: {exc}")
        raise exc

