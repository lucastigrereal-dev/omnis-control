from src.execution_queue.models import (
    QueueItem, QueueItemStatus, VALID_TRANSITIONS,
)
from src.execution_queue.errors import QueueStateError


class StateMachine:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run

    def can_transition(
        self, item: QueueItem, target: QueueItemStatus
    ) -> bool:
        allowed = VALID_TRANSITIONS.get(item.status, [])
        return target in allowed

    def transition(self, item: QueueItem, target: QueueItemStatus) -> None:
        if not self.can_transition(item, target):
            raise QueueStateError(
                f"Cannot transition '{item.item_id}' from "
                f"'{item.status.value}' to '{target.value}'"
            )
        item.status = target
