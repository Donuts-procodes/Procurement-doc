from typing import Any, Dict, List, Tuple


class BaseAgent:
    """Base class providing standard agent properties and lifecycle contracts."""

    agent_type: str = "base_agent"
    display_name: str = "Base Agent"
    description: str = "Base agent specification"

    def __init__(self) -> None:
        self._api_key: str = ""
        self._session_id: str = ""
        self._agent_id: str = ""
        self._display_name: str = self.display_name
        self._system_prompt: str = ""
        self._closing_line: str = ""
        self._blocked_words: List[str] = []
        self._llm_provider: str = ""
        self._llm_model: str = ""
        self._llm_api_key: str = ""
        self._rag_collection_ref: str = ""

    def set_agent_id(self, agent_id: str) -> None:
        self._agent_id = agent_id

    def set_display_name(self, name: str) -> None:
        self._display_name = name

    def set_system_prompt(self, prompt: str) -> None:
        self._system_prompt = prompt

    def set_rag_collection(self, ref: str) -> None:
        self._rag_collection_ref = ref

    def create_session(self) -> Tuple[str, str]:
        raise NotImplementedError

    async def process_text_query(self, session_id: str, query: str, *, language: str = "en") -> Dict[str, Any]:
        raise NotImplementedError

