"""Pipeline recovery for App Factory — state tracking, resume, rollback."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


STAGE_ORDER: list[str] = [
    "validate_idea",
    "extract_requirements",
    "design_blueprint",
    "generate_prd",
    "build_schema",
    "build_api_contract",
    "build_tasks",
    "bundle_export",
    "quality_gate",
    "generate_docs",
    "scaffold",
    "package_export",
]

STAGE_INDEX: dict[str, int] = {name: idx for idx, name in enumerate(STAGE_ORDER)}


@dataclass
class StageResult:
    """Result of a single pipeline stage."""
    stage: str
    status: StageStatus
    started_at: str = ""
    completed_at: str = ""
    error_message: str = ""
    artifact_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
            "artifact_refs": self.artifact_refs,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StageResult":
        return cls(
            stage=d["stage"],
            status=StageStatus(d["status"]),
            started_at=d.get("started_at", ""),
            completed_at=d.get("completed_at", ""),
            error_message=d.get("error_message", ""),
            artifact_refs=d.get("artifact_refs", []),
        )


@dataclass
class PipelineState:
    """Full pipeline execution state for an idea."""
    idea_id: str
    stages: dict[str, StageResult]
    started_at: str
    completed_at: str = ""
    overall_status: StageStatus = StageStatus.PENDING

    def to_dict(self) -> dict:
        return {
            "idea_id": self.idea_id,
            "stages": {k: v.to_dict() for k, v in self.stages.items()},
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "overall_status": self.overall_status.value,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PipelineState":
        stages = {k: StageResult.from_dict(v) for k, v in d.get("stages", {}).items()}
        return cls(
            idea_id=d["idea_id"],
            stages=stages,
            started_at=d.get("started_at", ""),
            completed_at=d.get("completed_at", ""),
            overall_status=StageStatus(d.get("overall_status", "pending")),
        )

    def mark_started(self, stage: str):
        if stage in self.stages:
            self.stages[stage].status = StageStatus.RUNNING
            self.stages[stage].started_at = datetime.now(timezone.utc).isoformat()
        if self.overall_status == StageStatus.PENDING:
            self.overall_status = StageStatus.RUNNING

    def mark_completed(self, stage: str, artifact_refs: Optional[list[str]] = None):
        if stage not in self.stages:
            self.stages[stage] = StageResult(stage=stage, status=StageStatus.COMPLETED)
        self.stages[stage].status = StageStatus.COMPLETED
        self.stages[stage].completed_at = datetime.now(timezone.utc).isoformat()
        if artifact_refs:
            self.stages[stage].artifact_refs = artifact_refs

    def mark_failed(self, stage: str, error: str):
        if stage not in self.stages:
            self.stages[stage] = StageResult(stage=stage, status=StageStatus.FAILED)
        self.stages[stage].status = StageStatus.FAILED
        self.stages[stage].error_message = error
        self.stages[stage].completed_at = datetime.now(timezone.utc).isoformat()
        self.overall_status = StageStatus.FAILED

    @property
    def last_completed_stage(self) -> Optional[str]:
        completed = [
            name for name in STAGE_ORDER
            if name in self.stages and self.stages[name].status == StageStatus.COMPLETED
        ]
        return completed[-1] if completed else None

    @property
    def first_failed_stage(self) -> Optional[str]:
        for name in STAGE_ORDER:
            if name in self.stages and self.stages[name].status == StageStatus.FAILED:
                return name
        return None

    @property
    def next_pending_stage(self) -> Optional[str]:
        for name in STAGE_ORDER:
            if name not in self.stages or self.stages[name].status in (StageStatus.PENDING, StageStatus.FAILED):
                return name
        return None

    @property
    def progress_pct(self) -> float:
        completed = sum(
            1 for name in STAGE_ORDER
            if name in self.stages and self.stages[name].status == StageStatus.COMPLETED
        )
        return round((completed / len(STAGE_ORDER)) * 100, 1)

    @property
    def is_complete(self) -> bool:
        return self.overall_status == StageStatus.COMPLETED

    def finish(self):
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.overall_status = StageStatus.COMPLETED


@dataclass
class RecoveryPlan:
    """Plan for resuming a failed pipeline execution."""
    state: PipelineState
    resume_from_stage: str
    failed_stages: list[str]
    can_resume: bool = True

    def to_dict(self) -> dict:
        return {
            "state": self.state.to_dict(),
            "resume_from_stage": self.resume_from_stage,
            "failed_stages": self.failed_stages,
            "can_resume": self.can_resume,
        }


def init_pipeline_state(idea_id: str) -> PipelineState:
    """Create a fresh pipeline state for an idea."""
    stages: dict[str, StageResult] = {}
    for stage in STAGE_ORDER:
        stages[stage] = StageResult(stage=stage, status=StageStatus.PENDING)
    return PipelineState(
        idea_id=idea_id,
        stages=stages,
        started_at=datetime.now(timezone.utc).isoformat(),
    )


def build_recovery_plan(state: PipelineState, force_retry: bool = False) -> RecoveryPlan:
    """Build a recovery plan from a failed pipeline state."""
    if state.overall_status != StageStatus.FAILED and not force_retry:
        return RecoveryPlan(
            state=state,
            resume_from_stage="",
            failed_stages=[],
            can_resume=False,
        )

    failed: list[str] = []
    last_completed_index = -1

    for stage in STAGE_ORDER:
        if stage in state.stages:
            if state.stages[stage].status == StageStatus.FAILED:
                failed.append(stage)
            elif state.stages[stage].status == StageStatus.COMPLETED:
                last_completed_index = STAGE_INDEX[stage]

    # Reset failed stages to pending so they can be retried
    for fstage in failed:
        state.stages[fstage].status = StageStatus.PENDING
        state.stages[fstage].error_message = ""

    resume_stage = STAGE_ORDER[last_completed_index + 1] if last_completed_index + 1 < len(STAGE_ORDER) else STAGE_ORDER[-1]
    state.overall_status = StageStatus.PENDING

    return RecoveryPlan(
        state=state,
        resume_from_stage=resume_stage,
        failed_stages=failed,
        can_resume=True,
    )


def rollback_to_stage(state: PipelineState, target_stage: str) -> PipelineState:
    """Roll back pipeline state to a specific stage, clearing all stages after it."""
    target_idx = STAGE_INDEX.get(target_stage)
    if target_idx is None:
        raise ValueError(f"Unknown stage: {target_stage}")

    for stage in STAGE_ORDER:
        if stage in state.stages and STAGE_INDEX[stage] > target_idx:
            state.stages[stage].status = StageStatus.PENDING
            state.stages[stage].completed_at = ""
            state.stages[stage].artifact_refs = []

    state.overall_status = StageStatus.PENDING
    return state
