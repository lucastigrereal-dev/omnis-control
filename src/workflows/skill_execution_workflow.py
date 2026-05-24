"""SkillExecutionWorkflow — Onda 29.

Wraps SkillRunnerBridge.execute_plan() for batch skill dispatch:
  DispatchPlan list → SkillRunnerBridge → ExecutionResult list → Akasha
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field

from src.agentic.skill_runner_bridge import ExecutionResult, SkillRunnerBridge
from src.agentic.task_dispatcher import DispatchEntry, DispatchPlan
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkEvent


def _run_id() -> str:
    return secrets.token_hex(6)


@dataclass
class PlanExecutionResult:
    mission_id: str
    results: list[ExecutionResult]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.status in ("success", "dry_run"))

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == "failed")

    @property
    def needs_review(self) -> int:
        return sum(1 for r in self.results if r.status == "needs_review")


@dataclass
class SkillExecutionResult:
    run_id: str
    success: bool
    plans_count: int
    total_entries: int
    succeeded_entries: int
    failed_entries: int
    review_entries: int
    skills_used: list[str]
    plan_results: list[PlanExecutionResult]
    akasha_event_id: str
    dry_run: bool
    cost_local_pct: int = 100
    error: str | None = None

    @property
    def unique_skills(self) -> int:
        return len(set(self.skills_used))

    @property
    def success_rate(self) -> float:
        if self.total_entries == 0:
            return 0.0
        return round(self.succeeded_entries / self.total_entries, 3)

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "success": self.success,
            "plans_count": self.plans_count,
            "total_entries": self.total_entries,
            "succeeded_entries": self.succeeded_entries,
            "failed_entries": self.failed_entries,
            "review_entries": self.review_entries,
            "unique_skills": self.unique_skills,
            "success_rate": self.success_rate,
            "akasha_event_id": self.akasha_event_id,
            "dry_run": self.dry_run,
            "cost_local_pct": self.cost_local_pct,
            "error": self.error,
        }


class SkillExecutionWorkflow:
    """Executa lotes de DispatchPlan via SkillRunnerBridge."""

    def __init__(self, akasha_sink=None) -> None:
        self._sink = akasha_sink or MockAkashaSink()

    def run(
        self,
        plans: list[DispatchPlan],
        dry_run: bool = True,
    ) -> SkillExecutionResult:
        run_id = _run_id()

        if not plans:
            event = SinkEvent(
                event_type="skill_execution_completed",
                source=run_id,
                payload={"error": "empty_plans", "plans_count": 0},
            )
            self._sink.write_event(event)
            return SkillExecutionResult(
                run_id=run_id,
                success=False,
                plans_count=0,
                total_entries=0,
                succeeded_entries=0,
                failed_entries=0,
                review_entries=0,
                skills_used=[],
                plan_results=[],
                akasha_event_id=event.event_id,
                dry_run=dry_run,
                error="empty_plans",
            )

        bridge = SkillRunnerBridge(dry_run=dry_run)
        plan_results: list[PlanExecutionResult] = []
        all_skills: list[str] = []

        for plan in plans:
            results = bridge.execute_plan(plan)
            plan_results.append(PlanExecutionResult(
                mission_id=plan.mission_id,
                results=results,
            ))
            all_skills.extend(r.skill_id for r in results)

        total = sum(pr.total for pr in plan_results)
        succeeded = sum(pr.succeeded for pr in plan_results)
        failed = sum(pr.failed for pr in plan_results)
        review = sum(pr.needs_review for pr in plan_results)

        event = SinkEvent(
            event_type="skill_execution_completed",
            source=run_id,
            payload={
                "plans_count": len(plans),
                "total_entries": total,
                "succeeded_entries": succeeded,
                "failed_entries": failed,
                "dry_run": dry_run,
            },
        )
        self._sink.write_event(event)

        return SkillExecutionResult(
            run_id=run_id,
            success=True,
            plans_count=len(plans),
            total_entries=total,
            succeeded_entries=succeeded,
            failed_entries=failed,
            review_entries=review,
            skills_used=all_skills,
            plan_results=plan_results,
            akasha_event_id=event.event_id,
            dry_run=dry_run,
        )
