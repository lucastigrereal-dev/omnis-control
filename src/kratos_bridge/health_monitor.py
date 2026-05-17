"""W166 — KRATOS Bridge Health Monitor: cockpit health checks & heartbeat tracking."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .models import _new_id, _now_iso


class HealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@dataclass
class HealthCheck:
    check_id: str = field(default_factory=lambda: _new_id("hc"))
    component: str = ""
    status: HealthStatus = HealthStatus.UNKNOWN
    message: str = ""
    latency_ms: float = 0.0
    checked_at: str = field(default_factory=_now_iso)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "checked_at": self.checked_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HealthCheck":
        return cls(
            check_id=data.get("check_id", _new_id("hc")),
            component=data.get("component", ""),
            status=HealthStatus(data.get("status", "UNKNOWN")),
            message=data.get("message", ""),
            latency_ms=data.get("latency_ms", 0.0),
            checked_at=data.get("checked_at", _now_iso()),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def ok(cls, component: str, latency_ms: float = 0.0) -> "HealthCheck":
        return cls(component=component, status=HealthStatus.HEALTHY, latency_ms=latency_ms)

    @classmethod
    def degraded(cls, component: str, message: str) -> "HealthCheck":
        return cls(component=component, status=HealthStatus.DEGRADED, message=message)

    @classmethod
    def unhealthy(cls, component: str, message: str) -> "HealthCheck":
        return cls(component=component, status=HealthStatus.UNHEALTHY, message=message)


# ---------------------------------------------------------------------------
# Heartbeat
# ---------------------------------------------------------------------------

@dataclass
class Heartbeat:
    beat_id: str = field(default_factory=lambda: _new_id("hb"))
    source: str = "omnis"
    sequence: int = 0
    sent_at: str = field(default_factory=_now_iso)
    acknowledged: bool = False
    ack_at: str = ""

    def to_dict(self) -> dict:
        return {
            "beat_id": self.beat_id,
            "source": self.source,
            "sequence": self.sequence,
            "sent_at": self.sent_at,
            "acknowledged": self.acknowledged,
            "ack_at": self.ack_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Heartbeat":
        return cls(
            beat_id=data.get("beat_id", _new_id("hb")),
            source=data.get("source", "omnis"),
            sequence=data.get("sequence", 0),
            sent_at=data.get("sent_at", _now_iso()),
            acknowledged=data.get("acknowledged", False),
            ack_at=data.get("ack_at", ""),
        )


# ---------------------------------------------------------------------------
# Health report
# ---------------------------------------------------------------------------

@dataclass
class HealthReport:
    report_id: str = field(default_factory=lambda: _new_id("hr"))
    overall: HealthStatus = HealthStatus.UNKNOWN
    checks: list[HealthCheck] = field(default_factory=list)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "overall": self.overall.value,
            "checks": [c.to_dict() for c in self.checks],
            "generated_at": self.generated_at,
        }


# ---------------------------------------------------------------------------
# Health monitor
# ---------------------------------------------------------------------------

class KratosHealthMonitor:
    """Tracks KRATOS bridge component health and heartbeat sequences."""

    _LATENCY_DEGRADED_MS = 500.0
    _LATENCY_UNHEALTHY_MS = 2000.0
    _MISSED_BEATS_DEGRADED = 2
    _MISSED_BEATS_UNHEALTHY = 5

    def __init__(self) -> None:
        self._checks: dict[str, list[HealthCheck]] = {}
        self._heartbeats: list[Heartbeat] = []
        self._sequence = 0

    # ------------------------------------------------------------------
    def record_check(self, check: HealthCheck) -> HealthCheck:
        self._checks.setdefault(check.component, []).append(check)
        return check

    def check_component(self, component: str, latency_ms: float = 0.0) -> HealthCheck:
        if latency_ms >= self._LATENCY_UNHEALTHY_MS:
            check = HealthCheck.unhealthy(component, f"latency {latency_ms:.0f}ms exceeds threshold")
        elif latency_ms >= self._LATENCY_DEGRADED_MS:
            check = HealthCheck.degraded(component, f"latency {latency_ms:.0f}ms elevated")
        else:
            check = HealthCheck.ok(component, latency_ms)
        return self.record_check(check)

    # ------------------------------------------------------------------
    def send_heartbeat(self) -> Heartbeat:
        self._sequence += 1
        beat = Heartbeat(sequence=self._sequence)
        self._heartbeats.append(beat)
        return beat

    def acknowledge_heartbeat(self, beat_id: str) -> bool:
        for beat in self._heartbeats:
            if beat.beat_id == beat_id:
                beat.acknowledged = True
                beat.ack_at = _now_iso()
                return True
        return False

    def missed_beats(self) -> int:
        return sum(1 for b in self._heartbeats if not b.acknowledged)

    # ------------------------------------------------------------------
    def report(self) -> HealthReport:
        latest_checks: list[HealthCheck] = []
        for component, checks in self._checks.items():
            latest_checks.append(checks[-1])

        # Determine overall status
        statuses = [c.status for c in latest_checks]
        missed = self.missed_beats()

        if HealthStatus.UNHEALTHY in statuses or missed >= self._MISSED_BEATS_UNHEALTHY:
            overall = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses or missed >= self._MISSED_BEATS_DEGRADED:
            overall = HealthStatus.DEGRADED
        elif statuses and all(s == HealthStatus.HEALTHY for s in statuses):
            overall = HealthStatus.HEALTHY
        else:
            overall = HealthStatus.UNKNOWN

        return HealthReport(overall=overall, checks=latest_checks)

    def is_healthy(self) -> bool:
        return self.report().overall == HealthStatus.HEALTHY

    def latest_check(self, component: str) -> Optional[HealthCheck]:
        checks = self._checks.get(component, [])
        return checks[-1] if checks else None

    def stats(self) -> dict:
        total_beats = len(self._heartbeats)
        ack = sum(1 for b in self._heartbeats if b.acknowledged)
        return {
            "components": list(self._checks.keys()),
            "total_heartbeats": total_beats,
            "acknowledged": ack,
            "missed": total_beats - ack,
            "overall": self.report().overall.value,
        }
