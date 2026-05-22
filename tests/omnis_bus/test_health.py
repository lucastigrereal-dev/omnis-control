"""Tests for OMNIS Bus health collector (17.4)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from src.omnis_bus.health import BusHealth, HealthCollector, health_to_event_envelope


class TestBusHealth:
    def test_default_state(self):
        h = BusHealth()
        assert h.bus_online is False
        assert h.last_event_at is None
        assert h.listener_count == 0
        assert h.error_count == 0
        assert h.events_received == 0
        assert h.source_badges == []
        assert h.channels_active == []

    def test_to_payload(self):
        h = BusHealth(bus_online=True, listener_count=3)
        payload = h.to_payload()
        assert payload["bus_online"] is True
        assert payload["listener_count"] == 3
        assert "checked_at" in payload


class TestHealthCollector:
    def test_initial_snapshot(self):
        c = HealthCollector()
        snap = c.snapshot()
        assert snap.bus_online is True
        assert snap.events_received == 0

    def test_record_event_updates_stats(self):
        c = HealthCollector()
        c.record_event("system.heartbeat", "kratos", "system:heartbeat")
        c.record_event("memory.ingested", "akasha", "akasha:memory")

        snap = c.snapshot()
        assert snap.events_received == 2
        assert snap.last_event_type == "memory.ingested"
        assert "kratos" in snap.source_badges
        assert "akasha" in snap.source_badges
        assert "system:heartbeat" in snap.channels_active
        assert "akasha:memory" in snap.channels_active

    def test_record_error_increments_counter(self):
        c = HealthCollector()
        c.record_error()
        c.record_error()
        snap = c.snapshot()
        assert snap.error_count == 2

    def test_set_listener_count(self):
        c = HealthCollector()
        c.set_listener_count(5)
        snap = c.snapshot()
        assert snap.listener_count == 5

    def test_set_channels(self):
        c = HealthCollector()
        c.set_channels(["omnis:runtime", "akasha:memory"])
        snap = c.snapshot()
        assert set(snap.channels_active) == {"omnis:runtime", "akasha:memory"}

    def test_uptime_increases(self):
        import time
        c = HealthCollector()
        snap1 = c.snapshot()
        time.sleep(0.1)
        snap2 = c.snapshot()
        assert snap2.uptime_seconds > snap1.uptime_seconds

    def test_multiple_snapshots_dont_reset(self):
        c = HealthCollector()
        c.record_event("test", "omnis")
        snap1 = c.snapshot()
        snap2 = c.snapshot()
        assert snap2.events_received == snap1.events_received


class TestHealthToEventEnvelope:
    def test_converts_to_envelope(self):
        h = BusHealth(bus_online=True, listener_count=3, events_received=42)
        payload = health_to_event_envelope(h, "test-service", "1.0")
        assert payload["type"] == "bus.health"
        assert payload["payload"]["listener_count"] == 3
        assert payload["payload"]["events_received"] == 42
        assert payload["source"]["service"] == "test-service"
