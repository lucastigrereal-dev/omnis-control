"""W161 — Tests for KratosDispatcher."""
import pytest
from src.kratos_bridge.dispatcher import KratosDispatcher, DispatchResult
from src.kratos_bridge.models import KratosPayload, PayloadPriority, PayloadStatus, PayloadType


def _payload(ptype: PayloadType = PayloadType.STATUS_UPDATE, priority: PayloadPriority = PayloadPriority.NORMAL) -> KratosPayload:
    return KratosPayload(payload_type=ptype, priority=priority, title="test")


# ---------------------------------------------------------------------------
# Dry-run dispatch
# ---------------------------------------------------------------------------

def test_dispatch_one_dry_run_ok():
    d = KratosDispatcher(dry_run=True)
    result = d.dispatch_one(_payload())
    assert result.ok
    assert result.dry_run is True
    assert result.status == PayloadStatus.SENT.value


def test_dry_run_sets_payload_status():
    d = KratosDispatcher(dry_run=True)
    p = _payload()
    d.dispatch_one(p)
    assert p.status == PayloadStatus.SENT


def test_dry_run_output_has_payload_type():
    d = KratosDispatcher(dry_run=True)
    result = d.dispatch_one(_payload(PayloadType.ALERT))
    assert result.output["payload_type"] == "ALERT"
    assert result.output["dry_run"] is True


# ---------------------------------------------------------------------------
# Enqueue + flush
# ---------------------------------------------------------------------------

def test_enqueue_increases_queue():
    d = KratosDispatcher(dry_run=True)
    d.enqueue(_payload())
    assert d.queue_size() == 1


def test_flush_dispatches_all():
    d = KratosDispatcher(dry_run=True)
    d.enqueue(_payload())
    d.enqueue(_payload())
    results = d.flush()
    assert len(results) == 2
    assert d.queue_size() == 0


def test_flush_priority_order():
    d = KratosDispatcher(dry_run=True)
    d.enqueue(_payload(priority=PayloadPriority.LOW))
    d.enqueue(_payload(priority=PayloadPriority.CRITICAL))
    d.enqueue(_payload(priority=PayloadPriority.NORMAL))
    results = d.flush()
    # CRITICAL must be first
    assert results[0].output["dry_run"] is True
    # All dispatched
    assert len(results) == 3


def test_flush_empty_queue():
    d = KratosDispatcher(dry_run=True)
    results = d.flush()
    assert results == []


# ---------------------------------------------------------------------------
# Handlers (non-dry-run)
# ---------------------------------------------------------------------------

def test_handler_registered_and_called():
    d = KratosDispatcher(dry_run=False)
    called = []

    def handler(p: KratosPayload) -> dict:
        called.append(p.title)
        return {"ok": True, "view": "dashboard"}

    d.register(PayloadType.STATUS_UPDATE, handler)
    result = d.dispatch_one(_payload(PayloadType.STATUS_UPDATE))
    assert result.ok
    assert result.status == PayloadStatus.DELIVERED.value
    assert "test" in called


def test_no_handler_drops_payload():
    d = KratosDispatcher(dry_run=False)
    p = _payload(PayloadType.ALERT)
    result = d.dispatch_one(p)
    assert not result.ok
    assert result.status == PayloadStatus.DROPPED.value
    assert "no_handler_for" in result.error


def test_handler_exception_fails_payload():
    d = KratosDispatcher(dry_run=False)

    def bad_handler(p: KratosPayload) -> dict:
        raise RuntimeError("cockpit unavailable")

    d.register(PayloadType.METRIC, bad_handler)
    p = _payload(PayloadType.METRIC)
    result = d.dispatch_one(p)
    assert not result.ok
    assert result.status == PayloadStatus.FAILED.value
    assert "cockpit unavailable" in result.error


# ---------------------------------------------------------------------------
# History and stats
# ---------------------------------------------------------------------------

def test_history_recorded():
    d = KratosDispatcher(dry_run=True)
    d.dispatch_one(_payload())
    d.dispatch_one(_payload())
    assert len(d.history()) == 2


def test_stats_after_dispatch():
    d = KratosDispatcher(dry_run=True)
    d.dispatch_one(_payload())
    s = d.stats()
    assert s["total_dispatched"] == 1
    assert s["ok"] == 1
    assert s["failed"] == 0
    assert s["queued"] == 0


def test_stats_failed_counted():
    d = KratosDispatcher(dry_run=False)
    d.dispatch_one(_payload(PayloadType.ALERT))  # no handler → dropped (not ok)
    s = d.stats()
    assert s["failed"] == 1


# ---------------------------------------------------------------------------
# DispatchResult round-trip
# ---------------------------------------------------------------------------

def test_dispatch_result_to_dict():
    r = DispatchResult(payload_id="p_001", ok=True, status=PayloadStatus.SENT.value)
    d = r.to_dict()
    assert d["payload_id"] == "p_001"
    assert d["ok"] is True
    assert "result_id" in d
