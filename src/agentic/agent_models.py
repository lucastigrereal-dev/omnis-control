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
    """Valores validos para o ciclo de vida de um AgentRun."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DRY_RUN = "dry_run"


class StepStatus:
    """Valores validos para o ciclo de vida de um AgentStep."""

    PENDING = "pending"
    OK = "ok"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class AgentStep:
    """Um passo individual executado dentro de um AgentRun."""

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
        """Marca o passo como concluido com sucesso."""
        self.status = StepStatus.OK
        self.output_summary = output_summary
        self.finished_at = _now_iso()

    def skip(self, reason: str = "") -> None:
        """Marca o passo como ignorado com uma justificativa curta."""
        self.status = StepStatus.SKIPPED
        self.output_summary = reason
        self.finished_at = _now_iso()

    def fail(self, error: str) -> None:
        """Marca o passo como falho e preserva a mensagem de erro."""
        self.status = StepStatus.ERROR
        self.error = error
        self.finished_at = _now_iso()

    def to_dict(self) -> dict[str, object]:
        """Serializa o passo para persistencia JSONL."""
        return asdict(self)

    @classmethod
    def from_dict(cls: type["AgentStep"], data: dict[str, object]) -> "AgentStep":
        """Reconstrui um passo a partir de um dicionario persistido."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AgentRun:
    """Execucao rastreavel de um agente OMNIS."""

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
        """Cria e anexa um novo passo ao run."""
        step = AgentStep(
            step_id=uuid.uuid4().hex[:8],
            run_id=self.run_id,
            name=name,
            input_summary=input_summary,
        )
        self.steps.append(step)
        return step

    def complete(self, result: dict[str, object] | None = None) -> None:
        """Finaliza o run como concluido ou dry-run concluido."""
        self.status = AgentRunStatus.DRY_RUN if self.dry_run else AgentRunStatus.COMPLETED
        self.result = result or {}
        self.finished_at = _now_iso()

    def fail(self, error: str) -> None:
        """Finaliza o run como falho."""
        self.status = AgentRunStatus.FAILED
        self.error = error
        self.finished_at = _now_iso()

    # ── serialization ───────────────────────────────────────────────────

    def to_dict(self) -> dict[str, object]:
        """Serializa o run completo, incluindo steps."""
        d = asdict(self)
        d["steps"] = [s.to_dict() for s in self.steps]
        return d

    @classmethod
    def from_dict(cls: type["AgentRun"], data: dict[str, object]) -> "AgentRun":
        """Reconstrui um run a partir de um dicionario persistido."""
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
        """Adiciona um run ao arquivo JSONL."""
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(run.to_dict()) + "\n")

    def list_all(self) -> list[AgentRun]:
        """Carrega todos os runs persistidos."""
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
        """Busca um run pelo identificador."""
        for run in self.list_all():
            if run.run_id == run_id:
                return run
        return None
