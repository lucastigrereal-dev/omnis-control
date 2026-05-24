"""TaskDispatchWorkflow — manifests → DispatchPlan lote → akasha.

Onda 27: envolve TaskDispatcher para rotear deliverables de N missões
para os executores corretos, produzindo planos de execução em lote.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from src.agentic.deliverable_mapper import DeliverableManifest
from src.agentic.task_dispatcher import TaskDispatcher, DispatchPlan
from src.akasha_event_sink.adapter import AkashaSinkAdapter
from src.akasha_event_sink.models import SinkEvent
from src.utils.run_context import RunContext

_logger = logging.getLogger("omnis.workflows.task_dispatch")

_COST_LOCAL_PCT = 100


@dataclass
class TaskDispatchResult:
    run_id: str
    success: bool
    missions_count: int
    plans: list[DispatchPlan]
    total_tasks: int
    executors_used: list[str]
    akasha_event_id: str
    dry_run: bool
    cost_local_pct: int = _COST_LOCAL_PCT
    error: str | None = None

    @property
    def unique_executors(self) -> int:
        return len(set(self.executors_used))

    @property
    def avg_tasks_per_mission(self) -> float:
        if self.missions_count == 0:
            return 0.0
        return self.total_tasks / self.missions_count

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "missions_count": self.missions_count,
            "total_tasks": self.total_tasks,
            "unique_executors": self.unique_executors,
            "avg_tasks_per_mission": self.avg_tasks_per_mission,
            "executors_used": self.executors_used,
            "akasha_event_id": self.akasha_event_id,
            "cost_local_pct": self.cost_local_pct,
        }


class TaskDispatchWorkflow:
    """Roteia deliverables de N missões para executores, emite snapshot akasha."""

    def __init__(self, akasha_sink=None) -> None:
        self._sink = akasha_sink or AkashaSinkAdapter()

    def run(
        self,
        missions: list[dict],
        dry_run: bool = True,
    ) -> TaskDispatchResult:
        """Gera DispatchPlan para cada missão do lote.

        Args:
            missions: lista de dicts com keys: mission_id (str),
                      manifest (DeliverableManifest).
            dry_run: se True, planos no modo simulação.

        Returns:
            TaskDispatchResult com todos os planos.
        """
        ctx = RunContext.new(budget_usd=0.0)

        if not missions:
            _logger.warning("task_dispatch[%s]: empty missions list", ctx.run_id)
            return TaskDispatchResult(
                run_id=ctx.run_id,
                success=False,
                missions_count=0,
                plans=[],
                total_tasks=0,
                executors_used=[],
                akasha_event_id="",
                dry_run=dry_run,
                error="empty_missions",
            )

        dispatcher = TaskDispatcher(dry_run=dry_run, log_dir=None)
        plans: list[DispatchPlan] = []
        executors_used: list[str] = []

        for mission in missions:
            mission_id = mission.get("mission_id", "")
            manifest: DeliverableManifest = mission["manifest"]
            plan = dispatcher.dispatch(manifest, mission_id)
            plans.append(plan)
            for entry in plan.entries:
                executors_used.append(entry.executor)
            _logger.debug(
                "task_dispatch[%s]: %s → %d tasks, executor=%s",
                ctx.run_id, mission_id, plan.total,
                plan.entries[0].executor if plan.entries else "none",
            )

        total_tasks = sum(p.total for p in plans)
        unique_execs = len(set(executors_used))
        _logger.info(
            "task_dispatch[%s]: %d missions, %d total tasks, %d executors",
            ctx.run_id, len(missions), total_tasks, unique_execs,
        )

        event = SinkEvent(
            event_type="task_dispatch_plans_generated",
            source=ctx.run_id,
            payload={
                "run_id": ctx.run_id,
                "missions_count": len(missions),
                "total_tasks": total_tasks,
                "unique_executors": unique_execs,
                "dry_run": dry_run,
            },
        )
        self._sink.write_event(event)

        return TaskDispatchResult(
            run_id=ctx.run_id,
            success=True,
            missions_count=len(missions),
            plans=plans,
            total_tasks=total_tasks,
            executors_used=executors_used,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
        )
