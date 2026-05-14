import pytest
from src.execution_queue.models import QueueItem, QueueItemStatus, QueueResult
from src.execution_queue.queue import ExecutionQueue
from src.execution_queue.runner import QueueRunner


class TestQueueRunner:
    @pytest.fixture
    def queue(self):
        return ExecutionQueue(dry_run=True)

    @pytest.fixture
    def runner(self, queue):
        return QueueRunner(queue, dry_run=True)

    def test_process_low_risk_dry_run_required(self, runner):
        item = QueueItem(
            title="Test",
            risk_level="LOW",
            dry_run_required=True,
            requires_approval=False,
        )
        runner.queue.enqueue(item)
        result = runner.process(item)
        assert result.status == QueueItemStatus.DRY_RUN

    def test_process_ready_item_runs(self, runner):
        item = QueueItem(
            title="Test",
            risk_level="LOW",
            dry_run_required=False,
            requires_approval=False,
            status=QueueItemStatus.READY,
        )
        runner.queue.items.append(item)
        result = runner.process(item)
        assert result.status == QueueItemStatus.DONE

    def test_process_high_risk_no_approval_raises(self, runner):
        item = QueueItem(
            title="Deploy",
            risk_level="HIGH",
            requires_approval=False,
            dry_run_required=False,
            status=QueueItemStatus.READY,
        )
        runner.queue.items.append(item)
        from src.execution_queue.errors import QueueBlockedError
        with pytest.raises(QueueBlockedError):
            runner.process(item)

    def test_process_all(self, runner):
        for i in range(3):
            item = QueueItem(
                title=f"Item {i}",
                risk_level="LOW",
                dry_run_required=True,
                requires_approval=False,
            )
            runner.queue.enqueue(item)
        results = runner.process_all()
        assert len(results) == 3
