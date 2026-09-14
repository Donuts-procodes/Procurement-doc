from __future__ import annotations

import asyncio
import copy
import logging
import time
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("gdocs.context_bus")


class ContextDiff(BaseModel):
    """Single atomic state mutation from a subagent."""
    source_agent: str
    timestamp: float = Field(default_factory=time.time)
    field_updates: dict[str, Any] = Field(default_factory=dict)
    segment_patches: list[dict[str, Any]] = Field(default_factory=list)


class ContextStateBus:
    """ponytail: Minimal linear context synchronization bus.
    Provides immutable snapshots for parallel reads and ordered write-back
    using a single asyncio.Lock. No external dependencies."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._segment_locks: dict[str, asyncio.Lock] = {}
        self._diffs: list[ContextDiff] = []
        self._revision: int = 0

    def snapshot(self, state_dict: dict[str, Any]) -> dict[str, Any]:
        """Return a deep-frozen copy for parallel subagent reads.
        Subagents receive this snapshot; they never touch the live state."""
        return copy.deepcopy(state_dict)

    async def acquire_segment_lock(self, segment_id: str) -> None:
        if segment_id not in self._segment_locks:
            self._segment_locks[segment_id] = asyncio.Lock()
        await self._segment_locks[segment_id].acquire()

    def release_segment_lock(self, segment_id: str) -> None:
        lock = self._segment_locks.get(segment_id)
        if lock and lock.locked():
            lock.release()

    async def commit_diff(self, diff: ContextDiff) -> int:
        """Atomically append a diff to the revision ledger."""
        async with self._lock:
            self._diffs.append(diff)
            self._revision += 1
            logger.info(
                f"📒 ContextBus: Revision {self._revision} committed by '{diff.source_agent}' "
                f"({len(diff.field_updates)} field updates, {len(diff.segment_patches)} segment patches)"
            )
            return self._revision

    async def reconcile(self, state_dict: dict[str, Any]) -> dict[str, Any]:
        """Apply all pending diffs to state_dict in deterministic commit order.
        Returns the updated state dict. Clears the diff ledger after reconciliation."""
        async with self._lock:
            for diff in self._diffs:
                for key, value in diff.field_updates.items():
                    if isinstance(value, list) and isinstance(state_dict.get(key), list):
                        state_dict[key].extend(value)
                    elif isinstance(value, dict) and isinstance(state_dict.get(key), dict):
                        state_dict[key].update(value)
                    else:
                        state_dict[key] = value

                for patch in diff.segment_patches:
                    seg_id = patch.get("segment_id")
                    if not seg_id:
                        continue
                    existing = next((s for s in state_dict.get("segments", []) if s.get("segment_id") == seg_id), None)
                    if existing:
                        existing.update(patch)
                    else:
                        state_dict.setdefault("segments", []).append(patch)

            applied = len(self._diffs)
            self._diffs.clear()
            logger.info(f"📒 ContextBus: Reconciled {applied} diffs into master state (revision {self._revision})")
            return state_dict

    @property
    def revision(self) -> int:
        return self._revision

    @property
    def pending_diffs(self) -> int:
        return len(self._diffs)


# ponytail: Single global instance, reused across the graph lifecycle
context_bus = ContextStateBus()
