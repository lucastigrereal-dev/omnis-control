"""Scheduler — agendamento de BatchRunner sem daemon.

BatchSchedule define quando e como rodar o batch.
SchedulerService.run_due() executa os schedules vencidos e persiste o histórico.
Invocação externa: omnis agent schedule run (via cron, Task Scheduler ou manual).
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.agentic.batch_runner import BatchReport, BatchRunner


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _add_hours(iso: str, hours: float) -> str:
    dt = _parse_iso(iso) + timedelta(hours=hours)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


_ROOT = os.path.normpath(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control")))
SCHEDULES_PATH = os.path.join(_ROOT, "data", "agent_schedules.jsonl")
SCHEDULE_RUNS_PATH = os.path.join(_ROOT, "data", "agent_schedule_runs.jsonl")


# ── models ────────────────────────────────────────────────────────────────────

@dataclass
class BatchSchedule:
    """Configuracao persistida de um batch recorrente."""

    schedule_id: str
    account_filter: str | None
    limit: int
    dry_run: bool
    interval_hours: float
    enabled: bool = True
    last_run_at: str | None = None
    next_run_at: str = field(default_factory=_now_iso)
    created_at: str = field(default_factory=_now_iso)
    run_count: int = 0

    @property
    def is_due(self) -> bool:
        """Indica se o schedule esta habilitado e vencido."""
        if not self.enabled:
            return False
        now = datetime.now(timezone.utc)
        return _parse_iso(self.next_run_at) <= now

    def advance(self) -> None:
        """Move o schedule para a proxima janela de execucao."""
        self.last_run_at = _now_iso()
        self.next_run_at = _add_hours(self.last_run_at, self.interval_hours)
        self.run_count += 1

    def to_dict(self) -> dict[str, object]:
        """Serializa o schedule para JSONL."""
        return asdict(self)

    @classmethod
    def from_dict(cls: type["BatchSchedule"], data: dict[str, object]) -> "BatchSchedule":
        """Reconstrui um schedule persistido."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ScheduleRun:
    """Registro historico de uma execucao disparada por schedule."""

    run_id: str
    schedule_id: str
    account_filter: str | None
    limit: int
    dry_run: bool
    approved: int
    needs_review: int
    failed: int
    total_processed: int
    batch_id: str
    executed_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, object]:
        """Serializa a execucao agendada para JSONL/API."""
        return asdict(self)

    @classmethod
    def from_dict(cls: type["ScheduleRun"], data: dict[str, object]) -> "ScheduleRun":
        """Reconstrui um registro de execucao agendada."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── repositories ──────────────────────────────────────────────────────────────

class ScheduleRepository:
    """Repositorio JSONL de BatchSchedule."""

    def __init__(self, path: str = SCHEDULES_PATH) -> None:
        self.path = path
        Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)

    def list_all(self) -> list[BatchSchedule]:
        """Lista schedules validos, ignorando linhas corrompidas."""
        if not os.path.exists(self.path):
            return []
        schedules = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        schedules.append(BatchSchedule.from_dict(json.loads(line)))
                    except (json.JSONDecodeError, TypeError, KeyError):
                        continue
        return schedules

    def get(self, schedule_id: str) -> BatchSchedule | None:
        """Busca um schedule pelo identificador."""
        for s in self.list_all():
            if s.schedule_id == schedule_id:
                return s
        return None

    def save(self, schedule: BatchSchedule) -> None:
        """Insere ou substitui um schedule no arquivo JSONL."""
        schedules = self.list_all()
        idx = next((i for i, s in enumerate(schedules) if s.schedule_id == schedule.schedule_id), None)
        if idx is not None:
            schedules[idx] = schedule
        else:
            schedules.append(schedule)
        self._rewrite(schedules)

    def remove(self, schedule_id: str) -> bool:
        """Remove um schedule pelo identificador."""
        schedules = self.list_all()
        filtered = [s for s in schedules if s.schedule_id != schedule_id]
        if len(filtered) == len(schedules):
            return False
        self._rewrite(filtered)
        return True

    def _rewrite(self, schedules: list[BatchSchedule]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            for s in schedules:
                f.write(json.dumps(s.to_dict()) + "\n")


class ScheduleRunRepository:
    """Repositorio JSONL do historico de execucoes agendadas."""

    def __init__(self, path: str = SCHEDULE_RUNS_PATH) -> None:
        self.path = path
        Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)

    def save(self, run: ScheduleRun) -> None:
        """Adiciona uma execucao ao historico."""
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(run.to_dict()) + "\n")

    def list_all(self) -> list[ScheduleRun]:
        """Lista execucoes historicas validas."""
        if not os.path.exists(self.path):
            return []
        runs = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        runs.append(ScheduleRun.from_dict(json.loads(line)))
                    except (json.JSONDecodeError, TypeError, KeyError):
                        continue
        return runs

    def for_schedule(self, schedule_id: str) -> list[ScheduleRun]:
        """Lista execucoes historicas de um schedule especifico."""
        return [r for r in self.list_all() if r.schedule_id == schedule_id]


# ── service ───────────────────────────────────────────────────────────────────

class SchedulerService:
    """Gerencia schedules e executa os vencidos."""

    def __init__(
        self,
        schedule_repo: ScheduleRepository | None = None,
        run_repo: ScheduleRunRepository | None = None,
        batch_runner_factory: "BatchRunnerFactory | None" = None,
    ) -> None:
        self._schedules = schedule_repo or ScheduleRepository()
        self._runs = run_repo or ScheduleRunRepository()
        self._factory = batch_runner_factory or _DefaultBatchRunnerFactory()

    def add(
        self,
        interval_hours: float,
        account_filter: str | None = None,
        limit: int = 5,
        dry_run: bool = True,
        run_now: bool = False,
    ) -> BatchSchedule:
        """Cria e persiste um novo schedule de batch."""
        schedule = BatchSchedule(
            schedule_id=uuid.uuid4().hex[:10],
            account_filter=account_filter,
            limit=limit,
            dry_run=dry_run,
            interval_hours=interval_hours,
            next_run_at=_now_iso() if run_now else _add_hours(_now_iso(), interval_hours),
        )
        self._schedules.save(schedule)
        return schedule

    def remove(self, schedule_id: str) -> bool:
        """Remove um schedule existente."""
        return self._schedules.remove(schedule_id)

    def list_schedules(self) -> list[BatchSchedule]:
        """Lista todos os schedules cadastrados."""
        return self._schedules.list_all()

    def run_due(self) -> list[ScheduleRun]:
        """Executa todos os schedules vencidos. Retorna os runs executados."""
        due = [s for s in self._schedules.list_all() if s.is_due]
        executed: list[ScheduleRun] = []
        for schedule in due:
            report = self._execute(schedule)
            schedule_run = self._record(schedule, report)
            schedule.advance()
            self._schedules.save(schedule)
            self._runs.save(schedule_run)
            executed.append(schedule_run)
        return executed

    def history(self, schedule_id: str | None = None) -> list[ScheduleRun]:
        """Retorna historico geral ou filtrado por schedule."""
        if schedule_id:
            return self._runs.for_schedule(schedule_id)
        return self._runs.list_all()

    # ── internals ─────────────────────────────────────────────────────────────

    def _execute(self, schedule: BatchSchedule) -> BatchReport:
        runner = self._factory.make(schedule)
        return runner.run(limit=schedule.limit, account_filter=schedule.account_filter)

    def _record(self, schedule: BatchSchedule, report: BatchReport) -> ScheduleRun:
        return ScheduleRun(
            run_id=uuid.uuid4().hex[:10],
            schedule_id=schedule.schedule_id,
            account_filter=schedule.account_filter,
            limit=schedule.limit,
            dry_run=schedule.dry_run,
            approved=report.approved,
            needs_review=report.needs_review,
            failed=report.failed,
            total_processed=report.total_processed,
            batch_id=report.batch_id,
        )


# ── factory ───────────────────────────────────────────────────────────────────

class BatchRunnerFactory:
    """Contrato minimo para criar BatchRunner a partir de um schedule."""

    def make(self, schedule: BatchSchedule) -> BatchRunner:
        """Cria um BatchRunner configurado para o schedule recebido."""
        ...


class _DefaultBatchRunnerFactory:
    def make(self, schedule: BatchSchedule) -> BatchRunner:
        return BatchRunner(dry_run=schedule.dry_run)
