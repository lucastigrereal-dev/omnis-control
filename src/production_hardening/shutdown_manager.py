"""W179 — Graceful Shutdown Manager: coordinates ordered module teardown."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from src.remote_control.models import _new_id, _now_iso


class ShutdownPhase(str, Enum):
    PENDING = "PENDING"
    DRAINING = "DRAINING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


ShutdownHook = Callable[[], None]


# ---------------------------------------------------------------------------
# Module shutdown descriptor
# ---------------------------------------------------------------------------

@dataclass
class ShutdownModule:
    name: str
    phase: int = 0          # lower phase shuts down later (last to start, first to stop? reversed here: 0 = first)
    hook: Optional[ShutdownHook] = None
    timeout_seconds: float = 5.0
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "phase": self.phase,
            "timeout_seconds": self.timeout_seconds,
            "dry_run": self.dry_run,
        }


# ---------------------------------------------------------------------------
# Shutdown result
# ---------------------------------------------------------------------------

@dataclass
class ModuleShutdownResult:
    name: str
    status: ShutdownPhase = ShutdownPhase.PENDING
    duration_ms: float = 0.0
    error: str = ""
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "duration_ms": round(self.duration_ms, 2),
            "error": self.error,
            "dry_run": self.dry_run,
        }


@dataclass
class ShutdownReport:
    report_id: str = field(default_factory=lambda: _new_id("sdr"))
    ok: bool = True
    results: list[ModuleShutdownResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    initiated_at: str = field(default_factory=_now_iso)
    completed_at: str = ""

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "ok": self.ok,
            "results": [r.to_dict() for r in self.results],
            "total_duration_ms": round(self.total_duration_ms, 2),
            "initiated_at": self.initiated_at,
            "completed_at": self.completed_at,
            "summary": {
                "stopped": sum(1 for r in self.results if r.status == ShutdownPhase.STOPPED),
                "failed": sum(1 for r in self.results if r.status == ShutdownPhase.FAILED),
            },
        }


# ---------------------------------------------------------------------------
# Shutdown Manager
# ---------------------------------------------------------------------------

class ShutdownManager:
    """Coordinates ordered, phased teardown of OMNIS modules."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self._modules: list[ShutdownModule] = []
        self._reports: list[ShutdownReport] = []
        self._phase = ShutdownPhase.PENDING

    def register(self, module: ShutdownModule) -> None:
        module.dry_run = self.dry_run
        self._modules.append(module)

    def register_hook(self, name: str, hook: ShutdownHook, phase: int = 0, timeout: float = 5.0) -> ShutdownModule:
        mod = ShutdownModule(name=name, phase=phase, hook=hook, timeout_seconds=timeout, dry_run=self.dry_run)
        self._modules.append(mod)
        return mod

    # ------------------------------------------------------------------
    def shutdown(self) -> ShutdownReport:
        import time
        report = ShutdownReport()
        self._phase = ShutdownPhase.DRAINING
        start_total = time.perf_counter()

        # Sort by phase descending (highest phase = outermost, stops last → reversed: stops first)
        # Convention: phase 0 = core (stops last), phase 10 = edge (stops first)
        ordered = sorted(self._modules, key=lambda m: m.phase, reverse=True)

        for mod in ordered:
            result = ModuleShutdownResult(name=mod.name, dry_run=self.dry_run)
            start = time.perf_counter()

            if self.dry_run:
                result.status = ShutdownPhase.STOPPED
                result.duration_ms = (time.perf_counter() - start) * 1000
                report.results.append(result)
                continue

            if mod.hook is None:
                result.status = ShutdownPhase.STOPPED
                result.duration_ms = (time.perf_counter() - start) * 1000
                report.results.append(result)
                continue

            try:
                mod.hook()
                result.status = ShutdownPhase.STOPPED
            except Exception as exc:
                result.status = ShutdownPhase.FAILED
                result.error = str(exc)
                report.ok = False

            result.duration_ms = (time.perf_counter() - start) * 1000
            report.results.append(result)

        report.total_duration_ms = (time.perf_counter() - start_total) * 1000
        report.completed_at = _now_iso()
        self._phase = ShutdownPhase.STOPPED if report.ok else ShutdownPhase.FAILED
        self._reports.append(report)
        return report

    @property
    def phase(self) -> ShutdownPhase:
        return self._phase

    def modules(self) -> list[str]:
        return [m.name for m in self._modules]

    def history(self) -> list[ShutdownReport]:
        return list(self._reports)

    def stats(self) -> dict:
        return {
            "registered": len(self._modules),
            "shutdowns": len(self._reports),
            "current_phase": self._phase.value,
            "dry_run": self.dry_run,
        }
