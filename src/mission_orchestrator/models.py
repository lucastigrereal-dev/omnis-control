"""Models for Mission Orchestrator Lite."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_id() -> str:
    return f"run_{uuid.uuid4().hex[:8]}"


RUN_STATUS_PLANNED = "planned"
RUN_STATUS_DRY_RUN = "dry_run"
RUN_STATUS_COMPLETE = "complete"
RUN_STATUS_FAILED = "failed"
RUN_STATUS_BLOCKED = "blocked"


@dataclass
class OrchestratorStep:
    step_id: str
    label: str
    module: str           # e.g. "mission_builder", "asset_inbox", "mission_report"
    command: str          # human-readable command
    status: str = "pending"  # pending | done | skipped | failed
    output: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "step_id": self.step_id,
            "label": self.label,
            "module": self.module,
            "command": self.command,
            "status": self.status,
            "output": self.output,
            "notes": self.notes,
        }


@dataclass
class OrchestratorRun:
    run_id: str
    request_text: str
    account_handle: str
    objective: str
    intent: str
    dry_run: bool
    status: str
    steps: list[OrchestratorStep] = field(default_factory=list)
    mission_id: str | None = None
    sector_id: str | None = None
    squad_id: str | None = None
    graph_run_id: str | None = None
    matched_capabilities: list[str] = field(default_factory=list)
    suggested_gap_ids: list[str] = field(default_factory=list)
    approval_required: bool = False
    approval_id: str | None = None
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    completed_at: str | None = None

    @classmethod
    def new(
        cls,
        request_text: str,
        account_handle: str = "",
        objective: str = "engajamento",
        dry_run: bool = True,
        intent: str = "unknown",
    ) -> "OrchestratorRun":
        return cls(
            run_id=_run_id(),
            request_text=request_text,
            account_handle=account_handle,
            objective=objective,
            intent=intent,
            dry_run=dry_run,
            status=RUN_STATUS_PLANNED,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "request_text": self.request_text,
            "account_handle": self.account_handle,
            "objective": self.objective,
            "intent": self.intent,
            "dry_run": self.dry_run,
            "status": self.status,
            "steps": [s.to_dict() for s in self.steps],
            "mission_id": self.mission_id,
            "sector_id": self.sector_id,
            "squad_id": self.squad_id,
            "graph_run_id": self.graph_run_id,
            "matched_capabilities": self.matched_capabilities,
            "suggested_gap_ids": self.suggested_gap_ids,
            "approval_required": self.approval_required,
            "approval_id": self.approval_id,
            "warnings": self.warnings,
            "blockers": self.blockers,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "OrchestratorRun":
        steps = [
            OrchestratorStep(**s)
            for s in data.pop("steps", [])
        ]
        run = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        run.steps = steps
        return run
