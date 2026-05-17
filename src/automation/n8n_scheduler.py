"""W145 — n8n Execution Scheduler (mock-first, cron-based)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import AutomationWorkflow, _now_iso, _new_id
from .n8n_bridge import N8nBridge, N8nTriggerResult


SCHEDULE_STATUS_PENDING = "pending"
SCHEDULE_STATUS_FIRED = "fired"
SCHEDULE_STATUS_SKIPPED = "skipped"


@dataclass
class ScheduledExecution:
    schedule_id: str
    workflow_id: str
    cron_expr: str
    dry_run: bool = True
    status: str = SCHEDULE_STATUS_PENDING
    fire_count: int = 0
    last_result: Optional[N8nTriggerResult] = None
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "schedule_id": self.schedule_id,
            "workflow_id": self.workflow_id,
            "cron_expr": self.cron_expr,
            "dry_run": self.dry_run,
            "status": self.status,
            "fire_count": self.fire_count,
            "last_result": self.last_result.to_dict() if self.last_result else None,
            "created_at": self.created_at,
        }


class N8nScheduler:
    """Mock scheduler that associates cron expressions with n8n workflows."""

    def __init__(self) -> None:
        self._schedules: dict[str, ScheduledExecution] = {}
        self._bridge = N8nBridge()

    def schedule(self, workflow: AutomationWorkflow, cron_expr: str, dry_run: bool = True) -> ScheduledExecution:
        sched = ScheduledExecution(
            schedule_id=_new_id("sched"),
            workflow_id=workflow.workflow_id,
            cron_expr=cron_expr,
            dry_run=dry_run,
        )
        self._schedules[sched.schedule_id] = sched
        return sched

    def fire(self, schedule_id: str, workflow: AutomationWorkflow) -> N8nTriggerResult:
        sched = self._schedules.get(schedule_id)
        if sched is None:
            raise KeyError(f"Schedule not found: {schedule_id!r}")
        result = self._bridge.trigger_workflow(workflow, dry_run=sched.dry_run)
        sched.status = SCHEDULE_STATUS_FIRED
        sched.fire_count += 1
        sched.last_result = result
        return result

    def skip(self, schedule_id: str) -> None:
        sched = self._schedules.get(schedule_id)
        if sched is None:
            raise KeyError(f"Schedule not found: {schedule_id!r}")
        sched.status = SCHEDULE_STATUS_SKIPPED

    def get(self, schedule_id: str) -> Optional[ScheduledExecution]:
        return self._schedules.get(schedule_id)

    def list_all(self) -> list[ScheduledExecution]:
        return list(self._schedules.values())

    def count(self) -> int:
        return len(self._schedules)
