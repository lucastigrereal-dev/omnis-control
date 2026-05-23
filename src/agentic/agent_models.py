"""AgentRun + AgentStep — rastreamento de execução de agentes OMNIS."""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_ROOT = os.path.normpath(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control")))
AGENT_RUNS_PATH = os.path.join(_ROOT, "data", "agent_runs.jsonl")


class AgentRunStatus:
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DRY_RUN = "dry_run"


class StepStatus:
    PENDING = "pending"
    OK = "ok"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class AgentStep:
    step_id: str
    run_id: str
    name: str
    status: str = StepStatus.PENDING
    input_summary: str = ""
    output_summary: str = ""
    error: str | None = None
    started_at: str = field(default_factory=_now_iso)
    finished_at: str | None = None

    def complete(self, output_summary: str = "") -> None:
        self.status = StepStatus.OK
        self.output_summary = output_summary
        self.finished_at = _now_iso()

    def skip(self, reason: str = "") -> None:
        self.status = StepStatus.SKIPPED
        self.output_summary = reason
        self.finished_at = _now_iso()

    def fail(self, error: str) -> None:
        self.status = StepStatus.ERROR
        self.error = error
        self.finished_at = _now_iso()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "AgentStep":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AgentRun:
    run_id: str
    agent: str
    account_handle: str
    objective: str
    dry_run: bool = True
    status: str = AgentRunStatus.RUNNING
    steps: list[AgentStep] = field(default_factory=list)
    result: dict[str, object] = field(default_factory=dict)
    error: str | None = None
    started_at: str = field(default_factory=_now_iso)
    finished_at: str | None = None

    # ── lifecycle ───────────────────────────────────────────────────────

    def add_step(self, name: str, input_summary: str = "") -> AgentStep:
        step = AgentStep(
            step_id=uuid.uuid4().hex[:8],
            run_id=self.run_id,
            name=name,
            input_summary=input_summary,
        )
        self.steps.append(step)
        return step

    def complete(self, result: dict[str, object] | None = None) -> None:
        self.status = AgentRunStatus.DRY_RUN if self.dry_run else AgentRunStatus.COMPLETED
        self.result = result or {}
        self.finished_at = _now_iso()

    def fail(self, error: str) -> None:
        self.status = AgentRunStatus.FAILED
        self.error = error
        self.finished_at = _now_iso()

    # ── serialization ───────────────────────────────────────────────────

    def to_dict(self) -> dict[str, object]:
        d = asdict(self)
        d["steps"] = [s.to_dict() for s in self.steps]
        return d

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "AgentRun":
        steps_raw = data.pop("steps", [])
        run = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        run.steps = [AgentStep.from_dict(s) for s in steps_raw]
        return run


class AgentRunRepository:
    """Persiste AgentRuns em JSONL."""

    def __init__(self, path: str = AGENT_RUNS_PATH) -> None:
        self.path = path
        Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)

    def save(self, run: AgentRun) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(run.to_dict()) + "\n")

    def list_all(self) -> list[AgentRun]:
        if not os.path.exists(self.path):
            return []
        runs = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    runs.append(AgentRun.from_dict(json.loads(line)))
        return runs

    def get(self, run_id: str) -> AgentRun | None:
        for run in self.list_all():
            if run.run_id == run_id:
                return run
        return None
