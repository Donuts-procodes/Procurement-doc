from __future__ import annotations

import asyncio
import collections
import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("gdocs.subagents")

# ANSI color palette for live terminal visibility
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_CYAN = "\033[96m"
ANSI_GREEN = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_MAGENTA = "\033[95m"
ANSI_BLUE = "\033[94m"
ANSI_RED = "\033[91m"

SUBAGENT_REGISTRY: dict[str, dict[str, str]] = {
    "super_agent": {
        "name": "Lead Super Agent",
        "icon": "👑",
        "role": "Planning & Orchestration",
        "color": ANSI_MAGENTA,
    },
    "deep_research_subagent": {
        "name": "Deep Research Subagent",
        "icon": "🔬",
        "role": "Provenance & Evidence Scraping",
        "color": ANSI_CYAN,
    },
    "sandbox_subagent": {
        "name": "Sandbox REPL Subagent",
        "icon": "🧪",
        "role": "Deterministic Python Calculations",
        "color": ANSI_YELLOW,
    },
    "visual_curation_subagent": {
        "name": "Visual Curation Subagent",
        "icon": "🎨",
        "role": "Diagrams & Media Asset Curation",
        "color": ANSI_BLUE,
    },
    "browser_actuator": {
        "name": "Browser Actuator Subagent",
        "icon": "🌐",
        "role": "Headless Web Browsing & DOM Ingestion",
        "color": ANSI_GREEN,
    },
    "saas_connectors": {
        "name": "SaaS Connector Subagent",
        "icon": "🔌",
        "role": "Enterprise Data Sync & PII Masking",
        "color": ANSI_CYAN,
    },
    "ephemeral_factory": {
        "name": "Ephemeral Agent Factory",
        "icon": "⚡",
        "role": "On-Demand Dynamic Provisioning",
        "color": ANSI_YELLOW,
    },
    "fact_check_agent": {
        "name": "Fact-Check Subagent (AI Judge)",
        "icon": "⚖️",
        "role": "Adversarial Auditing & Citation Tagging",
        "color": ANSI_RED,
    },
    "evaluator": {
        "name": "Execution Evaluator",
        "icon": "📊",
        "role": "Reward Scoring & Tool Trajectory Audit",
        "color": ANSI_MAGENTA,
    },
    "ai_docs_agent": {
        "name": "AI Docs Drafting Subagent",
        "icon": "📝",
        "role": "Rich-Text AST Canvas Synthesis",
        "color": ANSI_CYAN,
    },
    "canvas_checkpoint_agent": {
        "name": "Canvas Checkpoint Agent",
        "icon": "💾",
        "role": "Visual Layout & Versioned Persistence",
        "color": ANSI_GREEN,
    },
}


class SubagentActivityEvent(BaseModel):
    """Immutable event representing a subagent lifecycle action."""
    model_config = ConfigDict(from_attributes=True)

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: float = Field(default_factory=time.time)
    subagent_id: str
    subagent_name: str
    icon: str
    activity_type: str  # START, PROGRESS, TOOL_CALL, COMPLETE, ERROR
    message: str
    session_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float | None = None
    status: str = "RUNNING"  # RUNNING, SUCCESS, WARNING, FAILED


class SubagentTrackerHandle:
    """Handle yielded to subagents during execution to emit intermediate live progress."""

    def __init__(self, logger_hub: SubagentLoggerHub, subagent_id: str, session_id: str | None, start_time: float):
        self._hub = logger_hub
        self.subagent_id = subagent_id
        self.session_id = session_id
        self.start_time = start_time

    def progress(self, message: str, **details: Any) -> None:
        self._hub.emit(
            subagent_id=self.subagent_id,
            activity_type="PROGRESS",
            message=message,
            session_id=self.session_id,
            details=details,
            status="RUNNING",
        )

    def tool_call(self, tool_name: str, input_preview: str, output_preview: str, latency_ms: float | None = None) -> None:
        self._hub.emit(
            subagent_id=self.subagent_id,
            activity_type="TOOL_CALL",
            message=f"Tool '{tool_name}' invoked",
            session_id=self.session_id,
            details={
                "tool_name": tool_name,
                "input": input_preview,
                "output": output_preview,
                "tool_latency_ms": latency_ms,
            },
            status="RUNNING",
        )

    def state_update(self, field_name: str, summary: str) -> None:
        self._hub.emit(
            subagent_id=self.subagent_id,
            activity_type="STATE_UPDATE",
            message=f"State reconciled: {field_name} -> {summary}",
            session_id=self.session_id,
            details={"field": field_name, "summary": summary},
            status="RUNNING",
        )


class SubagentLoggerHub:
    """Centralized high-visibility subagent live activity logger.
    Emits formatted, colorized terminal logs, buffers event history,
    and broadcasts to async streaming subscribers."""

    def __init__(self, max_history: int = 500):
        self._max_history = max_history
        self._history: collections.deque[SubagentActivityEvent] = collections.deque(maxlen=max_history)
        self._active: dict[str, dict[str, Any]] = {}
        self._subscribers: set[asyncio.Queue[SubagentActivityEvent]] = set()
        self._stats: dict[str, dict[str, Any]] = collections.defaultdict(
            lambda: {"total_runs": 0, "total_duration_ms": 0.0, "errors": 0, "last_active": 0.0}
        )

    def _format_terminal(self, event: SubagentActivityEvent, meta: dict[str, str]) -> str:
        color = meta.get("color", "")
        icon = meta.get("icon", "🤖")
        name = meta.get("name", event.subagent_id)
        timestr = time.strftime("%H:%M:%S", time.localtime(event.timestamp))
        ms = int((event.timestamp % 1) * 1000)
        time_formatted = f"{timestr}.{ms:03d}"

        type_badges = {
            "START": f"{ANSI_BOLD}{ANSI_BLUE}[START]{ANSI_RESET}   ",
            "PROGRESS": f"{ANSI_YELLOW}[PROGRESS]{ANSI_RESET}",
            "TOOL_CALL": f"{ANSI_MAGENTA}[TOOL]{ANSI_RESET}    ",
            "STATE_UPDATE": f"{ANSI_CYAN}[STATE]{ANSI_RESET}   ",
            "COMPLETE": f"{ANSI_BOLD}{ANSI_GREEN}[DONE]{ANSI_RESET}    ",
            "ERROR": f"{ANSI_BOLD}{ANSI_RED}[FAIL]{ANSI_RESET}    ",
        }
        badge = type_badges.get(event.activity_type, f"[{event.activity_type}]")

        sess_str = f" {ANSI_DIM}[sess:{event.session_id[:8]}]{ANSI_RESET}" if event.session_id else ""
        dur_str = f" {ANSI_DIM}(took {event.duration_ms:,.0f}ms){ANSI_RESET}" if event.duration_ms is not None else ""

        return (
            f"{ANSI_DIM}{time_formatted}{ANSI_RESET} "
            f"{badge} {icon} {color}{ANSI_BOLD}{name}{ANSI_RESET}{sess_str} | "
            f"{event.message}{dur_str}"
        )

    def emit(
        self,
        subagent_id: str,
        activity_type: str,
        message: str,
        session_id: str | None = None,
        details: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        status: str = "RUNNING",
    ) -> SubagentActivityEvent:
        meta = SUBAGENT_REGISTRY.get(subagent_id, {
            "name": subagent_id.replace("_", " ").title(),
            "icon": "🤖",
            "role": "General Subagent",
            "color": ANSI_CYAN,
        })

        event = SubagentActivityEvent(
            subagent_id=subagent_id,
            subagent_name=meta["name"],
            icon=meta["icon"],
            activity_type=activity_type,
            message=message,
            session_id=session_id,
            details=details or {},
            duration_ms=duration_ms,
            status=status,
        )

        self._history.append(event)

        # Print formatted live log to stdout immediately (unbuffered)
        formatted_line = self._format_terminal(event, meta)
        sys.stdout.write(formatted_line + "\n")
        sys.stdout.flush()

        # Update stats
        st = self._stats[subagent_id]
        st["last_active"] = event.timestamp
        if activity_type == "COMPLETE" and duration_ms:
            st["total_runs"] += 1
            st["total_duration_ms"] += duration_ms
        elif activity_type == "ERROR":
            st["errors"] += 1

        # Push to real-time subscribers
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

        return event

    @asynccontextmanager
    async def track(
        self,
        subagent_id: str,
        initial_action: str,
        session_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AsyncGenerator[SubagentTrackerHandle, None]:
        """Context manager for automatic START -> COMPLETE/ERROR lifecycle logging."""
        start_time = time.perf_counter()
        meta = SUBAGENT_REGISTRY.get(subagent_id, {})
        active_key = f"{subagent_id}:{session_id or 'global'}"

        self._active[active_key] = {
            "subagent_id": subagent_id,
            "session_id": session_id,
            "action": initial_action,
            "start_time": time.time(),
        }

        self.emit(
            subagent_id=subagent_id,
            activity_type="START",
            message=initial_action,
            session_id=session_id,
            details=details,
            status="RUNNING",
        )

        handle = SubagentTrackerHandle(self, subagent_id, session_id, start_time)
        try:
            yield handle
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            self.emit(
                subagent_id=subagent_id,
                activity_type="COMPLETE",
                message=f"Completed {initial_action.lower().rstrip('.')}",
                session_id=session_id,
                duration_ms=duration_ms,
                status="SUCCESS",
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            self.emit(
                subagent_id=subagent_id,
                activity_type="ERROR",
                message=f"Failed during '{initial_action}': {exc}",
                session_id=session_id,
                details={"error": str(exc)},
                duration_ms=duration_ms,
                status="FAILED",
            )
            raise
        finally:
            self._active.pop(active_key, None)

    def get_recent_activities(
        self, limit: int = 100, session_id: str | None = None, subagent_id: str | None = None
    ) -> list[SubagentActivityEvent]:
        events = list(self._history)
        if session_id:
            events = [e for e in events if e.session_id == session_id]
        if subagent_id:
            events = [e for e in events if e.subagent_id == subagent_id]
        return events[-limit:]

    def get_live_summary(self) -> dict[str, Any]:
        """Snapshot of all registered subagents, their current run states, and stats."""
        subagent_statuses = []
        for sid, meta in SUBAGENT_REGISTRY.items():
            is_active = any(k.startswith(sid) for k in self._active)
            current_act = next((v["action"] for k, v in self._active.items() if k.startswith(sid)), None)
            stat = self._stats[sid]
            avg_dur = (
                stat["total_duration_ms"] / stat["total_runs"] if stat["total_runs"] > 0 else 0.0
            )

            subagent_statuses.append({
                "subagent_id": sid,
                "name": meta["name"],
                "icon": meta["icon"],
                "role": meta["role"],
                "status": "RUNNING" if is_active else "IDLE",
                "current_activity": current_act,
                "last_active_timestamp": stat["last_active"] if stat["last_active"] > 0 else None,
                "total_runs": stat["total_runs"],
                "average_duration_ms": round(avg_dur, 2),
                "error_count": stat["errors"],
            })

        return {
            "active_count": len(self._active),
            "subagents": subagent_statuses,
            "recent_events": [e.model_dump() for e in list(self._history)[-25:]],
        }

    async def subscribe(self) -> AsyncGenerator[SubagentActivityEvent, None]:
        """Subscribe to real-time event generator."""
        q: asyncio.Queue[SubagentActivityEvent] = asyncio.Queue(maxsize=100)
        self._subscribers.add(q)
        try:
            while True:
                event = await q.get()
                yield event
        finally:
            self._subscribers.discard(q)

    def clear(self) -> None:
        self._history.clear()
        self._active.clear()


# Global singleton instance
subagent_logger = SubagentLoggerHub()
