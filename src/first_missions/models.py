"""W181 — First Real Missions: Mission model & registry."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


class MissionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    DRY_RUN = "DRY_RUN"


class MissionType(str, Enum):
    CONTENT_GENERATION = "CONTENT_GENERATION"
    CAPTION_APPROVAL = "CAPTION_APPROVAL"
    CAMPAIGN_AUDIT = "CAMPAIGN_AUDIT"
    METRIC_REPORT = "METRIC_REPORT"
    LEAD_QUALIFICATION = "LEAD_QUALIFICATION"
    WAVE_PROGRESS_REPORT = "WAVE_PROGRESS_REPORT"
    HEALTH_SNAPSHOT = "HEALTH_SNAPSHOT"
    CUSTOM = "CUSTOM"


class MissionPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FailureCategory(str, Enum):
    NONE = "NONE"
    VALIDATION = "VALIDATION"
    RUNTIME = "RUNTIME"
    STORAGE = "STORAGE"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Mission
# ---------------------------------------------------------------------------

@dataclass
class Mission:
    mission_id: str = field(default_factory=lambda: _new_id("mss"))
    name: str = ""
    mission_type: MissionType = MissionType.CUSTOM
    priority: MissionPriority = MissionPriority.NORMAL
    status: MissionStatus = MissionStatus.PENDING
    payload: dict = field(default_factory=dict)
    result: dict = field(default_factory=dict)
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)
    started_at: str = ""
    completed_at: str = ""
    error: str = ""
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        return self.status in (MissionStatus.COMPLETED, MissionStatus.FAILED, MissionStatus.CANCELLED)

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "name": self.name,
            "mission_type": self.mission_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "payload": self.payload,
            "result": self.result,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Mission":
        return cls(
            mission_id=d.get("mission_id", _new_id("mss")),
            name=d.get("name", ""),
            mission_type=MissionType(d.get("mission_type", "CUSTOM")),
            priority=MissionPriority(d.get("priority", "NORMAL")),
            status=MissionStatus(d.get("status", "PENDING")),
            payload=d.get("payload", {}),
            result=d.get("result", {}),
            dry_run=d.get("dry_run", True),
            created_at=d.get("created_at", _now_iso()),
            started_at=d.get("started_at", ""),
            completed_at=d.get("completed_at", ""),
            error=d.get("error", ""),
            tags=d.get("tags", []),
            metadata=d.get("metadata", {}),
        )

    # Factories
    @classmethod
    def content_generation(cls, profile: str, topic: str) -> "Mission":
        return cls(
            name=f"content:{profile}:{topic}",
            mission_type=MissionType.CONTENT_GENERATION,
            payload={"profile": profile, "topic": topic},
        )

    @classmethod
    def metric_report(cls, metric_name: str, period: str = "daily") -> "Mission":
        return cls(
            name=f"metric:{metric_name}:{period}",
            mission_type=MissionType.METRIC_REPORT,
            payload={"metric": metric_name, "period": period},
        )

    @classmethod
    def health_snapshot(cls) -> "Mission":
        return cls(
            name="health_snapshot",
            mission_type=MissionType.HEALTH_SNAPSHOT,
            priority=MissionPriority.HIGH,
        )


# ---------------------------------------------------------------------------
# Mission Registry
# ---------------------------------------------------------------------------

class MissionRegistry:
    """Stores and queries missions with filtering."""

    def __init__(self) -> None:
        self._missions: dict[str, Mission] = {}

    def register(self, mission: Mission) -> Mission:
        self._missions[mission.mission_id] = mission
        return mission

    def get(self, mission_id: str) -> Mission | None:
        return self._missions.get(mission_id)

    def query(
        self,
        status: MissionStatus | None = None,
        mission_type: MissionType | None = None,
        priority: MissionPriority | None = None,
        limit: int = 100,
    ) -> list[Mission]:
        results = list(self._missions.values())
        if status:
            results = [m for m in results if m.status == status]
        if mission_type:
            results = [m for m in results if m.mission_type == mission_type]
        if priority:
            results = [m for m in results if m.priority == priority]
        return results[:limit]

    def pending(self) -> list[Mission]:
        return self.query(status=MissionStatus.PENDING)

    def completed(self) -> list[Mission]:
        return self.query(status=MissionStatus.COMPLETED)

    def stats(self) -> dict:
        total = len(self._missions)
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for m in self._missions.values():
            by_status[m.status.value] = by_status.get(m.status.value, 0) + 1
            by_type[m.mission_type.value] = by_type.get(m.mission_type.value, 0) + 1
        return {"total": total, "by_status": by_status, "by_type": by_type}

    def validate(self) -> dict:
        """Validate all registered missions. Returns report with issues."""
        issues: list[dict] = []
        seen_names: dict[str, str] = {}

        for m in self._missions.values():
            # Missing name
            if not m.name.strip():
                issues.append({
                    "mission_id": m.mission_id,
                    "severity": "error",
                    "issue": "Mission has empty name",
                })

            # Duplicate name
            if m.name and m.name in seen_names:
                issues.append({
                    "mission_id": m.mission_id,
                    "severity": "warning",
                    "issue": f"Duplicate name: '{m.name}' also used by {seen_names[m.name]}",
                })
            elif m.name:
                seen_names[m.name] = m.mission_id

            # Content missions must have profile in payload
            if m.mission_type == MissionType.CONTENT_GENERATION:
                if "profile" not in m.payload:
                    issues.append({
                        "mission_id": m.mission_id,
                        "severity": "warning",
                        "issue": "Content generation mission missing 'profile' in payload",
                    })

            # Metric missions must have metric name
            if m.mission_type == MissionType.METRIC_REPORT:
                if "metric" not in m.payload:
                    issues.append({
                        "mission_id": m.mission_id,
                        "severity": "warning",
                        "issue": "Metric report mission missing 'metric' in payload",
                    })

        return {
            "total": len(self._missions),
            "issues": len(issues),
            "valid": len(issues) == 0,
            "details": issues,
        }
