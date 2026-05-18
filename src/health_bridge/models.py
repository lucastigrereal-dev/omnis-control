"""W196-197 — Normalized HealthStatus model + Doctor contract."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


class HealthLevel(str, Enum):
    OK = "ok"
    WARN = "warn"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    name: str
    level: HealthLevel = HealthLevel.UNKNOWN
    message: str = ""
    details: dict = field(default_factory=dict)
    checked_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "name": self.name, "level": self.level.value,
            "message": self.message, "details": self.details,
            "checked_at": self.checked_at,
        }

    @classmethod
    def ok(cls, name: str, message: str = "") -> "HealthCheck":
        return cls(name=name, level=HealthLevel.OK, message=message)

    @classmethod
    def warn(cls, name: str, message: str) -> "HealthCheck":
        return cls(name=name, level=HealthLevel.WARN, message=message)

    @classmethod
    def error(cls, name: str, message: str) -> "HealthCheck":
        return cls(name=name, level=HealthLevel.ERROR, message=message)


@dataclass
class HealthStatus:
    status: HealthLevel = HealthLevel.OK
    checks: list[HealthCheck] = field(default_factory=list)
    timestamp: str = field(default_factory=_now_iso)
    source: str = "omnis-health-bridge"

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "checks": [c.to_dict() for c in self.checks],
            "timestamp": self.timestamp,
            "source": self.source,
        }

    @classmethod
    def from_checks(cls, checks: list[HealthCheck], source: str = "omnis-health-bridge") -> "HealthStatus":
        levels = [c.level for c in checks]
        if any(l == HealthLevel.ERROR for l in levels):
            overall = HealthLevel.ERROR
        elif any(l == HealthLevel.WARN for l in levels):
            overall = HealthLevel.WARN
        elif all(l == HealthLevel.OK for l in levels) and levels:
            overall = HealthLevel.OK
        else:
            overall = HealthLevel.UNKNOWN
        return cls(status=overall, checks=checks, source=source)
