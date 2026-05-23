"""Tests for Autonomous Local Backlog."""

import tempfile
from pathlib import Path

import pytest

from src.backlog.models import BacklogItem, BacklogQueue, ItemStatus, ItemType
from src.backlog.queue import BacklogManager


@pytest.fixture
def manager():
    with tempfile.TemporaryDirectory() as tmp:
        yield BacklogManager(data_dir=Path(tmp))


class TestBacklogModels:
    def test_item_to_dict_round_trip(self):
        item = BacklogItem(
            item_id="abc123", item_type=ItemType.MISSION,
            title="Test mission", priority=2, tags=["urgent"],
        )
        d = item.to_dict()
        restored = BacklogItem.from_dict(d)
        assert restored.item_id == "abc123"
        assert restored.item_type == ItemType.MISSION
        assert restored.title == "Test mission"
        assert restored.priority == 2
        assert restored.tags == ["urgent"]
        assert restored.status == ItemStatus.PENDING

    def test_item_enum_values_serialized(self):
        item = BacklogItem(item_id="x", item_type=ItemType.REVIEW, title="R")
        d = item.to_dict()
        assert d["item_type"] == "review"
        assert d["status"] == "pending"

    def test_queue_next_returns_highest_priority(self):
        items = [
            BacklogItem(item_id="1", item_type=ItemType.MISSION, title="Low", priority=5),
            BacklogItem(item_id="2", item_type=ItemType.MISSION, title="High", priority=1),
            BacklogItem(item_id="3", item_type=ItemType.MISSION, title="Mid", priority=3),
        ]
        q = BacklogQueue(name="test", items=items)
        nxt = q.next()
        assert nxt is not None
        assert nxt.item_id == "2"
        assert nxt.priority == 1

    def test_queue_next_skips_non_pending(self):
        items = [
            BacklogItem(item_id="1", item_type=ItemType.MISSION, title="Done",
                        priority=1, status=ItemStatus.COMPLETED),
            BacklogItem(item_id="2", item_type=ItemType.MISSION, title="Pending",
                        priority=5, status=ItemStatus.PENDING),
        ]
        q = BacklogQueue(name="test", items=items)
        nxt = q.next()
        assert nxt is not None
        assert nxt.item_id == "2"

    def test_queue_next_returns_none_when_empty(self):
        q = BacklogQueue(name="test")
        assert q.next() is None

    def test_queue_to_dict_from_dict(self):
        items = [BacklogItem(item_id="1", item_type=ItemType.ASSET, title="Asset")]
        q = BacklogQueue(name="test", items=items)
        d = q.to_dict()
        restored = BacklogQueue.from_dict(d)
        assert restored.name == "test"
        assert len(restored.items) == 1
        assert restored.items[0].item_id == "1"


class TestBacklogManager:
    def test_enqueue_adds_item(self, manager):
        item = manager.enqueue(ItemType.MISSION, "Mission 1", "Desc", priority=2, tags=["ops"])
        assert item.item_id
        assert item.title == "Mission 1"
        assert item.priority == 2
        assert item.status == ItemStatus.PENDING

    def test_enqueue_persists(self, manager):
        item = manager.enqueue(ItemType.REVIEW, "Review")
        # Create new manager loading same file
        mgr2 = BacklogManager(data_dir=manager.data_dir)
        restored = mgr2.get(item.item_id)
        assert restored is not None
        assert restored.title == "Review"

    def test_dequeue_returns_highest_priority(self, manager):
        manager.enqueue(ItemType.MISSION, "Low", priority=5)
        manager.enqueue(ItemType.MISSION, "High", priority=1)
        item = manager.dequeue()
        assert item is not None
        assert item.title == "High"
        assert item.status == ItemStatus.IN_PROGRESS

    def test_dequeue_none_when_empty(self, manager):
        assert manager.dequeue() is None

    def test_dequeue_none_when_all_done(self, manager):
        item = manager.enqueue(ItemType.MISSION, "Done")
        dequeued = manager.dequeue()
        assert dequeued is not None
        manager.complete(dequeued.item_id)
        assert dequeued.status == ItemStatus.COMPLETED
        assert manager.dequeue() is None

    def test_complete_marks_done(self, manager):
        item = manager.enqueue(ItemType.MISSION, "Task")
        result = manager.complete(item.item_id)
        assert result is not None
        assert result.status == ItemStatus.COMPLETED

    def test_cancel_marks_cancelled(self, manager):
        item = manager.enqueue(ItemType.APPROVAL, "Approval")
        result = manager.cancel(item.item_id)
        assert result.status == ItemStatus.CANCELLED

    def test_block_unblock(self, manager):
        item = manager.enqueue(ItemType.ASSET, "Asset")
        manager.block(item.item_id, reason="Missing deps")
        blocked = manager.get(item.item_id)
        assert blocked.status == ItemStatus.BLOCKED
        assert blocked.metadata["block_reason"] == "Missing deps"

        manager.unblock(item.item_id)
        unblocked = manager.get(item.item_id)
        assert unblocked.status == ItemStatus.PENDING
        assert "block_reason" not in unblocked.metadata

    def test_list_by_status(self, manager):
        manager.enqueue(ItemType.MISSION, "M1")
        manager.enqueue(ItemType.REVIEW, "R1")
        item = manager.dequeue()  # Now IN_PROGRESS
        pending = manager.list_by_status(ItemStatus.PENDING)
        in_progress = manager.list_by_status(ItemStatus.IN_PROGRESS)
        assert len(pending) >= 1
        assert len(in_progress) == 1

    def test_list_by_type(self, manager):
        manager.enqueue(ItemType.MISSION, "M1")
        manager.enqueue(ItemType.REVIEW, "R1")
        manager.enqueue(ItemType.REVIEW, "R2")
        reviews = manager.list_by_type(ItemType.REVIEW)
        assert len(reviews) == 2

    def test_list_by_tag(self, manager):
        manager.enqueue(ItemType.MISSION, "M1", tags=["urgent", "ops"])
        manager.enqueue(ItemType.MISSION, "M2", tags=["low"])
        assert len(manager.list_by_tag("urgent")) == 1
        assert len(manager.list_by_tag("ops")) == 1
        assert len(manager.list_by_tag("nonexistent")) == 0

    def test_prioritize(self, manager):
        item = manager.enqueue(ItemType.MISSION, "M", priority=3)
        manager.prioritize(item.item_id, 1)
        updated = manager.get(item.item_id)
        assert updated.priority == 1

    def test_prioritize_clamps(self, manager):
        item = manager.enqueue(ItemType.MISSION, "M", priority=3)
        manager.prioritize(item.item_id, 0)
        assert manager.get(item.item_id).priority == 1
        manager.prioritize(item.item_id, 99)
        assert manager.get(item.item_id).priority == 5

    def test_count(self, manager):
        manager.enqueue(ItemType.MISSION, "M1")
        manager.enqueue(ItemType.REVIEW, "R1")
        manager.enqueue(ItemType.APPROVAL, "A1")
        item = manager.dequeue()
        manager.complete(item.item_id)
        c = manager.count()
        assert c["total"] == 3
        assert c["pending"] == 2
        assert c["in_progress"] == 0
        assert c["completed"] == 1

    def test_get_nonexistent(self, manager):
        assert manager.get("no-such-id") is None

    def test_complete_nonexistent(self, manager):
        assert manager.complete("no-such-id") is None

    def test_empty_file_is_handled(self, manager):
        manager.file_path.write_text("", encoding="utf-8")
        mgr2 = BacklogManager(data_dir=manager.data_dir)
        assert mgr2.count()["total"] == 0
