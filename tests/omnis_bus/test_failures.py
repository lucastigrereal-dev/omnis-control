"""Tests for OMNIS Bus failure handling (17.7)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from src.omnis_bus.failures import (
    FAILURE_STRATEGY_MAP,
    DuplicateDetector,
    FailureIncident,
    FailureLog,
    FailureMode,
    ReconnectBackoff,
    RecoveryStrategy,
    SafeMessageHandler,
)


# ---------------------------------------------------------------------------
# FailureIncident
# ---------------------------------------------------------------------------
class TestFailureIncident:
    def test_records_mode_and_detail(self):
        incident = FailureIncident(FailureMode.REDIS_OFFLINE, "Connection refused")
        assert incident.mode == FailureMode.REDIS_OFFLINE
        assert incident.detail == "Connection refused"
        assert incident.strategy == RecoveryStrategy.RECONNECT_BACKOFF
        assert incident.timestamp

    def test_to_dict(self):
        incident = FailureIncident(FailureMode.MALFORMED_EVENT, "Missing fields", event_id="evt-123")
        d = incident.to_dict()
        assert d["mode"] == "malformed_event"
        assert d["event_id"] == "evt-123"
        assert d["strategy"] == "log_and_skip"


# ---------------------------------------------------------------------------
# ReconnectBackoff
# ---------------------------------------------------------------------------
class TestReconnectBackoff:
    def test_exponential_increase(self):
        backoff = ReconnectBackoff(base_delay=1.0, max_delay=60.0)
        d1 = backoff.next_delay()
        d2 = backoff.next_delay()
        d3 = backoff.next_delay()
        assert d1 == 1.0
        assert d2 == 2.0
        assert d3 == 4.0

    def test_caps_at_max(self):
        backoff = ReconnectBackoff(base_delay=1.0, max_delay=2.0)
        backoff.next_delay()  # 1.0
        backoff.next_delay()  # 2.0
        d3 = backoff.next_delay()  # 4.0 capped -> 2.0
        assert d3 == 2.0

    def test_reset(self):
        backoff = ReconnectBackoff(base_delay=1.0)
        backoff.next_delay()  # 1.0
        backoff.next_delay()  # 2.0
        backoff.reset()
        assert backoff.attempt == 0
        assert backoff.next_delay() == 1.0

    def test_attempt_counter(self):
        backoff = ReconnectBackoff()
        assert backoff.attempt == 0
        backoff.next_delay()
        assert backoff.attempt == 1


# ---------------------------------------------------------------------------
# DuplicateDetector
# ---------------------------------------------------------------------------
class TestDuplicateDetector:
    def test_first_occurrence_not_duplicate(self):
        dd = DuplicateDetector()
        assert dd.is_duplicate("evt-1") is False

    def test_second_occurrence_is_duplicate(self):
        dd = DuplicateDetector()
        dd.is_duplicate("evt-1")
        assert dd.is_duplicate("evt-1") is True

    def test_tracks_duplicate_count(self):
        dd = DuplicateDetector()
        dd.is_duplicate("evt-1")
        dd.is_duplicate("evt-1")
        dd.is_duplicate("evt-1")
        assert dd.duplicate_count == 2

    def test_seen_count(self):
        dd = DuplicateDetector()
        dd.is_duplicate("evt-a")
        dd.is_duplicate("evt-b")
        dd.is_duplicate("evt-c")
        assert dd.seen_count == 3

    def test_clears_when_full(self):
        dd = DuplicateDetector(max_ids=3)
        dd.is_duplicate("evt-1")
        dd.is_duplicate("evt-2")
        dd.is_duplicate("evt-3")
        dd.is_duplicate("evt-4")  # triggers clear
        assert dd.seen_count <= 3


# ---------------------------------------------------------------------------
# FailureLog
# ---------------------------------------------------------------------------
class TestFailureLog:
    def test_records_incident(self):
        fl = FailureLog()
        fl.record(FailureMode.REDIS_OFFLINE, "No connection")
        assert fl.total() == 1
        assert fl.counts()["redis_offline"] == 1

    def test_multiple_modes(self):
        fl = FailureLog()
        fl.record(FailureMode.REDIS_OFFLINE, "x")
        fl.record(FailureMode.REDIS_OFFLINE, "y")
        fl.record(FailureMode.MALFORMED_EVENT, "z")
        assert fl.total() == 3
        counts = fl.counts()
        assert counts["redis_offline"] == 2
        assert counts["malformed_event"] == 1

    def test_recent_returns_list(self):
        fl = FailureLog()
        fl.record(FailureMode.TIMEOUT, "timeout")
        recent = fl.recent(n=5)
        assert len(recent) == 1
        assert recent[0]["mode"] == "timeout"

    def test_ring_buffer_cap(self):
        fl = FailureLog(max_entries=3)
        for i in range(10):
            fl.record(FailureMode.MALFORMED_EVENT, f"error {i}")
        assert len(fl.recent(n=20)) == 3


# ---------------------------------------------------------------------------
# FAILURE_STRATEGY_MAP
# ---------------------------------------------------------------------------
class TestFailureStrategyMap:
    def test_all_modes_have_strategy(self):
        for mode in FailureMode:
            assert mode in FAILURE_STRATEGY_MAP

    def test_redis_offline_uses_reconnect(self):
        assert FAILURE_STRATEGY_MAP[FailureMode.REDIS_OFFLINE] == RecoveryStrategy.RECONNECT_BACKOFF

    def test_malformed_uses_log_and_skip(self):
        assert FAILURE_STRATEGY_MAP[FailureMode.MALFORMED_EVENT] == RecoveryStrategy.LOG_AND_SKIP

    def test_unknown_source_uses_accept(self):
        assert FAILURE_STRATEGY_MAP[FailureMode.UNKNOWN_SOURCE] == RecoveryStrategy.ACCEPT_WITH_BADGE

    def test_duplicate_uses_deduplicate(self):
        assert FAILURE_STRATEGY_MAP[FailureMode.DUPLICATE_EVENT] == RecoveryStrategy.DEDUPLICATE

    def test_timeout_uses_graceful_degrade(self):
        assert FAILURE_STRATEGY_MAP[FailureMode.TIMEOUT] == RecoveryStrategy.GRACEFUL_DEGRADE


# ---------------------------------------------------------------------------
# SafeMessageHandler
# ---------------------------------------------------------------------------
class TestSafeMessageHandler:
    def _valid_event(self, **overrides):
        event = {
            "event_id": "evt-test",
            "type": "system.heartbeat",
            "event_type": "system.heartbeat",
            "timestamp": "2026-05-19T14:30:00+00:00",
            "source": {"service": "kratos-mission-control", "version": "0.12.0"},
            "severity": "info",
            "status": "ok",
            "payload": {},
        }
        event.update(overrides)
        return event

    def test_handles_valid_event(self):
        processed = []
        handler = SafeMessageHandler(on_event=lambda e: processed.append(e))
        result = handler.handle(self._valid_event())
        assert result is True
        assert len(processed) == 1

    def test_rejects_non_dict(self):
        processed = []
        handler = SafeMessageHandler(on_event=lambda e: processed.append(e))
        result = handler.handle("not a dict")
        assert result is False
        assert len(processed) == 0

    def test_rejects_malformed_event(self):
        processed = []
        handler = SafeMessageHandler(on_event=lambda e: processed.append(e))
        result = handler.handle({"event_id": "evt-1"})  # missing required fields
        assert result is False
        assert len(processed) == 0

    def test_detects_duplicates(self):
        processed = []
        handler = SafeMessageHandler(on_event=lambda e: processed.append(e))
        event = self._valid_event()
        assert handler.handle(event) is True
        assert handler.handle(event) is False  # duplicate
        assert len(processed) == 1

    def test_accepts_unknown_source(self):
        processed = []
        handler = SafeMessageHandler(on_event=lambda e: processed.append(e))
        event = self._valid_event(
            source={"service": "mystery", "version": "0.1"}
        )
        result = handler.handle(event)
        assert result is True
        assert len(processed) == 1

    def test_skips_subscribe_messages(self):
        processed = []
        handler = SafeMessageHandler(on_event=lambda e: processed.append(e))
        result = handler.handle({"type": "subscribe", "channel": "test"})
        assert result is False
        assert len(processed) == 0

    def test_stats_tracks_counts(self):
        handler = SafeMessageHandler(on_event=lambda e: None)
        handler.handle(self._valid_event(event_id="evt-a"))
        handler.handle(self._valid_event(event_id="evt-b"))
        handler.handle("not json")  # failure
        stats = handler.stats()
        assert stats["events_received"] == 3
        assert stats["failure_total"] >= 1

    def test_handler_exception_is_caught(self):
        def bad_handler(event):
            raise RuntimeError("boom")

        handler = SafeMessageHandler(on_event=bad_handler)
        event = self._valid_event()
        result = handler.handle(event)
        assert result is False
        assert handler.stats()["failure_total"] == 1
