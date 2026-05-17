"""W168 — KRATOS Bridge Snapshot: captures OMNIS state for cockpit display."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .models import _new_id, _now_iso


# ---------------------------------------------------------------------------
# Snapshot sections
# ---------------------------------------------------------------------------

@dataclass
class WaveProgressSection:
    current_wave: str = ""
    total_waves: int = 210
    completed_waves: int = 0
    pct: float = 0.0
    current_group: str = ""

    def to_dict(self) -> dict:
        return {
            "current_wave": self.current_wave,
            "total_waves": self.total_waves,
            "completed_waves": self.completed_waves,
            "pct": round(self.pct, 1),
            "current_group": self.current_group,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WaveProgressSection":
        return cls(
            current_wave=d.get("current_wave", ""),
            total_waves=d.get("total_waves", 210),
            completed_waves=d.get("completed_waves", 0),
            pct=d.get("pct", 0.0),
            current_group=d.get("current_group", ""),
        )


@dataclass
class TestSuiteSection:
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    last_run: str = ""

    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return round(self.passed / self.total * 100, 1)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "pass_rate": self.pass_rate,
            "last_run": self.last_run,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TestSuiteSection":
        return cls(
            total=d.get("total", 0),
            passed=d.get("passed", 0),
            failed=d.get("failed", 0),
            skipped=d.get("skipped", 0),
            last_run=d.get("last_run", ""),
        )


@dataclass
class SystemSection:
    healthy: bool = True
    dry_run: bool = True
    active_modules: list[str] = field(default_factory=list)
    version: str = "0.1.0"

    def to_dict(self) -> dict:
        return {
            "healthy": self.healthy,
            "dry_run": self.dry_run,
            "active_modules": self.active_modules,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SystemSection":
        return cls(
            healthy=d.get("healthy", True),
            dry_run=d.get("dry_run", True),
            active_modules=d.get("active_modules", []),
            version=d.get("version", "0.1.0"),
        )


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------

@dataclass
class CockpitSnapshot:
    snapshot_id: str = field(default_factory=lambda: _new_id("snap"))
    wave_progress: WaveProgressSection = field(default_factory=WaveProgressSection)
    test_suite: TestSuiteSection = field(default_factory=TestSuiteSection)
    system: SystemSection = field(default_factory=SystemSection)
    alerts: list[dict] = field(default_factory=list)
    recent_events: list[dict] = field(default_factory=list)
    captured_at: str = field(default_factory=_now_iso)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "wave_progress": self.wave_progress.to_dict(),
            "test_suite": self.test_suite.to_dict(),
            "system": self.system.to_dict(),
            "alerts": self.alerts,
            "recent_events": self.recent_events,
            "captured_at": self.captured_at,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: dict) -> "CockpitSnapshot":
        return cls(
            snapshot_id=d.get("snapshot_id", _new_id("snap")),
            wave_progress=WaveProgressSection.from_dict(d.get("wave_progress", {})),
            test_suite=TestSuiteSection.from_dict(d.get("test_suite", {})),
            system=SystemSection.from_dict(d.get("system", {})),
            alerts=d.get("alerts", []),
            recent_events=d.get("recent_events", []),
            captured_at=d.get("captured_at", _now_iso()),
            metadata=d.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, raw: str) -> "CockpitSnapshot":
        return cls.from_dict(json.loads(raw))


# ---------------------------------------------------------------------------
# Snapshot builder
# ---------------------------------------------------------------------------

class SnapshotBuilder:
    """Builds CockpitSnapshots and optionally persists them."""

    def __init__(self, snapshot_dir: Optional[Path] = None) -> None:
        self._snapshot_dir = snapshot_dir
        self._history: list[CockpitSnapshot] = []

    def build(
        self,
        wave: str = "",
        completed: int = 0,
        total_waves: int = 210,
        group: str = "",
        tests_passed: int = 0,
        tests_total: int = 0,
        healthy: bool = True,
        dry_run: bool = True,
        active_modules: Optional[list[str]] = None,
        alerts: Optional[list[dict]] = None,
        recent_events: Optional[list[dict]] = None,
        metadata: Optional[dict] = None,
    ) -> CockpitSnapshot:
        pct = round(completed / total_waves * 100, 1) if total_waves > 0 else 0.0
        snap = CockpitSnapshot(
            wave_progress=WaveProgressSection(
                current_wave=wave,
                total_waves=total_waves,
                completed_waves=completed,
                pct=pct,
                current_group=group,
            ),
            test_suite=TestSuiteSection(
                total=tests_total,
                passed=tests_passed,
                failed=tests_total - tests_passed,
                last_run=_now_iso(),
            ),
            system=SystemSection(
                healthy=healthy,
                dry_run=dry_run,
                active_modules=active_modules or [],
            ),
            alerts=alerts or [],
            recent_events=recent_events or [],
            metadata=metadata or {},
        )
        self._history.append(snap)
        if self._snapshot_dir:
            self._persist(snap)
        return snap

    def latest(self) -> Optional[CockpitSnapshot]:
        return self._history[-1] if self._history else None

    def history(self) -> list[CockpitSnapshot]:
        return list(self._history)

    def _persist(self, snap: CockpitSnapshot) -> None:
        try:
            self._snapshot_dir.mkdir(parents=True, exist_ok=True)
            path = self._snapshot_dir / f"{snap.snapshot_id}.json"
            path.write_text(snap.to_json(), encoding="utf-8")
        except OSError:
            pass
