"""W184 — Mission Result Store: persistence and retrieval of mission results."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.first_missions.models import Mission, MissionStatus, MissionType, _new_id, _now_iso


@dataclass
class StoredResult:
    result_id: str = field(default_factory=lambda: _new_id("res"))
    mission_id: str = ""
    mission_name: str = ""
    mission_type: str = ""
    status: str = MissionStatus.COMPLETED.value
    result: dict = field(default_factory=dict)
    error: str = ""
    duration_ms: float = 0.0
    dry_run: bool = True
    stored_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "mission_id": self.mission_id,
            "mission_name": self.mission_name,
            "mission_type": self.mission_type,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
            "dry_run": self.dry_run,
            "stored_at": self.stored_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StoredResult":
        return cls(
            result_id=d.get("result_id", _new_id("res")),
            mission_id=d.get("mission_id", ""),
            mission_name=d.get("mission_name", ""),
            mission_type=d.get("mission_type", ""),
            status=d.get("status", MissionStatus.COMPLETED.value),
            result=d.get("result", {}),
            error=d.get("error", ""),
            duration_ms=d.get("duration_ms", 0.0),
            dry_run=d.get("dry_run", True),
            stored_at=d.get("stored_at", _now_iso()),
        )

    @classmethod
    def from_mission(cls, mission: Mission, duration_ms: float = 0.0) -> "StoredResult":
        return cls(
            mission_id=mission.mission_id,
            mission_name=mission.name,
            mission_type=mission.mission_type.value,
            status=mission.status.value,
            result=mission.result,
            error=mission.error,
            duration_ms=duration_ms,
            dry_run=mission.dry_run,
        )


class MissionResultStore:
    """In-memory result store with optional JSONL persistence."""

    def __init__(self, path: Optional[Path] = None, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self._path = path
        self._store: dict[str, StoredResult] = {}
        if path and path.exists():
            self._load(path)

    def save(self, result: StoredResult) -> StoredResult:
        self._store[result.result_id] = result
        if self._path and not self.dry_run:
            self._append(result)
        return result

    def save_mission(self, mission: Mission, duration_ms: float = 0.0) -> StoredResult:
        stored = StoredResult.from_mission(mission, duration_ms=duration_ms)
        return self.save(stored)

    def get(self, result_id: str) -> Optional[StoredResult]:
        return self._store.get(result_id)

    def by_mission(self, mission_id: str) -> list[StoredResult]:
        return [r for r in self._store.values() if r.mission_id == mission_id]

    def query(
        self,
        status: Optional[str] = None,
        mission_type: Optional[str] = None,
        dry_run: Optional[bool] = None,
        limit: int = 100,
    ) -> list[StoredResult]:
        results = list(self._store.values())
        if status:
            results = [r for r in results if r.status == status]
        if mission_type:
            results = [r for r in results if r.mission_type == mission_type]
        if dry_run is not None:
            results = [r for r in results if r.dry_run == dry_run]
        # Sort newest first
        results.sort(key=lambda r: r.stored_at, reverse=True)
        return results[:limit]

    def successful(self) -> list[StoredResult]:
        return self.query(status=MissionStatus.COMPLETED.value)

    def failed(self) -> list[StoredResult]:
        return self.query(status=MissionStatus.FAILED.value)

    def stats(self) -> dict:
        total = len(self._store)
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for r in self._store.values():
            by_status[r.status] = by_status.get(r.status, 0) + 1
            by_type[r.mission_type] = by_type.get(r.mission_type, 0) + 1
        return {"total": total, "by_status": by_status, "by_type": by_type, "dry_run": self.dry_run}

    def summary(self) -> dict:
        """Rich summary: counts, rates, avg duration, success/fail/dry breakdown."""
        total = len(self._store)
        if total == 0:
            return {
                "total": 0, "successful": 0, "failed": 0, "dry_run": 0,
                "success_rate": 0.0, "avg_duration_ms": 0.0,
            }

        success = len(self.query(status=MissionStatus.COMPLETED.value))
        failed = len(self.query(status=MissionStatus.FAILED.value))
        dry = len(self.query(status=MissionStatus.DRY_RUN.value))
        durations = [r.duration_ms for r in self._store.values() if r.duration_ms > 0]

        return {
            "total": total,
            "successful": success,
            "failed": failed,
            "dry_run": dry,
            "success_rate": round(success / max(total - dry, 1), 3),
            "avg_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0.0,
        }

    # ------------------------------------------------------------------
    def _append(self, result: StoredResult) -> None:
        assert self._path is not None
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(result.to_dict()) + "\n")

    def _load(self, path: Path) -> None:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        self._store[_new_id("res")] = StoredResult.from_dict(json.loads(line))
                    except Exception:
                        pass
