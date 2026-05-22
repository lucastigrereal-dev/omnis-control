"""Event Health — bus health payload and diagnostics collector.

Provides BusHealth snapshot: online status, last event, listener count,
error count, and source badges for all connected systems.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from .envelope import SourceBadge


class BusHealth(BaseModel):
    """Health snapshot of the OMNIS Bus."""

    bus_online: bool = False
    last_event_at: str | None = None
    last_event_type: str | None = None
    listener_count: int = 0
    error_count: int = 0
    events_received: int = 0
    source_badges: list[str] = Field(default_factory=list)
    channels_active: list[str] = Field(default_factory=list)
    uptime_seconds: float = 0.0
    checked_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class HealthCollector:
    """Collects health data from a bus instance for diagnostics.

    Usage:
        collector = HealthCollector()
        collector.record_event(event_type="system.heartbeat", source_badge="kratos")
        health = collector.snapshot()
    """

    def __init__(self):
        self._started_at = datetime.now(timezone.utc)
        self._last_event_at: str | None = None
        self._last_event_type: str | None = None
        self._error_count = 0
        self._events_received = 0
        self._source_badges: set[str] = set()
        self._channels_active: set[str] = set()
        self._listener_count = 0

    def record_event(
        self,
        event_type: str,
        source_badge: str = SourceBadge.UNKNOWN.value,
        channel: str | None = None,
    ) -> None:
        self._last_event_at = datetime.now(timezone.utc).isoformat()
        self._last_event_type = event_type
        self._events_received += 1
        self._source_badges.add(source_badge)
        if channel:
            self._channels_active.add(channel)

    def record_error(self) -> None:
        self._error_count += 1

    def set_listener_count(self, count: int) -> None:
        self._listener_count = count

    def set_channels(self, channels: list[str]) -> None:
        self._channels_active = set(channels)

    def snapshot(self) -> BusHealth:
        now = datetime.now(timezone.utc)
        uptime = (now - self._started_at).total_seconds()
        return BusHealth(
            bus_online=True,
            last_event_at=self._last_event_at,
            last_event_type=self._last_event_type,
            listener_count=self._listener_count,
            error_count=self._error_count,
            events_received=self._events_received,
            source_badges=sorted(self._source_badges),
            channels_active=sorted(self._channels_active),
            uptime_seconds=uptime,
        )


def health_to_event_envelope(health: BusHealth, source_service: str, source_version: str) -> dict[str, Any]:
    """Convert a BusHealth snapshot to a bus-ready event payload."""
    from .envelope import make_envelope

    env = make_envelope(
        event_type="bus.health",
        payload=health.to_payload(),
        source_service=source_service,
        source_version=source_version,
    )
    return env.to_redis_payload()
