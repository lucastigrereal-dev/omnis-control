"""Stage Events — deterministic stage lifecycle events linked to traces."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class StageStatus(str, Enum):
    PLANNED = "planned"
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class StageEvent:
    """Deterministic stage event — linked to a trace span for correlation."""

    stage_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    stage_name: str = ""
    phase: str = ""
    status: StageStatus = StageStatus.PLANNED
    trace_id: str = ""
    span_id: str = ""
    mission_id: str = ""
    run_id: str = ""
    duration_ms: float = 0.0
    artifacts_produced: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def for_stage(
        cls,
        stage_name: str,
        phase: str = "",
        mission_id: str = "",
        run_id: str = "",
    ) -> "StageEvent":
        return cls(
            stage_name=stage_name,
            phase=phase,
            mission_id=mission_id,
            run_id=run_id,
            trace_id=uuid.uuid4().hex,
            span_id=uuid.uuid4().hex[:16],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_id": self.stage_id,
            "stage_name": self.stage_name,
            "phase": self.phase,
            "status": self.status.value,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "mission_id": self.mission_id,
            "run_id": self.run_id,
            "duration_ms": self.duration_ms,
            "artifacts_produced": self.artifacts_produced,
            "warnings": self.warnings,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }
