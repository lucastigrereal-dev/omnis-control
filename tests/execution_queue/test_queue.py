import pytest
from src.execution_queue.models import QueueItem, QueueItemStatus, QueueResult
from src.execution_queue.queue import ExecutionQueue


class TestExecutionQueue:
    @pytest.fixture
    def queue(self):
        return ExecutionQueue(dry_run=True)

    def test_enqueue_low_risk(self, queue):
        item = QueueItem(title="Test", risk_level="LOW")
        queue.enqueue(item)
        assert len(queue.items) == 1
        assert queue.items[0].status == QueueItemStatus.QUEUED

    def test_enqueue_high_risk_no_approval_blocks(self, queue):
        item = QueueItem(
            title="Deploy",
            risk_level="HIGH",
            requires_approval=False,
        )
        queue.enqueue(item)
        assert item.status == QueueItemStatus.BLOCKED

    def test_enqueue_high_risk_with_approval_queues(self, queue):
        item = QueueItem(
            title="Deploy",
            risk_level="HIGH",
            requires_approval=True,
        )
        queue.enqueue(item)
        assert item.status == QueueItemStatus.QUEUED

    def test_validate_low_risk_dry_run(self, queue):
        item = QueueItem(title="Test", risk_level="LOW", dry_run_required=True)
        queue.enqueue(item)
        queue.validate(item)
        assert item.status == QueueItemStatus.DRY_RUN

    def test_validate_requires_approval(self, queue):
        item = QueueItem(
            title="Deploy",
            risk_level="HIGH",
            requires_approval=True,
            dry_run_required=True,
        )
        queue.enqueue(item)
        queue.validate(item)
        assert item.status == QueueItemStatus.WAITING_APPROVAL

    def test_approve_transitions_to_ready(self, queue):
        item = QueueItem(
            title="Deploy",
            risk_level="HIGH",
            requires_approval=True,
            status=QueueItemStatus.WAITING_APPROVAL,
        )
        queue.items.append(item)
        queue.approve(item)
        assert item.status == QueueItemStatus.READY

    def test_run_ready_item(self, queue):
        item = QueueItem(
            title="Test",
            risk_level="LOW",
            requires_approval=False,
            status=QueueItemStatus.READY,
        )
        queue.items.append(item)
        result = queue.run(item)
        assert result.status == QueueItemStatus.DONE
        assert item.status == QueueItemStatus.DONE

    def test_run_high_risk_without_approval_blocks(self, queue):
        item = QueueItem(
            title="Deploy",
            risk_level="HIGH",
            requires_approval=False,
            status=QueueItemStatus.READY,
        )
        queue.items.append(item)
        result = queue.run(item)
        assert result.status == QueueItemStatus.BLOCKED

    def test_get_items_by_status(self, queue):
        for i in range(3):
            item = QueueItem(title=f"Item {i}", risk_level="LOW")
            queue.enqueue(item)
        queue.items[0].status = QueueItemStatus.DONE
        assert len(queue.get_items(QueueItemStatus.QUEUED)) == 2
        assert len(queue.get_items(QueueItemStatus.DONE)) == 1

    def test_pending_count(self, queue):
        item = QueueItem(title="Test", risk_level="LOW")
        queue.enqueue(item)
        assert queue.pending_count() == 1
        item.status = QueueItemStatus.DONE
        assert queue.pending_count() == 0
