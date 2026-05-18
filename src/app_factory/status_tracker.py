"""Status tracker for App Factory — per-idea pipeline progress, summaries, reports."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.app_factory.recovery import (
    PipelineState,
    StageStatus,
    init_pipeline_state,
    STAGE_ORDER,
)


@dataclass(frozen=True)
class IdeaStatus:
    """Lightweight status snapshot for an idea in the pipeline."""
    idea_id: str
    title: str
    overall_status: str  # "pending" | "running" | "completed" | "failed"
    progress_pct: float
    current_stage: str
    failed_stage: Optional[str] = None
    error_message: str = ""
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "idea_id": self.idea_id,
            "title": self.title,
            "overall_status": self.overall_status,
            "progress_pct": self.progress_pct,
            "current_stage": self.current_stage,
            "failed_stage": self.failed_stage,
            "error_message": self.error_message,
            "duration_seconds": self.duration_seconds,
        }


@dataclass(frozen=True)
class PipelineSummary:
    """Aggregate summary of all ideas in the pipeline."""
    total: int
    pending: int
    running: int
    completed: int
    failed: int
    avg_progress_pct: float
    generated_at: str

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "pending": self.pending,
            "running": self.running,
            "completed": self.completed,
            "failed": self.failed,
            "avg_progress_pct": self.avg_progress_pct,
            "generated_at": self.generated_at,
        }

    @property
    def healthy(self) -> bool:
        return self.failed == 0

    @property
    def all_complete(self) -> bool:
        return self.completed == self.total and self.total > 0


class StatusTracker:
    """Tracks pipeline status for multiple ideas."""

    def __init__(self):
        self._states: dict[str, PipelineState] = {}
        self._titles: dict[str, str] = {}

    def register_idea(self, idea_id: str, title: str) -> PipelineState:
        """Register an idea and start tracking its pipeline state."""
        if idea_id not in self._states:
            self._states[idea_id] = init_pipeline_state(idea_id)
            self._titles[idea_id] = title
        return self._states[idea_id]

    def get_state(self, idea_id: str) -> Optional[PipelineState]:
        return self._states.get(idea_id)

    def get_status(self, idea_id: str) -> Optional[IdeaStatus]:
        """Get a lightweight status snapshot for an idea."""
        state = self._states.get(idea_id)
        if state is None:
            return None

        return IdeaStatus(
            idea_id=idea_id,
            title=self._titles.get(idea_id, ""),
            overall_status=state.overall_status.value,
            progress_pct=state.progress_pct,
            current_stage=state.next_pending_stage or "complete",
            failed_stage=state.first_failed_stage,
            error_message=(
                state.stages[state.first_failed_stage].error_message
                if state.first_failed_stage and state.first_failed_stage in state.stages
                else ""
            ),
        )

    def list_all(self) -> list[IdeaStatus]:
        """List status for all tracked ideas."""
        return [s for s in (self.get_status(iid) for iid in self._states) if s is not None]

    def list_by_status(self, status: str) -> list[IdeaStatus]:
        """Filter ideas by overall status."""
        return [s for s in self.list_all() if s.overall_status == status]

    def summary(self) -> PipelineSummary:
        """Generate aggregate summary of all tracked ideas."""
        all_statuses = self.list_all()
        total = len(all_statuses)
        if total == 0:
            return PipelineSummary(
                total=0, pending=0, running=0, completed=0, failed=0,
                avg_progress_pct=0.0,
                generated_at=datetime.now(timezone.utc).isoformat(),
            )

        pending = sum(1 for s in all_statuses if s.overall_status == "pending")
        running = sum(1 for s in all_statuses if s.overall_status == "running")
        completed = sum(1 for s in all_statuses if s.overall_status == "completed")
        failed = sum(1 for s in all_statuses if s.overall_status == "failed")
        avg = sum(s.progress_pct for s in all_statuses) / total

        return PipelineSummary(
            total=total,
            pending=pending,
            running=running,
            completed=completed,
            failed=failed,
            avg_progress_pct=round(avg, 1),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def mark_stage(self, idea_id: str, stage: str, status: str, error: str = "") -> Optional[PipelineState]:
        """Update a stage status for an idea."""
        state = self._states.get(idea_id)
        if state is None:
            return None

        if status == "started":
            state.mark_started(stage)
        elif status == "completed":
            state.mark_completed(stage)
        elif status == "failed":
            state.mark_failed(stage, error)

        # Check if all stages complete
        if all(
            s.status in (StageStatus.COMPLETED, StageStatus.SKIPPED)
            for s in state.stages.values()
        ):
            state.finish()

        return state

    def remove(self, idea_id: str) -> bool:
        """Remove an idea from tracking."""
        if idea_id in self._states:
            del self._states[idea_id]
            self._titles.pop(idea_id, None)
            return True
        return False
