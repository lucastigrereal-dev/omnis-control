"""Unified health models — bridge between jarvis doctor and GET /health."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class HealthStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass
class CheckResult:
    """Normalized individual health check result."""
    name: str
    status: HealthStatus
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: int = 0
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CheckResult:
        error = data.get("error")
        if error:
            status = HealthStatus.ERROR
        else:
            status_raw = data.get("status") or data.get("severity", "ok")
            try:
                status = HealthStatus(status_raw)
            except ValueError:
                status = HealthStatus.UNKNOWN
        return cls(
            name=data["name"],
            status=status,
            data=data.get("data", {}),
            error=error,
            duration_ms=data.get("duration_ms", 0),
            timestamp=data.get("timestamp", ""),
        )


@dataclass
class HealthReport:
    """Aggregate health report from all checks."""
    session_id: str
    timestamp: str
    overall_status: HealthStatus
    checks: list[CheckResult] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "overall_status": self.overall_status.value,
            "checks": [c.to_dict() for c in self.checks],
            "risks": self.risks,
            "next_steps": self.next_steps,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HealthReport:
        raw_checks = data.get("checks", [])
        if isinstance(raw_checks, dict):
            checks = [CheckResult.from_dict({"name": k, **v}) for k, v in raw_checks.items()]
        elif isinstance(raw_checks, list) and raw_checks and isinstance(raw_checks[0], dict) and "name" in raw_checks[0]:
            checks = [CheckResult.from_dict(c) for c in raw_checks]
        else:
            checks = cls._normalize_legacy_checks(raw_checks)

        return cls(
            session_id=data.get("session_id", ""),
            timestamp=data.get("timestamp", ""),
            overall_status=HealthStatus(data.get("overall_status", "unknown")),
            checks=checks,
            risks=data.get("risks", []),
            next_steps=data.get("next_steps", []),
        )

    @staticmethod
    def _normalize_legacy_checks(raw_checks: dict[str, Any]) -> list[CheckResult]:
        """Convert legacy dict-of-dicts checks to list of CheckResult."""
        results = []
        if not isinstance(raw_checks, dict):
            return results
        for name, data in raw_checks.items():
            if isinstance(data, dict):
                error = data.get("error")
                status = HealthStatus.ERROR if error else HealthStatus.OK
                results.append(CheckResult(
                    name=name,
                    status=status,
                    data=data,
                    error=error,
                ))
            else:
                results.append(CheckResult(
                    name=name,
                    status=HealthStatus.UNKNOWN,
                    data={"raw": data},
                ))
        return results

    def healthy_count(self) -> int:
        return sum(1 for c in self.checks if c.status == HealthStatus.OK)

    def warning_count(self) -> int:
        return sum(1 for c in self.checks if c.status == HealthStatus.WARNING)

    def critical_count(self) -> int:
        return sum(1 for c in self.checks if c.status in (HealthStatus.CRITICAL, HealthStatus.ERROR))
