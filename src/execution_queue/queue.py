from src.execution_queue.models import (
    QueueItem, QueueItemStatus, QueueResult,
)
from src.execution_queue.state import StateMachine
from src.execution_queue.errors import QueueBlockedError


class ExecutionQueue:

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.items: list[QueueItem] = []
        self.results: list[QueueResult] = []
        self.state = StateMachine(dry_run=dry_run)

    def enqueue(self, item: QueueItem) -> None:
        if item.risk_level.upper() in ("HIGH", "CRITICAL") and \
           not item.requires_approval:
            item.status = QueueItemStatus.BLOCKED
            item.errors.append(
                f"High risk item '{item.item_id}' requires approval"
            )
        self.items.append(item)

    def validate(self, item: QueueItem) -> QueueItem:
        self.state.transition(item, QueueItemStatus.VALIDATING)

        if item.status == QueueItemStatus.BLOCKED:
            return item

        if item.requires_approval and item.status == QueueItemStatus.VALIDATING:
            self.state.transition(item, QueueItemStatus.WAITING_APPROVAL)
            return item

        if item.dry_run_required:
            self.state.transition(item, QueueItemStatus.DRY_RUN)
        else:
            self.state.transition(item, QueueItemStatus.READY)

        return item

    def approve(self, item: QueueItem) -> QueueItem:
        if item.status != QueueItemStatus.WAITING_APPROVAL:
            raise QueueBlockedError(
                f"Item '{item.item_id}' is not waiting approval "
                f"(status: {item.status.value})"
            )
        self.state.transition(item, QueueItemStatus.READY)
        return item

    def block(self, item: QueueItem, reason: str = "") -> QueueItem:
        self.state.transition(item, QueueItemStatus.BLOCKED)
        if reason:
            item.errors.append(reason)
        return item

    def run(self, item: QueueItem) -> QueueResult:
        if item.status not in (QueueItemStatus.READY, QueueItemStatus.RUNNING):
            raise QueueBlockedError(
                f"Item '{item.item_id}' is not ready (status: {item.status.value})"
            )

        if item.risk_level.upper() in ("HIGH", "CRITICAL") and \
           not item.requires_approval:
            self.state.transition(item, QueueItemStatus.BLOCKED)
            item.errors.append("High risk without approval")
            return QueueResult(
                item_id=item.item_id,
                status=QueueItemStatus.BLOCKED,
                errors=item.errors,
            )

        self.state.transition(item, QueueItemStatus.RUNNING)

        result = QueueResult(
            item_id=item.item_id,
            status=QueueItemStatus.DONE,
            output=f"[EXECUTED] Item '{item.title}' completed successfully",
            tests_run=0,
            tests_passed=0,
        )
        self.results.append(result)

        self.state.transition(item, QueueItemStatus.DONE)
        item.result = result.output

        return result

    def get_items(self, status: QueueItemStatus | None = None) -> list[QueueItem]:
        if status:
            return [i for i in self.items if i.status == status]
        return self.items

    def pending_count(self) -> int:
        return len([i for i in self.items if not i.is_terminal])
