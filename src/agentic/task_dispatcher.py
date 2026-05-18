"""TaskDispatcher — roteia deliverables para o executor correto por setor/tipo."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.agentic.deliverable_mapper import DeliverableManifest, DeliverableSpec


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short_id() -> str:
    return uuid.uuid4().hex[:8]


# ── sector → executor mapping ──────────────────────────────────────────

SECTOR_EXECUTOR: dict[str, str] = {
    "marketing": "publisher",
    "sales": "sales",
    "app_factory": "app_factory",
    "computer_ops": "computer_ops",
    "finance": "finance",
    "general": "skill_runner",
}

EXECUTOR_LABELS: dict[str, str] = {
    "publisher": "Publisher Agent",
    "sales": "Sales Agent",
    "app_factory": "App Factory",
    "computer_ops": "Computer Ops",
    "finance": "Finance Agent",
    "skill_runner": "Skill Runner",
    "code_executor": "Code Executor",
    "browser": "Browser Agent",
    "workflow": "Workflow Runner",
    "analytics": "Analytics Agent",
}


# ── models ─────────────────────────────────────────────────────────────

@dataclass
class DispatchEntry:
    task_id: str
    deliverable: str  # filename from DeliverableSpec
    executor: str
    status: str = "pending"  # pending | dispatched | running | done | failed
    dry_run: bool = True
    dispatched_at: Optional[str] = None
    finished_at: Optional[str] = None
    result_hint: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "deliverable": self.deliverable,
            "executor": self.executor,
            "status": self.status,
            "dry_run": self.dry_run,
            "dispatched_at": self.dispatched_at,
            "finished_at": self.finished_at,
            "result_hint": self.result_hint,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DispatchEntry":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class DispatchPlan:
    mission_id: str
    entries: list[DispatchEntry] = field(default_factory=list)
    generated_at: str = field(default_factory=_now_iso)
    dry_run: bool = True
    total: int = 0
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "entries": [e.to_dict() for e in self.entries],
            "generated_at": self.generated_at,
            "dry_run": self.dry_run,
            "total": self.total,
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DispatchPlan":
        entries = [DispatchEntry.from_dict(e) for e in data.pop("entries", [])]
        plan = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        plan.entries = entries
        return plan


# ── dispatcher ─────────────────────────────────────────────────────────

class TaskDispatcher:
    """Roteia deliverables de um manifest para os executores corretos."""

    def __init__(self, dry_run: bool = True, log_dir: Optional[Path] = None) -> None:
        self.dry_run = dry_run
        self.log_dir = log_dir

    def dispatch(self, manifest: DeliverableManifest, mission_id: str) -> DispatchPlan:
        """Cria DispatchPlan com uma entry por deliverable, roteado ao executor."""
        executor = self._resolve_executor(manifest.setor)
        entries: list[DispatchEntry] = []

        for spec in manifest.deliverables:
            entry = DispatchEntry(
                task_id=f"TSK-{_short_id()}",
                deliverable=spec.filename,
                executor=executor,
                status="pending",
                dry_run=self.dry_run,
                dispatched_at=_now_iso() if not self.dry_run else None,
                result_hint=self._simulate_result(spec, executor),
            )
            entries.append(entry)

        plan = DispatchPlan(
            mission_id=mission_id,
            entries=entries,
            dry_run=self.dry_run,
            total=len(entries),
            summary=self._build_summary(manifest.setor, executor, len(entries)),
        )

        if self.log_dir:
            self._write_log(plan)

        return plan

    def _resolve_executor(self, sector: str) -> str:
        return SECTOR_EXECUTOR.get(sector, "skill_runner")

    def _simulate_result(self, spec: DeliverableSpec, executor: str) -> str:
        label = EXECUTOR_LABELS.get(executor, executor)
        if self.dry_run:
            return (
                f"[DRY-RUN] {label} geraria {spec.filename} "
                f"({spec.format}) → {spec.target_subdir}/"
            )
        return f"{label} gerou {spec.filename} → {spec.target_subdir}/"

    def _build_summary(self, sector: str, executor: str, count: int) -> str:
        label = EXECUTOR_LABELS.get(executor, executor)
        mode = "dry-run" if self.dry_run else "live"
        return f"Setor '{sector}' → {label} ({count} tasks, {mode})"

    def _write_log(self, plan: DispatchPlan) -> None:
        assert self.log_dir is not None
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.log_dir / "task_dispatch_log.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            for entry in plan.entries:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
