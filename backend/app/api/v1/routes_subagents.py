from __future__ import annotations

import json
from typing import AsyncGenerator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.core.subagent_logger import subagent_logger
from app.schemas.schemas import (
    SubagentActivityEventDTO,
    SubagentLiveSummaryResponse,
    SubagentStatusDTO,
)

router = APIRouter()


@router.get("/live", response_model=SubagentLiveSummaryResponse)
async def get_live_subagents_summary() -> SubagentLiveSummaryResponse:
    """Returns current runtime state of all registered subagents, active workloads, and recent activity."""
    raw = subagent_logger.get_live_summary()
    return SubagentLiveSummaryResponse(
        active_count=raw["active_count"],
        subagents=[SubagentStatusDTO(**s) for s in raw["subagents"]],
        recent_events=[SubagentActivityEventDTO(**e) for e in raw["recent_events"]],
    )


@router.get("/events", response_model=list[SubagentActivityEventDTO])
async def get_recent_subagent_events(
    limit: int = Query(default=50, ge=1, le=200),
    session_id: str | None = Query(default=None),
    subagent_id: str | None = Query(default=None),
) -> list[SubagentActivityEventDTO]:
    """Retrieve historical subagent activity events with optional session or subagent filter."""
    events = subagent_logger.get_recent_activities(
        limit=limit, session_id=session_id, subagent_id=subagent_id
    )
    return [SubagentActivityEventDTO.model_validate(e) for e in events]


@router.get("/stream")
async def stream_subagent_activities(
    session_id: str | None = Query(default=None),
) -> StreamingResponse:
    """Server-Sent Events (SSE) feed streaming live subagent actions as they occur in real time."""

    async def event_generator() -> AsyncGenerator[str, None]:
        # Initial greeting event with current state
        summary = subagent_logger.get_live_summary()
        yield f"event: init\ndata: {json.dumps(summary)}\n\n"

        async for event in subagent_logger.subscribe():
            if session_id and event.session_id and event.session_id != session_id:
                continue
            payload = event.model_dump()
            yield f"event: subagent_activity\ndata: {json.dumps(payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/clear")
async def clear_subagent_activity() -> dict[str, str]:
    """Clears buffered activity history."""
    subagent_logger.clear()
    return {"status": "cleared"}
