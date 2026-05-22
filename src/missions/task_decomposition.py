"""Task Decomposition — structured mission task breakdown with dependencies."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskType(str, Enum):
    PLANNING = "planning"
    MEMORY = "memory"
    EXECUTION = "execution"
    REVIEW = "review"
    REPORT = "report"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class MissionTask(BaseModel):
    """A single task within a mission decomposition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    type: TaskType
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    assignee: str = ""
    depends_on: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    estimated_tokens: int = 0


class TaskDecomposition(BaseModel):
    """Structured breakdown of a mission into tasks with dependency ordering."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mission_id: str = ""
    tasks: list[MissionTask] = Field(default_factory=list)
    total_estimated_tokens: int = 0
    created_at: str = ""

    @classmethod
    def create_default(cls, mission_id: str) -> "TaskDecomposition":
        """Create default 5-task decomposition with dependency chain."""
        tasks = [
            MissionTask(
                id=f"{mission_id}-planning",
                type=TaskType.PLANNING,
                description="Analyze intent and create execution plan",
            ),
            MissionTask(
                id=f"{mission_id}-memory",
                type=TaskType.MEMORY,
                description="Look up relevant context from memory systems",
                depends_on=[f"{mission_id}-planning"],
            ),
            MissionTask(
                id=f"{mission_id}-execution",
                type=TaskType.EXECUTION,
                description="Execute the mission plan",
                depends_on=[f"{mission_id}-planning", f"{mission_id}-memory"],
            ),
            MissionTask(
                id=f"{mission_id}-review",
                type=TaskType.REVIEW,
                description="Review outputs and verify acceptance criteria",
                depends_on=[f"{mission_id}-execution"],
            ),
            MissionTask(
                id=f"{mission_id}-report",
                type=TaskType.REPORT,
                description="Generate mission completion report",
                depends_on=[f"{mission_id}-review"],
            ),
        ]
        return cls(
            mission_id=mission_id,
            tasks=tasks,
            total_estimated_tokens=sum(t.estimated_tokens for t in tasks),
        )
