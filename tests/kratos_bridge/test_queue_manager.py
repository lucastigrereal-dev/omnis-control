"""W165 — Tests for PayloadQueueManager."""
import json
import pytest
from src.kratos_bridge.queue_manager import PayloadQueueManager, QueueEntry
from src.kratos_bridge.models import KratosPayload, PayloadPriority, PayloadStatus, PayloadType


def _p(priority: PayloadPriority = PayloadPriority.NORMAL, ptype: PayloadType = PayloadType.STATUS_UPDATE) -> KratosPayload:
    return KratosPayload(payload_type=ptype, priority=priority, title="test")


def _mgr(**kwargs) -> PayloadQueueManager:
    return PayloadQueueManager(**kwargs)


# ---------------------------------------------------------------------------
# QueueEntry
# ---------------------------------------------------------------------------

def test_entry_defaults():
    e = QueueEntry(payload=_p())
    assert e.status == "QUEUED"
    assert e.attempts == 0
    assert e.is_pending


def test_entry_exhausted():
    e = QueueEntry(payload=_p(), attempts=3, max_retries=3)
    assert e.exhausted


def test_entry_not_exhausted():
    e = QueueEntry(payload=_p(), attempts=2, max_retries=3)
    assert not e.exhausted


def test_entry_round_trip():
    e = QueueEntry(payload=_p(), attempts=1, last_error="timeout")
    e2 = QueueEntry.from_dict(e.to_dict())
    assert e2.entry_id == e.entry_id
    assert e2.attempts == 1
    assert e2.last_error == "timeout"


def test_entry_is_delivered():
    e = QueueEntry(payload=_p(), status="DELIVERED")
    assert e.is_delivered
    assert not e.is_pending


def test_entry_is_failed():
    e = QueueEntry(payload=_p(), status="FAILED")
    assert e.is_failed


# ---------------------------------------------------------------------------
# Enqueue
# ---------------------------------------------------------------------------

def test_enqueue_increases_size():
    mgr = _mgr()
    mgr.enqueue(_p())
    assert mgr.size() == 1


def test_enqueue_many():
    mgr = _mgr()
    mgr.enqueue_many([_p(), _p(), _p()])
    assert mgr.size() == 3


def test_enqueue_returns_entry():
    mgr = _mgr()
    e = mgr.enqueue(_p())
    assert isinstance(e, QueueEntry)
    assert e.status == "QUEUED"


# ---------------------------------------------------------------------------
# Peek and pop
# ---------------------------------------------------------------------------

def test_peek_returns_pending():
    mgr = _mgr()
    mgr.enqueue(_p())
    mgr.enqueue(_p())
    peeked = mgr.peek(2)
    assert len(peeked) == 2


def test_peek_empty_queue():
    mgr = _mgr()
    assert mgr.peek() == []


def test_pop_returns_highest_priority():
    mgr = _mgr()
    mgr.enqueue(_p(PayloadPriority.LOW))
    mgr.enqueue(_p(PayloadPriority.CRITICAL))
    mgr.enqueue(_p(PayloadPriority.NORMAL))
    entry = mgr.pop()
    assert entry.payload.priority == PayloadPriority.CRITICAL


def test_pop_empty():
    mgr = _mgr()
    assert mgr.pop() is None


# ---------------------------------------------------------------------------
# Mark delivered
# ---------------------------------------------------------------------------

def test_mark_delivered():
    mgr = _mgr()
    e = mgr.enqueue(_p())
    assert mgr.mark_delivered(e.entry_id)
    assert e.status == "DELIVERED"
    assert mgr.size() == 0


def test_mark_delivered_missing():
    mgr = _mgr()
    assert not mgr.mark_delivered("nonexistent")


# ---------------------------------------------------------------------------
# Mark failed / retry
# ---------------------------------------------------------------------------

def test_mark_failed_increments_attempts():
    mgr = _mgr(max_retries=3)
    e = mgr.enqueue(_p())
    mgr.mark_failed(e.entry_id, "timeout")
    assert e.attempts == 1
    assert e.status == "RETRY"
    assert e.last_error == "timeout"


def test_mark_failed_exhausts():
    mgr = _mgr(max_retries=2)
    e = mgr.enqueue(_p())
    mgr.mark_failed(e.entry_id)
    mgr.mark_failed(e.entry_id)
    assert e.status == "FAILED"
    assert e.exhausted


def test_failed_not_in_pending():
    mgr = _mgr(max_retries=1)
    e = mgr.enqueue(_p())
    mgr.mark_failed(e.entry_id)
    assert e not in mgr.pending()


def test_retry_still_in_pending():
    mgr = _mgr(max_retries=3)
    e = mgr.enqueue(_p())
    mgr.mark_failed(e.entry_id)
    assert e in mgr.pending()


# ---------------------------------------------------------------------------
# Mark dropped
# ---------------------------------------------------------------------------

def test_mark_dropped():
    mgr = _mgr()
    e = mgr.enqueue(_p())
    assert mgr.mark_dropped(e.entry_id, "rate_limited")
    assert e.status == "DROPPED"
    assert mgr.size() == 0


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------

def test_delivered_list():
    mgr = _mgr()
    e = mgr.enqueue(_p())
    mgr.mark_delivered(e.entry_id)
    assert e in mgr.delivered()


def test_failed_list():
    mgr = _mgr(max_retries=1)
    e = mgr.enqueue(_p())
    mgr.mark_failed(e.entry_id)
    assert e in mgr.failed()


def test_all_entries():
    mgr = _mgr()
    mgr.enqueue(_p())
    mgr.enqueue(_p())
    assert len(mgr.all_entries()) == 2


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------

def test_clear_delivered():
    mgr = _mgr()
    e1 = mgr.enqueue(_p())
    e2 = mgr.enqueue(_p())
    mgr.mark_delivered(e1.entry_id)
    removed = mgr.clear_delivered()
    assert removed == 1
    assert mgr.size() == 1


def test_clear_all():
    mgr = _mgr()
    mgr.enqueue_many([_p(), _p()])
    mgr.clear_all()
    assert mgr.size() == 0


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def test_stats_empty():
    mgr = _mgr()
    s = mgr.stats()
    assert s["total"] == 0


def test_stats_mixed():
    mgr = _mgr(max_retries=1)
    e1 = mgr.enqueue(_p())
    e2 = mgr.enqueue(_p())
    e3 = mgr.enqueue(_p())
    mgr.mark_delivered(e1.entry_id)
    mgr.mark_failed(e2.entry_id)
    s = mgr.stats()
    assert s["total"] == 3
    assert s["delivered"] == 1
    assert s["failed"] == 1
    assert s["pending"] == 1


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_persist_and_reload(tmp_path):
    path = tmp_path / "queue.jsonl"
    mgr = PayloadQueueManager(queue_path=path)
    mgr.enqueue(_p())
    mgr.enqueue(_p(PayloadPriority.HIGH))

    mgr2 = PayloadQueueManager(queue_path=path)
    assert mgr2.size() == 2


def test_persist_preserves_status(tmp_path):
    path = tmp_path / "queue.jsonl"
    mgr = PayloadQueueManager(queue_path=path)
    e = mgr.enqueue(_p())
    mgr.mark_delivered(e.entry_id)

    mgr2 = PayloadQueueManager(queue_path=path)
    delivered = mgr2.delivered()
    assert len(delivered) == 1


def test_reload_method(tmp_path):
    path = tmp_path / "queue.jsonl"
    mgr = PayloadQueueManager(queue_path=path)
    mgr.enqueue(_p())
    mgr.clear_all()
    mgr.reload()
    assert mgr.size() == 0  # file was cleared


def test_in_memory_no_path():
    mgr = PayloadQueueManager()
    mgr.enqueue(_p())
    assert mgr.size() == 1
