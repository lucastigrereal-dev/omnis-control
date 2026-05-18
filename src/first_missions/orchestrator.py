"""W185 — Mission Orchestrator: E2E integration of all first_missions modules."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.first_missions.executor import MissionExecutor
from src.first_missions.models import Mission, MissionRegistry, MissionStatus, MissionType
from src.first_missions.result_store import MissionResultStore, StoredResult
from src.first_missions.scheduler import MissionScheduler


@dataclass
class OrchestratorResult:
    missions_executed: int = 0
    successful: int = 0
    failed: int = 0
    results: list[StoredResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    dry_run: bool = True

    @property
    def ok(self) -> bool:
        return self.failed == 0 and len(self.errors) == 0

    def to_dict(self) -> dict:
        return {
            "missions_executed": self.missions_executed,
            "successful": self.successful,
            "failed": self.failed,
            "ok": self.ok,
            "dry_run": self.dry_run,
            "result_ids": [r.result_id for r in self.results],
            "errors": self.errors,
        }

    @classmethod
    def empty(cls, dry_run: bool = True) -> "OrchestratorResult":
        return cls(dry_run=dry_run)


class MissionOrchestrator:
    """Top-level orchestrator: registry → scheduler → executor → result_store.

    This is the single entry-point for the First Real Missions subsystem.
    All operations respect dry_run — no real actions fire without approval.
    """

    def __init__(self, dry_run: bool = True, result_path: Optional[Path] = None) -> None:
        self.dry_run = dry_run
        self.registry = MissionRegistry()
        self.scheduler = MissionScheduler(dry_run=dry_run)
        self.executor = MissionExecutor(dry_run=dry_run)
        self.result_store = MissionResultStore(path=result_path, dry_run=dry_run)

    # -- Submit -----------------------------------------------------------

    def submit(self, mission: Mission, run_at: str = "") -> Mission:
        """Register + schedule a mission. If run_at is empty, schedule now."""
        self.registry.register(mission)
        if run_at:
            self.scheduler.schedule(mission, run_at=run_at)
        else:
            self.scheduler.schedule_now(mission)
        return mission

    def submit_many(self, missions: list[Mission]) -> list[Mission]:
        for m in missions:
            self.submit(m)
        return missions

    # -- Run --------------------------------------------------------------

    def run_pending(self) -> OrchestratorResult:
        """Dispatch ready missions, execute them, store results."""
        missions = self.scheduler.dispatch_ready()
        if not missions:
            return OrchestratorResult.empty(dry_run=self.dry_run)

        exec_results = self.executor.execute_many(missions)
        stored: list[StoredResult] = []
        errors: list[str] = []
        ok_count = 0
        fail_count = 0

        for ex in exec_results:
            mission = self.registry.get(ex.mission_id)
            if mission:
                sr = self.result_store.save_mission(mission, duration_ms=ex.duration_ms)
                stored.append(sr)
            if ex.ok:
                ok_count += 1
            else:
                fail_count += 1
                if ex.error:
                    errors.append(ex.error)

        return OrchestratorResult(
            missions_executed=len(exec_results),
            successful=ok_count,
            failed=fail_count,
            results=stored,
            errors=errors,
            dry_run=self.dry_run,
        )

    def run_one(self, mission: Mission) -> StoredResult:
        """Submit + execute + store a single mission immediately."""
        self.submit(mission)
        self.scheduler.dispatch_ready()
        self.executor.execute(mission)
        return self.result_store.save_mission(mission)

    def preview(self, mission: Mission) -> dict:
        """Return a preview of what would be executed — never changes state."""
        handler_names = {
            "CONTENT_GENERATION": "generate mock caption + hashtags",
            "METRIC_REPORT": "generate mock metric delta",
            "HEALTH_SNAPSHOT": "generate mock health status",
        }
        action = handler_names.get(mission.mission_type.value, "generic mock handler")
        return {
            "mission_id": mission.mission_id,
            "name": mission.name,
            "mission_type": mission.mission_type.value,
            "priority": mission.priority.value,
            "dry_run": True,
            "would_execute": action,
            "would_store": True,
            "note": "This is a preview only — no state will be changed.",
        }

    # -- Status -----------------------------------------------------------

    def status(self) -> dict:
        return {
            "dry_run": self.dry_run,
            "registry": self.registry.stats(),
            "scheduler": self.scheduler.stats(),
            "executor": self.executor.stats(),
            "result_store": self.result_store.stats(),
        }

    def summary(self) -> str:
        s = self.status()
        parts = [
            f"MissionOrchestrator {'(dry-run)' if s['dry_run'] else '(LIVE)'}",
            f"  Registry: {s['registry']['total']} missions",
            f"  Scheduler: {s['scheduler']['pending']} pending, {s['scheduler']['dispatched']} dispatched",
            f"  Executor: {s['executor']['total_executions']} executed ({s['executor']['successful']} ok, {s['executor']['failed']} fail)",
            f"  Results: {s['result_store']['total']} stored",
        ]
        return "\n".join(parts)
