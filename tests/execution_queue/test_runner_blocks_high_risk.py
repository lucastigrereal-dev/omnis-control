import pytest
from src.execution_queue.models import QueueItem, QueueItemStatus
from src.execution_queue.queue import ExecutionQueue
from src.execution_queue.runner import QueueRunner
from src.execution_queue.errors import QueueBlockedError


class TestRunnerBlocksHighRisk:
    @pytest.fixture
    def queue(self):
        return ExecutionQueue(dry_run=True)

    @pytest.fixture
    def runner(self, queue):
        return QueueRunner(queue, dry_run=True)

    def test_high_risk_no_approval_blocked(self, runner):
        item = QueueItem(
            title="Delete DB",
            risk_level="CRITICAL",
            requires_approval=False,
            dry_run_required=False,
            status=QueueItemStatus.READY,
        )
        runner.queue.items.append(item)
        with pytest.raises(QueueBlockedError, match="cannot be run"):
            runner.process(item)

    def test_high_risk_with_approval_but_not_ready_blocked(self, runner):
        item = QueueItem(
            title="Deploy",
            risk_level="HIGH",
            requires_approval=True,
            dry_run_required=False,
            status=QueueItemStatus.WAITING_APPROVAL,
        )
        runner.queue.items.append(item)
        with pytest.raises(QueueBlockedError, match="needs approval"):
            runner.process(item)

    def test_enqueue_high_risk_no_approval_blocks_immediately(self, queue):
        item = QueueItem(
            title="Delete All",
            risk_level="CRITICAL",
            requires_approval=False,
        )
        queue.enqueue(item)
        assert item.status == QueueItemStatus.BLOCKED
        assert any("approval" in e.lower() for e in item.errors)

    def test_high_risk_cannot_approve_from_wrong_state(self, queue):
        item = QueueItem(
            title="Deploy",
            risk_level="HIGH",
            requires_approval=True,
            status=QueueItemStatus.QUEUED,
        )
        queue.items.append(item)
        with pytest.raises(QueueBlockedError):
            queue.approve(item)
