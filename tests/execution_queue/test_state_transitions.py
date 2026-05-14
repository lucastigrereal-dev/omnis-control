import pytest
from src.execution_queue.models import QueueItem, QueueItemStatus
from src.execution_queue.state import StateMachine
from src.execution_queue.errors import QueueStateError


class TestStateMachine:
    @pytest.fixture
    def sm(self):
        return StateMachine(dry_run=True)

    def test_queued_to_validating(self, sm):
        item = QueueItem(status=QueueItemStatus.QUEUED)
        sm.transition(item, QueueItemStatus.VALIDATING)
        assert item.status == QueueItemStatus.VALIDATING

    def test_queued_to_blocked(self, sm):
        item = QueueItem(status=QueueItemStatus.QUEUED)
        sm.transition(item, QueueItemStatus.BLOCKED)
        assert item.status == QueueItemStatus.BLOCKED

    def test_valid_transitions_list(self):
        for current, targets in [
            (QueueItemStatus.QUEUED, [QueueItemStatus.VALIDATING, QueueItemStatus.BLOCKED]),
            (QueueItemStatus.READY, [QueueItemStatus.RUNNING]),
            (QueueItemStatus.RUNNING, [QueueItemStatus.DONE, QueueItemStatus.FAILED]),
            (QueueItemStatus.DONE, []),
            (QueueItemStatus.FAILED, []),
            (QueueItemStatus.BLOCKED, []),
        ]:
            item = QueueItem(status=current)
            sm = StateMachine()
            for target in targets:
                assert sm.can_transition(item, target) is True

    def test_invalid_transition_raises(self, sm):
        item = QueueItem(status=QueueItemStatus.DONE)
        with pytest.raises(QueueStateError, match="Cannot transition"):
            sm.transition(item, QueueItemStatus.RUNNING)

    def test_blocked_is_terminal(self, sm):
        item = QueueItem(status=QueueItemStatus.BLOCKED)
        for target in QueueItemStatus:
            if target != QueueItemStatus.BLOCKED:
                assert sm.can_transition(item, target) is False

    def test_done_is_terminal(self, sm):
        item = QueueItem(status=QueueItemStatus.DONE)
        for target in QueueItemStatus:
            if target != QueueItemStatus.DONE:
                assert sm.can_transition(item, target) is False

    def test_full_happy_path(self, sm):
        item = QueueItem(title="Happy Path")
        sm.transition(item, QueueItemStatus.VALIDATING)  # from QUEUED
        sm.transition(item, QueueItemStatus.DRY_RUN)
        sm.transition(item, QueueItemStatus.READY)
        sm.transition(item, QueueItemStatus.RUNNING)
        sm.transition(item, QueueItemStatus.DONE)
        assert item.status == QueueItemStatus.DONE

    def test_waiting_approval_to_ready(self, sm):
        item = QueueItem(status=QueueItemStatus.WAITING_APPROVAL)
        sm.transition(item, QueueItemStatus.READY)
        assert item.status == QueueItemStatus.READY
