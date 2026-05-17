"""W148 — n8n E2E Pipeline (safety → export → register → schedule → fire)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import AutomationWorkflow, _now_iso, _new_id
from .n8n_bridge import N8nBridge, N8nTriggerResult
from .n8n_registry import N8nWorkflowRegistry, N8nRegistryEntry
from .n8n_scheduler import N8nScheduler, ScheduledExecution
from .n8n_safety_gate import N8nSafetyGate, SafetyCheckResult


@dataclass
class N8nPipelineResult:
    run_id: str
    workflow_id: str
    safety: SafetyCheckResult
    registry_entry: Optional[N8nRegistryEntry]
    schedule: Optional[ScheduledExecution]
    trigger_result: Optional[N8nTriggerResult]
    success: bool
    error: str = ""
    ran_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "safety": self.safety.to_dict(),
            "registry_entry": self.registry_entry.to_dict() if self.registry_entry else None,
            "schedule": self.schedule.to_dict() if self.schedule else None,
            "trigger_result": self.trigger_result.to_dict() if self.trigger_result else None,
            "success": self.success,
            "error": self.error,
            "ran_at": self.ran_at,
        }


class N8nPipeline:
    """Full n8n pipeline: validate → export → register → schedule → fire."""

    def __init__(self) -> None:
        self._gate = N8nSafetyGate()
        self._registry = N8nWorkflowRegistry()
        self._scheduler = N8nScheduler()

    def run(
        self,
        workflow: AutomationWorkflow,
        cron_expr: str = "0 8 * * *",
        tags: Optional[list[str]] = None,
        dry_run: bool = True,
        auto_fire: bool = True,
    ) -> N8nPipelineResult:
        run_id = _new_id("pipe")
        safety = self._gate.check(workflow)
        if not safety.passed:
            return N8nPipelineResult(
                run_id=run_id,
                workflow_id=workflow.workflow_id,
                safety=safety,
                registry_entry=None,
                schedule=None,
                trigger_result=None,
                success=False,
                error=f"Safety gate failed: {safety.errors}",
            )

        entry = self._registry.register(workflow, tags=tags, dry_run=dry_run)
        sched = self._scheduler.schedule(workflow, cron_expr=cron_expr, dry_run=dry_run)

        trigger_result = None
        if auto_fire:
            trigger_result = self._scheduler.fire(sched.schedule_id, workflow)

        return N8nPipelineResult(
            run_id=run_id,
            workflow_id=workflow.workflow_id,
            safety=safety,
            registry_entry=entry,
            schedule=sched,
            trigger_result=trigger_result,
            success=True,
        )
