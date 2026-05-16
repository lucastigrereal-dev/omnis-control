"""BridgeResult and status mapping for RuntimeBridge."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.execution_graph.models import StepStatus
from src.execution_queue.models import QueueItem, QueueItemStatus, QueueResult

# StepRunLog final status → QueueItemStatus
STATUS_MAP: dict[str, QueueItemStatus] = {
    StepStatus.DONE.value: QueueItemStatus.READY,
    StepStatus.FAILED.value: QueueItemStatus.BLOCKED,
    StepStatus.SKIPPED.value: QueueItemStatus.BLOCKED,
}

# Statuses we skip entirely (not final outcomes)
_SKIP_STATUSES: set[str] = {
    StepStatus.PENDING.value,
    StepStatus.READY.value,
    StepStatus.RUNNING.value,
}


def map_step_status(step_status: str) -> QueueItemStatus:
    """Map a StepStatus value to a QueueItemStatus. Raises BridgeMappingError on unknown status."""
    mapped = STATUS_MAP.get(step_status)
    if mapped is not None:
        return mapped
    if step_status in _SKIP_STATUSES:
        raise ValueError(
            f"Status '{step_status}' is non-final and should have been filtered"
        )
    from src.runtime_bridge.errors import BridgeMappingError
    raise BridgeMappingError(step_id="<unknown>", status=step_status)


@dataclass
class BridgeResult:
    """Result of bridging a StepRun into queue items."""
    graph_run_id: str
    queue_items: list[QueueItem] = field(default_factory=list)
    mapping: dict[str, str] = field(default_factory=dict)  # step_id → item_id
    items_blocked: int = 0
    items_ready: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_run_id": self.graph_run_id,
            "queue_items": [it.to_dict() for it in self.queue_items],
            "mapping": dict(self.mapping),
            "items_blocked": self.items_blocked,
            "items_ready": self.items_ready,
            "errors": list(self.errors),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BridgeResult":
        from src.execution_queue.queue import ExecutionQueue
        items = []
        for raw in d.get("queue_items", []):
            item = QueueItem(
                item_id=raw.get("item_id", ""),
                contract_id=raw.get("contract_id", ""),
                title=raw.get("title", ""),
                risk_level=raw.get("risk_level", "LOW"),
                requires_approval=raw.get("requires_approval", False),
                dry_run_required=raw.get("dry_run_required", True),
                status=QueueItemStatus(raw.get("status", "QUEUED")),
                result=raw.get("result", ""),
                errors=list(raw.get("errors", [])),
                created_at=raw.get("created_at", ""),
            )
            items.append(item)
        return cls(
            graph_run_id=d["graph_run_id"],
            queue_items=items,
            mapping=dict(d.get("mapping", {})),
            items_blocked=d.get("items_blocked", 0),
            items_ready=d.get("items_ready", 0),
            errors=list(d.get("errors", [])),
        )
