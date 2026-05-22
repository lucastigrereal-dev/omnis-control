"""Replay engine — deterministic mission replay from event log.

All events are append-only and immutable. Replay reconstructs system state
by re-processing events in sequence order.

Contracts:
    1. Events are idempotent (same input → same output)
    2. Sequence numbers define total order
    3. Timestamps are wall-clock (not processed-at)
    4. State is a pure function of event stream
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from ..events.event_bus import EventBus, get_event_bus
from ..schemas.event_schema import EventEnvelope

logger = logging.getLogger(__name__)


@dataclass
class ReplayState:
    """Mutable state reconstructed during replay."""

    missions: dict[str, dict] = field(default_factory=dict)
    tasks: dict[str, dict] = field(default_factory=dict)
    provider_calls: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    token_total: int = 0
    cost_total: float = 0.0
    event_count: int = 0
    last_sequence: int = 0


class ReplayEngine:
    """Deterministic replay of mission events.

    Reconstructs system state by replaying events from the event log
    in sequence order. Verifies that replay is deterministic.

    Usage:
        engine = ReplayEngine(event_bus)
        state = await engine.replay_mission("mission_123")
        print(f"Replayed {state.event_count} events, ${state.cost_total:.4f}")
    """

    def __init__(self, bus: EventBus | None = None):
        self.bus = bus or get_event_bus()

    async def replay_mission(self, mission_id: str) -> ReplayState:
        """Replay all events for a mission, reconstructing state."""
        state = ReplayState()

        async def handler(event: EventEnvelope) -> None:
            state.event_count += 1
            state.last_sequence = event.sequence
            state.token_total += event.delta_tokens or 0
            state.cost_total += event.delta_cost_usd or 0.0

            if event.event_type.value.startswith("mission_"):
                state.missions[event.mission_id or ""] = event.payload
            elif event.event_type.value.startswith("task_"):
                state.tasks[event.task_id or ""] = event.payload
            elif event.event_type.value.startswith("provider_"):
                state.provider_calls.append(event.payload)

            if event.event_type.value in ("mission_failed", "task_failed", "provider_failed"):
                state.errors.append(
                    {
                        "event_type": event.event_type.value,
                        "timestamp": event.timestamp.isoformat(),
                        "payload": event.payload,
                    }
                )

        count = await self.bus.replay_stream(
            EventBus.STREAMS["missions"], handler, start="0"
        )
        logger.info("Replayed %d events for mission %s", count, mission_id)
        return state

    async def verify_replay(self, mission_id: str) -> dict[str, Any]:
        """Run replay twice and verify determinism."""
        run1 = await self.replay_mission(mission_id)
        run2 = await self.replay_mission(mission_id)

        deterministic = (
            run1.event_count == run2.event_count
            and run1.token_total == run2.token_total
            and run1.cost_total == run2.cost_total
            and run1.last_sequence == run2.last_sequence
        )

        return {
            "mission_id": mission_id,
            "deterministic": deterministic,
            "event_count": run1.event_count,
            "token_total": run1.token_total,
            "cost_total": round(run1.cost_total, 6),
            "errors": run1.errors,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }


class ReplayAuditor:
    """Audit replay integrity — verify event log is complete and consistent."""

    def __init__(self, bus: EventBus | None = None):
        self.bus = bus or get_event_bus()

    async def audit_stream(self, stream: str) -> dict[str, Any]:
        """Audit a stream for gaps, duplicates, and integrity issues."""
        seen_sequences: set[int] = set()
        seen_ids: set[str] = set()
        gaps: list[int] = []
        duplicates: list[str] = []
        count = 0
        last_seq = -1

        async def check(event: EventEnvelope) -> None:
            nonlocal count, last_seq
            count += 1

            if event.sequence in seen_sequences:
                duplicates.append(event.event_id)
            seen_sequences.add(event.sequence)

            if event.event_id in seen_ids:
                duplicates.append(event.event_id)
            seen_ids.add(event.event_id)

            if last_seq >= 0 and event.sequence > last_seq + 1:
                for gap_seq in range(last_seq + 1, event.sequence):
                    gaps.append(gap_seq)
            last_seq = event.sequence

        await self.bus.replay_stream(stream, check, start="0")

        return {
            "stream": stream,
            "total_events": count,
            "gaps": gaps,
            "gap_count": len(gaps),
            "duplicates": duplicates[:100],
            "duplicate_count": len(duplicates),
            "complete": len(gaps) == 0 and len(duplicates) == 0,
        }
