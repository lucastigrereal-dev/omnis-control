"""W167 — Tests for KratosEventStream."""
import pytest
from src.kratos_bridge.event_stream import (
    EventType,
    KratosEventStream,
    OmnisEvent,
    Subscription,
)


def _evt(etype: EventType = EventType.SYSTEM_STATUS, tags: list[str] | None = None) -> OmnisEvent:
    return OmnisEvent(event_type=etype, tags=tags or [])


# ---------------------------------------------------------------------------
# OmnisEvent
# ---------------------------------------------------------------------------

def test_event_defaults():
    e = OmnisEvent()
    assert e.source == "omnis"
    assert e.event_type == EventType.SYSTEM_STATUS


def test_event_round_trip():
    e = OmnisEvent.wave_completed("W167", 27)
    e2 = OmnisEvent.from_dict(e.to_dict())
    assert e2.event_type == EventType.WAVE_COMPLETED
    assert e2.payload["wave"] == "W167"
    assert e2.payload["tests"] == 27


def test_wave_completed_factory():
    e = OmnisEvent.wave_completed("W165", 31)
    assert e.event_type == EventType.WAVE_COMPLETED
    assert "wave" in e.tags


def test_test_result_passed():
    e = OmnisEvent.test_result(passed=True, count=22)
    assert e.event_type == EventType.TEST_PASSED


def test_test_result_failed():
    e = OmnisEvent.test_result(passed=False, count=1)
    assert e.event_type == EventType.TEST_FAILED


def test_metric_updated_factory():
    e = OmnisEvent.metric_updated("tests", 185.0)
    assert e.event_type == EventType.METRIC_UPDATED
    assert e.payload["value"] == 185.0


def test_alert_raised_factory():
    e = OmnisEvent.alert_raised("Something broke")
    assert e.event_type == EventType.ALERT_RAISED
    assert "alert" in e.tags


def test_event_unique_ids():
    e1 = OmnisEvent()
    e2 = OmnisEvent()
    assert e1.event_id != e2.event_id


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------

def test_subscription_matches_all_when_empty():
    sub = Subscription()
    assert sub.matches(_evt(EventType.ALERT_RAISED))


def test_subscription_type_filter():
    sub = Subscription(event_types=[EventType.ALERT_RAISED])
    assert sub.matches(_evt(EventType.ALERT_RAISED))
    assert not sub.matches(_evt(EventType.METRIC_UPDATED))


def test_subscription_tag_filter():
    sub = Subscription(tags=["alert"])
    assert sub.matches(OmnisEvent(tags=["alert"]))
    assert not sub.matches(OmnisEvent(tags=["wave"]))


def test_subscription_inactive_no_match():
    sub = Subscription(active=False)
    assert not sub.matches(_evt())


# ---------------------------------------------------------------------------
# Emit
# ---------------------------------------------------------------------------

def test_emit_records_event():
    stream = KratosEventStream(dry_run=True)
    stream.emit(_evt())
    assert len(stream.replay()) == 1


def test_emit_returns_handler_count():
    stream = KratosEventStream(dry_run=True)
    stream.subscribe(lambda e: None, event_types=[EventType.SYSTEM_STATUS])
    stream.subscribe(lambda e: None)
    count = stream.emit(_evt(EventType.SYSTEM_STATUS))
    assert count == 2


def test_emit_dry_run_does_not_call_handler():
    stream = KratosEventStream(dry_run=True)
    called = []
    stream.subscribe(lambda e: called.append(e))
    stream.emit(_evt())
    assert called == []  # dry_run: counted but not called


def test_emit_not_dry_run_calls_handler():
    stream = KratosEventStream(dry_run=False)
    called = []
    stream.subscribe(lambda e: called.append(e))
    stream.emit(_evt())
    assert len(called) == 1


def test_emit_many():
    stream = KratosEventStream(dry_run=True)
    events = [_evt(), OmnisEvent.wave_completed("W1", 10), OmnisEvent.alert_raised("x")]
    counts = stream.emit_many(events)
    assert len(counts) == 3
    assert len(stream.replay()) == 3


# ---------------------------------------------------------------------------
# Subscribe / unsubscribe
# ---------------------------------------------------------------------------

def test_subscribe_returns_subscription():
    stream = KratosEventStream(dry_run=True)
    sub = stream.subscribe(lambda e: None)
    assert isinstance(sub, Subscription)
    assert sub.active


def test_unsubscribe_deactivates():
    stream = KratosEventStream(dry_run=True)
    sub = stream.subscribe(lambda e: None)
    assert stream.unsubscribe(sub.sub_id)
    assert not sub.active


def test_unsubscribe_missing():
    stream = KratosEventStream(dry_run=True)
    assert not stream.unsubscribe("nonexistent")


def test_inactive_sub_not_counted():
    stream = KratosEventStream(dry_run=True)
    sub = stream.subscribe(lambda e: None)
    stream.unsubscribe(sub.sub_id)
    count = stream.emit(_evt())
    assert count == 0


# ---------------------------------------------------------------------------
# Replay / latest
# ---------------------------------------------------------------------------

def test_replay_all():
    stream = KratosEventStream(dry_run=True)
    stream.emit(_evt(EventType.WAVE_COMPLETED))
    stream.emit(_evt(EventType.ALERT_RAISED))
    assert len(stream.replay()) == 2


def test_replay_by_type():
    stream = KratosEventStream(dry_run=True)
    stream.emit(_evt(EventType.WAVE_COMPLETED))
    stream.emit(_evt(EventType.ALERT_RAISED))
    stream.emit(_evt(EventType.WAVE_COMPLETED))
    results = stream.replay(EventType.WAVE_COMPLETED)
    assert len(results) == 2


def test_latest():
    stream = KratosEventStream(dry_run=True)
    for _ in range(15):
        stream.emit(_evt())
    assert len(stream.latest(10)) == 10


def test_clear():
    stream = KratosEventStream(dry_run=True)
    stream.emit(_evt())
    stream.clear()
    assert stream.replay() == []


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def test_stats_empty():
    stream = KratosEventStream(dry_run=True)
    s = stream.stats()
    assert s["total_events"] == 0
    assert s["active_subscriptions"] == 0
    assert s["dry_run"] is True


def test_stats_after_emit():
    stream = KratosEventStream(dry_run=True)
    stream.subscribe(lambda e: None)
    stream.emit(OmnisEvent.wave_completed("W1", 5))
    stream.emit(OmnisEvent.alert_raised("x"))
    s = stream.stats()
    assert s["total_events"] == 2
    assert s["active_subscriptions"] == 1
    assert "WAVE_COMPLETED" in s["by_type"]
    assert "ALERT_RAISED" in s["by_type"]
