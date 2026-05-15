from src.observability.models import RunStatus, _now_iso


class RunLogger:
    def __init__(self):
        self._runs: dict[str, RunStatus] = {}

    def start_run(self, phase: str) -> RunStatus:
        run = RunStatus(
            phase=phase,
            status="STARTED",
            started_at=_now_iso(),
        )
        self._runs[run.run_id] = run
        return run

    def update(self, run_id: str, status: str, detail: str = "") -> RunStatus:
        run = self._runs.get(run_id)
        if not run:
            run = RunStatus(run_id=run_id, status=status, detail=detail, started_at=_now_iso())
            self._runs[run_id] = run
        run.status = status
        run.detail = detail
        run.updated_at = _now_iso()
        if status in ("COMPLETED", "FAILED", "BLOCKED"):
            run.finished_at = _now_iso()
        return run

    def get_run(self, run_id: str) -> RunStatus | None:
        return self._runs.get(run_id)

    @property
    def active_runs(self) -> list[RunStatus]:
        return [r for r in self._runs.values() if r.finished_at == ""]

    def to_dict(self) -> dict:
        return {
            "runs": [r.to_dict() for r in self._runs.values()],
        }
