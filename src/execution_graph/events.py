"""Structured Event Log for Execution Graph runs."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class EventType(str, Enum):
    GRAPH_RUN_STARTED = "graph_run_started"
    GRAPH_RUN_COMPLETED = "graph_run_completed"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    STEP_SKIPPED = "step_skipped"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_RESOLVED = "approval_resolved"
    # Shadow mode events
    SHADOW_RUN_STARTED = "shadow_run_started"
    SHADOW_RUN_COMPLETED = "shadow_run_completed"
    SHADOW_NODE_PROMOTED = "shadow_node_promoted"
    # Replay visibility hooks
    REPLAY_STARTED = "replay_started"
    REPLAY_COMPLETED = "replay_completed"
    RESUME_STARTED = "resume_started"
    RESUME_COMPLETED = "resume_completed"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class GraphEvent:
    """A single typed event from the execution pipeline."""
    event_type: EventType
    graph_run_id: str
    graph_id: str
    step_id: str = ""
    role_id: str = ""
    status: str = ""
    message: str = ""
    timestamp: str = field(default_factory=_now)
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "event_type": self.event_type.value,
            "graph_run_id": self.graph_run_id,
            "graph_id": self.graph_id,
            "step_id": self.step_id,
            "role_id": self.role_id,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> "GraphEvent":
        return cls(
            event_type=EventType(d["event_type"]),
            graph_run_id=d["graph_run_id"],
            graph_id=d.get("graph_id", ""),
            step_id=d.get("step_id", ""),
            role_id=d.get("role_id", ""),
            status=d.get("status", ""),
            message=d.get("message", ""),
            timestamp=d.get("timestamp", ""),
            metadata=d.get("metadata", {}),
        )


class EventLog:
    """In-memory append-only event log for a graph run."""

    def __init__(self) -> None:
        self._events: list[GraphEvent] = []

    def append(self, event: GraphEvent) -> None:
        self._events.append(event)

    def all(self) -> list[GraphEvent]:
        return list(self._events)

    def filter_by_type(self, event_type: EventType) -> list[GraphEvent]:
        return [e for e in self._events if e.event_type == event_type]

    def filter_by_step(self, step_id: str) -> list[GraphEvent]:
        return [e for e in self._events if e.step_id == step_id]

    def filter_by_role(self, role_id: str) -> list[GraphEvent]:
        return [e for e in self._events if e.role_id == role_id]

    def step_ids(self) -> set[str]:
        return {e.step_id for e in self._events if e.step_id}

    def role_ids(self) -> set[str]:
        return {e.role_id for e in self._events if e.role_id}

    def __len__(self) -> int:
        return len(self._events)

    def to_dicts(self) -> list[dict[str, object]]:
        return [e.to_dict() for e in self._events]


def event_log_from_step_run(step_run) -> EventLog:
    """Build an EventLog from a StepRun's logs and metadata."""
    from src.execution_graph.models import StepStatus

    log = EventLog()

    log.append(GraphEvent(
        event_type=EventType.GRAPH_RUN_STARTED,
        graph_run_id=step_run.graph_run_id,
        graph_id=step_run.graph_id,
        message=f"Graph run started: {step_run.request[:80]}",
    ))

    if step_run.approval_required and step_run.approval_id:
        log.append(GraphEvent(
            event_type=EventType.APPROVAL_REQUESTED,
            graph_run_id=step_run.graph_run_id,
            graph_id=step_run.graph_id,
            message=f"Approval required: {step_run.approval_id}",
            metadata={"approval_id": step_run.approval_id},
        ))

    for entry in step_run.logs:
        evt_type = {
            StepStatus.RUNNING.value: EventType.STEP_STARTED,
            StepStatus.DONE.value: EventType.STEP_COMPLETED,
            StepStatus.FAILED.value: EventType.STEP_FAILED,
            StepStatus.SKIPPED.value: EventType.STEP_SKIPPED,
        }.get(entry.status)

        if evt_type:
            log.append(GraphEvent(
                event_type=evt_type,
                graph_run_id=step_run.graph_run_id,
                graph_id=step_run.graph_id,
                step_id=entry.step_id,
                role_id=entry.role_id,
                status=entry.status,
                message=entry.message,
                timestamp=entry.timestamp,
            ))

    log.append(GraphEvent(
        event_type=EventType.GRAPH_RUN_COMPLETED,
        graph_run_id=step_run.graph_run_id,
        graph_id=step_run.graph_id,
        status=step_run.status,
        message=f"Graph run finished with status: {step_run.status}",
    ))

    return log
