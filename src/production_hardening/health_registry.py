"""W174 — Health Check Registry: centralized module health verification."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from src.remote_control.models import _new_id, _now_iso


class CheckStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


# ---------------------------------------------------------------------------
# Check definition
# ---------------------------------------------------------------------------

@dataclass
class HealthCheckDef:
    check_id: str = field(default_factory=lambda: _new_id("chk"))
    name: str = ""
    module: str = ""
    fn: Optional[Callable[[], bool]] = None
    critical: bool = False          # if True, FAIL → overall FAIL
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "module": self.module,
            "critical": self.critical,
            "enabled": self.enabled,
        }


# ---------------------------------------------------------------------------
# Check result
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    check_id: str = ""
    name: str = ""
    module: str = ""
    status: CheckStatus = CheckStatus.SKIP
    message: str = ""
    critical: bool = False
    duration_ms: float = 0.0
    checked_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "module": self.module,
            "status": self.status.value,
            "message": self.message,
            "critical": self.critical,
            "duration_ms": round(self.duration_ms, 2),
            "checked_at": self.checked_at,
        }


# ---------------------------------------------------------------------------
# Registry report
# ---------------------------------------------------------------------------

@dataclass
class RegistryReport:
    report_id: str = field(default_factory=lambda: _new_id("rpt"))
    overall: CheckStatus = CheckStatus.SKIP
    results: list[CheckResult] = field(default_factory=list)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "overall": self.overall.value,
            "results": [r.to_dict() for r in self.results],
            "generated_at": self.generated_at,
            "summary": {
                "pass": sum(1 for r in self.results if r.status == CheckStatus.PASS),
                "warn": sum(1 for r in self.results if r.status == CheckStatus.WARN),
                "fail": sum(1 for r in self.results if r.status == CheckStatus.FAIL),
                "skip": sum(1 for r in self.results if r.status == CheckStatus.SKIP),
            },
        }


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class HealthCheckRegistry:
    """Central registry of health checks across all OMNIS modules."""

    def __init__(self) -> None:
        self._checks: dict[str, HealthCheckDef] = {}
        self._history: list[RegistryReport] = []

    # ------------------------------------------------------------------
    def register(self, check: HealthCheckDef) -> HealthCheckDef:
        self._checks[check.check_id] = check
        return check

    def register_fn(
        self,
        name: str,
        fn: Callable[[], bool],
        module: str = "unknown",
        critical: bool = False,
    ) -> HealthCheckDef:
        check = HealthCheckDef(name=name, module=module, fn=fn, critical=critical)
        return self.register(check)

    def unregister(self, check_id: str) -> bool:
        return self._checks.pop(check_id, None) is not None

    # ------------------------------------------------------------------
    def run(self, module: Optional[str] = None) -> RegistryReport:
        import time
        report = RegistryReport()
        checks = list(self._checks.values())
        if module:
            checks = [c for c in checks if c.module == module]

        for chk in checks:
            result = CheckResult(
                check_id=chk.check_id,
                name=chk.name,
                module=chk.module,
                critical=chk.critical,
            )
            if not chk.enabled:
                result.status = CheckStatus.SKIP
                result.message = "disabled"
                report.results.append(result)
                continue

            if chk.fn is None:
                result.status = CheckStatus.SKIP
                result.message = "no_fn"
                report.results.append(result)
                continue

            start = time.perf_counter()
            try:
                ok = chk.fn()
                result.status = CheckStatus.PASS if ok else CheckStatus.FAIL
                result.message = "ok" if ok else "check_returned_false"
            except Exception as exc:
                result.status = CheckStatus.FAIL
                result.message = str(exc)
            finally:
                result.duration_ms = (time.perf_counter() - start) * 1000

            report.results.append(result)

        # Overall status
        statuses = [r.status for r in report.results]
        critical_failures = any(r.critical and r.status == CheckStatus.FAIL for r in report.results)
        if critical_failures or CheckStatus.FAIL in statuses:
            report.overall = CheckStatus.FAIL
        elif CheckStatus.WARN in statuses:
            report.overall = CheckStatus.WARN
        elif CheckStatus.PASS in statuses:
            report.overall = CheckStatus.PASS
        else:
            report.overall = CheckStatus.SKIP

        self._history.append(report)
        return report

    def run_one(self, check_id: str) -> Optional[CheckResult]:
        chk = self._checks.get(check_id)
        if not chk:
            return None
        report = self.run(module=None)
        for r in report.results:
            if r.check_id == check_id:
                return r
        return None

    # ------------------------------------------------------------------
    def checks(self) -> list[HealthCheckDef]:
        return list(self._checks.values())

    def history(self) -> list[RegistryReport]:
        return list(self._history)

    def latest_report(self) -> Optional[RegistryReport]:
        return self._history[-1] if self._history else None

    def stats(self) -> dict:
        return {
            "registered": len(self._checks),
            "enabled": sum(1 for c in self._checks.values() if c.enabled),
            "critical": sum(1 for c in self._checks.values() if c.critical),
            "history": len(self._history),
        }
