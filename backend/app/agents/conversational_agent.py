import json
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

from app.agents.base_agent import BaseAgent
from app.core.llm_router import chat_complete
from app.services.document_generator_service import document_generator_service

logger = logging.getLogger(__name__)

_DEFAULT_FIELDS: List[Dict[str, str]] = [
    {"key": "organization_name",   "label": "Organization name",   "example": ""},
    {"key": "requirement_summary", "label": "Requirement summary", "example": ""},
    {"key": "budget_range",        "label": "Budget range",        "example": "$10k–$20k"},
    {"key": "delivery_timeline",   "label": "Delivery timeline",   "example": "within 8 weeks"},
    {"key": "submission_deadline", "label": "Submission deadline", "example": "2026-08-15"},
    {"key": "contact_person.name", "label": "Contact person name", "example": ""},
]


class ProcurementAgent(BaseAgent):
    """RFQ/RFP form-filling intake agent matching voicelatex-agents procurement-service."""

    agent_type: str = "procurement_doc"
    display_name: str = "Procurement Document Agent"
    description: str = "Creates RFQ / RFP documents from natural-language procurement requirements."

    _GREETING: str = "Hi! I can help you create an RFQ or RFP. Tell me what you need to procure."
    _opening_line_override: str = ""

    def __init__(self) -> None:
        super().__init__()
        self._fields: Optional[Dict[str, List[Dict[str, str]]]] = None
        self._sessions: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _normalize_field(f: Union[str, Dict[str, str]]) -> Dict[str, str]:
        if isinstance(f, str):
            return {"key": f, "label": f.replace("_", " ").replace(".", " ").title(), "example": ""}
        key = f.get("key", "")
        return {
            "key": key,
            "label": f.get("label") or key.replace("_", " ").replace(".", " ").title(),
            "example": f.get("example", ""),
        }

    def set_mandatory_fields(self, fields: Any) -> None:
        norm = lambda lst: [self._normalize_field(f) for f in lst if f]
        if isinstance(fields, dict):
            self._fields = {k: norm(v) for k, v in fields.items() if isinstance(v, list)}
        elif isinstance(fields, list) and fields:
            shared = norm(fields)
            self._fields = {"rfq": shared, "rfp": shared}
        else:
            return
        logger.info(f"Procurement agent mandatory fields updated: {list(self._fields.keys())}")

    def _required(self, doc_type: str) -> List[Dict[str, str]]:
        source = self._fields or {"rfq": _DEFAULT_FIELDS, "rfp": _DEFAULT_FIELDS}
        return source.get(doc_type) or _DEFAULT_FIELDS

    @staticmethod
    def _missing_fields(required: List[Dict[str, str]], collected: Dict[str, str]) -> List[Dict[str, str]]:
        return [f for f in required if not str(collected.get(f["key"], "")).strip()]

    def create_session(self) -> Tuple[str, str]:
        session_id = str(uuid.uuid4())
        greeting = self._opening_line_override or self._GREETING
        self._sessions[session_id] = {
            "history": [{"role": "assistant", "content": greeting}],
            "collected": {},
            "doc_type": None,
            "created_at": time.time(),
        }
        return session_id, greeting

    def end_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    async def _llm_json(self, prompt: str) -> str:
        if self._llm_provider and self._llm_api_key:
            raw_text = await chat_complete(
                provider=self._llm_provider,
                model=self._llm_model,
                api_key=self._llm_api_key,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.0,
                session_id=self._session_id,
                agent_type=self.agent_type,
            )
        else:
            # Fallback mock for unit test environments
            return json.dumps({"doc_type": "rfq", "fields": {}})

        text = raw_text.strip()
        if text.startswith("```"):
            text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0]
        return text

    async def _classify_and_extract(self, query: str, session: Dict[str, Any]) -> Dict[str, Any]:
        all_fields = {f["key"]: f["label"] for dt in ("rfq", "rfp") for f in self._required(dt)}
        field_lines = "\n".join(f"  - {k}: {label}" for k, label in all_fields.items())
        history_text = "".join(
            f"{t['role'].capitalize()}: {t['content']}\n" for t in session.get("history", [])[-6:]
        )
        prompt = (
            "You are extracting structured procurement data from a conversation.\n"
            "Determine whether the user wants an RFQ or an RFP (or leave empty if unclear).\n"
            "Extract any of these fields that the user has provided:\n"
            f"{field_lines}\n\n"
            f"Conversation so far:\n{history_text}\n"
            f"Latest user message: {query}\n\n"
            'Respond ONLY with JSON: {"doc_type": "rfq"|"rfp"|"", "fields": {"<key>": "<value>", ...}}. '
            "Omit fields the user has not provided. Do not invent values."
        )
        try:
            raw = await self._llm_json(prompt)
            data = json.loads(raw)
            dt = str(data.get("doc_type", "")).lower().strip()
            fields = {k: v for k, v in (data.get("fields") or {}).items() if k in all_fields and v}
            return {"doc_type": dt if dt in ("rfq", "rfp") else "", "fields": fields}
        except Exception as e:
            logger.error(f"Procurement extract failed: {e}")
            return {"doc_type": "", "fields": {}}

    @staticmethod
    def _ask_for_missing(doc_type: str, missing: List[Dict[str, str]]) -> str:
        parts: List[str] = []
        for f in missing:
            parts.append(f"{f['label']} (e.g. {f['example']})" if f.get("example") else f["label"])
        needed = "; ".join(parts)
        return f"To finish your {doc_type.upper()} I still need: {needed}. Could you provide these?"

    def _reply(self, session: Dict[str, Any], text: str, **extra: Any) -> Dict[str, Any]:
        session["history"].append({"role": "assistant", "content": text})
        return {"response": text, "type": "response", **extra}

    async def process_text_query(self, session_id: str, query: str, *, language: str = "en") -> Dict[str, Any]:
        t0 = time.time()
        session = self._sessions.setdefault(
            session_id, {"history": [], "collected": {}, "doc_type": None}
        )
        session["history"].append({"role": "user", "content": query})

        extracted = await self._classify_and_extract(query, session)
        if extracted["doc_type"]:
            session["doc_type"] = extracted["doc_type"]
        session["collected"].update(extracted["fields"])

        doc_type = session["doc_type"]
        if not doc_type:
            return self._reply(session, "Are you looking to create an RFQ or an RFP?", intent="clarify_type")

        required = self._required(doc_type)
        missing = self._missing_fields(required, session["collected"])
        if missing:
            return self._reply(
                session, self._ask_for_missing(doc_type, missing),
                intent="collecting", missing=[m["key"] for m in missing],
            )

        # Real generator execution via LangGraph pipeline
        doc_artifact = await document_generator_service.trigger_generation(
            doc_type=doc_type,
            collected_fields=session["collected"],
            session_id=session_id,
        )
        elapsed = time.time() - t0
        logger.info(f"[{session_id[:8]}] Procurement {doc_type} complete in {elapsed:.2f}s")
        msg = f"Your {doc_type.upper()} is ready: {doc_artifact.download_url}"
        return self._reply(
            session,
            msg,
            intent="document_ready",
            document=doc_artifact.model_dump(),
            timing={"total": elapsed},
        )

