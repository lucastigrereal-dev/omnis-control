"""W182 — Mission Executor: mock execution engine for First Real Missions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from src.first_missions.models import Mission, MissionStatus, MissionType, _now_iso


ExecutorHandler = Callable[[Mission], dict]


@dataclass
class ExecutionResult:
    mission_id: str
    ok: bool
    result: dict = field(default_factory=dict)
    error: str = ""
    duration_ms: float = 0.0
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "ok": self.ok,
            "result": self.result,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
            "dry_run": self.dry_run,
        }


# ---------------------------------------------------------------------------
# Default mock handlers per mission type
# ---------------------------------------------------------------------------

def _handle_content_generation(mission: Mission) -> dict:
    profile = mission.payload.get("profile", "unknown")
    topic = mission.payload.get("topic", "general")
    return {
        "caption": f"[MOCK] Caption for @{profile} about {topic}",
        "hashtags": ["#travel", "#brasil"],
        "char_count": 120,
    }


def _handle_metric_report(mission: Mission) -> dict:
    metric = mission.payload.get("metric", "followers")
    period = mission.payload.get("period", "daily")
    return {
        "metric": metric,
        "period": period,
        "value": 0,
        "delta": 0,
        "source": "mock",
    }


def _handle_health_snapshot(mission: Mission) -> dict:
    return {
        "status": "HEALTHY",
        "modules": ["core", "kratos_bridge", "remote_control", "production_hardening"],
        "issues": [],
    }


def _handle_generic(mission: Mission) -> dict:
    return {"mission_type": mission.mission_type.value, "executed": True}


_DEFAULT_HANDLERS: dict[MissionType, ExecutorHandler] = {
    MissionType.CONTENT_GENERATION: _handle_content_generation,
    MissionType.METRIC_REPORT: _handle_metric_report,
    MissionType.HEALTH_SNAPSHOT: _handle_health_snapshot,
}


# ---------------------------------------------------------------------------
# MissionExecutor
# ---------------------------------------------------------------------------

class MissionExecutor:
    """Executes missions using registered handlers (mock-first)."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self._handlers: dict[MissionType, ExecutorHandler] = dict(_DEFAULT_HANDLERS)
        self._history: list[ExecutionResult] = []

    def register_handler(self, mission_type: MissionType, handler: ExecutorHandler) -> None:
        self._handlers[mission_type] = handler

    def execute(self, mission: Mission) -> ExecutionResult:
        import time
        start = time.perf_counter()

        if mission.is_terminal:
            return ExecutionResult(
                mission_id=mission.mission_id,
                ok=False,
                error=f"Mission already in terminal state: {mission.status.value}",
                dry_run=self.dry_run,
            )

        mission.status = MissionStatus.RUNNING
        mission.started_at = _now_iso()

        handler = self._handlers.get(mission.mission_type, _handle_generic)

        try:
            if self.dry_run:
                result_data = {"dry_run": True, "simulated": True, "mission_type": mission.mission_type.value}
            else:
                result_data = handler(mission)

            mission.result = result_data
            mission.status = MissionStatus.COMPLETED
            mission.completed_at = _now_iso()
            ok = True
            error = ""
        except Exception as exc:
            mission.status = MissionStatus.FAILED
            mission.error = str(exc)
            mission.completed_at = _now_iso()
            ok = False
            error = str(exc)
            result_data = {}

        duration_ms = (time.perf_counter() - start) * 1000
        res = ExecutionResult(
            mission_id=mission.mission_id,
            ok=ok,
            result=result_data,
            error=error,
            duration_ms=duration_ms,
            dry_run=self.dry_run,
        )
        self._history.append(res)
        return res

    def execute_many(self, missions: list[Mission]) -> list[ExecutionResult]:
        return [self.execute(m) for m in missions]

    def history(self) -> list[ExecutionResult]:
        return list(self._history)

    def stats(self) -> dict:
        total = len(self._history)
        ok_count = sum(1 for r in self._history if r.ok)
        return {
            "total_executions": total,
            "successful": ok_count,
            "failed": total - ok_count,
            "dry_run": self.dry_run,
        }
