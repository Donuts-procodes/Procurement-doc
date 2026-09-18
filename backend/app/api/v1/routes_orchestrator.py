import os
from fastapi import APIRouter, HTTPException, status
from app.agents.conversational_agent import ProcurementAgent
from app.core.kms_decryptor import kms_decrypt
from app.schemas.orchestrator_schemas import ChatInput, ChatTurnRequest, ChatTurnResponse

router = APIRouter(tags=["NestJS Orchestrator Bridge"])

# Global session store for active agent instances
_ACTIVE_AGENTS: dict[str, ProcurementAgent] = {}


@router.post("/session", response_model=ChatTurnResponse, status_code=status.HTTP_200_OK)
async def init_session(req: ChatTurnRequest) -> ChatTurnResponse:
    """
    Initializes agent session with full config sent ONCE by NestJS Orchestrator.
    Handles KMS decryption, system prompt templating, and Milvus collection binding.
    """
    agent = ProcurementAgent()
    agent._api_key = req.api_key
    agent._session_id = req.session_id

    if req.agent_id:
        agent.set_agent_id(req.agent_id)
    if req.display_name:
        agent.set_display_name(req.display_name)
    if req.system_prompt:
        agent.set_system_prompt(
            req.system_prompt
            .replace("{agentName}", req.display_name or "")
            .replace("{companyName}", req.company_name or "")
        )
    agent._closing_line = req.closing_line
    agent._blocked_words = list(req.blocked_words or [])

    if req.mandatory_fields:
        agent.set_mandatory_fields(req.mandatory_fields)

    # Per-session LLM KMS Decryption
    if req.provider and req.model and req.ciphertext_blob:
        decrypted_key = await kms_decrypt(req.ciphertext_blob, os.getenv("AWS_REGION", "us-east-1"))
        agent._llm_provider = req.provider
        agent._llm_model = req.model
        agent._llm_api_key = decrypted_key

    # External Milvus RAG configuration
    if req.milvus_database and req.milvus_collection:
        ref = f"{req.milvus_database}::{req.milvus_collection}"
        agent.set_rag_collection(ref)

    _, greeting = agent.create_session()
    _ACTIVE_AGENTS[req.session_id] = agent

    return ChatTurnResponse(
        session_id=req.session_id,
        agent_type=agent.agent_type,
        response=greeting,
        intent="session_started",
        missing=[],
        document=None,
    )


@router.post("/chat", response_model=ChatTurnResponse, status_code=status.HTTP_200_OK)
async def handle_turn(req: ChatInput) -> ChatTurnResponse:
    """
    Handles single conversational turn. If session is not initialized on this instance,
    returns 409 Conflict so NestJS Orchestrator re-primes via /session.
    """
    agent = _ACTIVE_AGENTS.get(req.session_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="session_not_initialized",
        )

    result = await agent.process_text_query(session_id=(req.chat_id or req.session_id), query=req.text)

    return ChatTurnResponse(
        session_id=req.session_id,
        agent_type=agent.agent_type,
        response=result.get("response", ""),
        intent=result.get("intent", ""),
        missing=result.get("missing", []),
        document=result.get("document"),
        timing=result.get("timing"),
    )

