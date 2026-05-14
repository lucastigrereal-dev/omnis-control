from src.execution_queue.models import QueueItem, QueueItemStatus, QueueResult
from src.execution_queue.queue import ExecutionQueue
from src.execution_queue.errors import QueueBlockedError


class QueueRunner:

    def __init__(self, queue: ExecutionQueue, dry_run: bool = True):
        self.queue = queue
        self.dry_run = dry_run

    def process(self, item: QueueItem) -> QueueResult:
        if item.dry_run_required and item.status == QueueItemStatus.QUEUED:
            self.queue.validate(item)
            if item.requires_approval:
                return QueueResult(
                    item_id=item.item_id,
                    status=QueueItemStatus.WAITING_APPROVAL,
                    output=f"[DRY_RUN] Item '{item.title}' needs approval",
                )

            result = QueueResult(
                item_id=item.item_id,
                status=QueueItemStatus.DRY_RUN,
                output=f"[DRY_RUN] Item '{item.title}' dry-run completed",
                tests_run=0,
                tests_passed=0,
            )
            self.queue.results.append(result)

            if item.status == QueueItemStatus.DRY_RUN:
                self.queue.state.transition(item, QueueItemStatus.READY)
                item.result = result.output

            return result

        if item.risk_level.upper() in ("HIGH", "CRITICAL"):
            if not item.requires_approval:
                raise QueueBlockedError(
                    f"High risk item '{item.item_id}' cannot be run without approval"
                )
            if item.status != QueueItemStatus.READY:
                raise QueueBlockedError(
                    f"Item '{item.item_id}' needs approval before execution "
                    f"(status: {item.status.value})"
                )

        return self.queue.run(item)

    def process_all(self) -> list[QueueResult]:
        results: list[QueueResult] = []
        for item in self.queue.items:
            if not item.is_terminal:
                try:
                    result = self.process(item)
                    results.append(result)
                except QueueBlockedError as e:
                    results.append(QueueResult(
                        item_id=item.item_id,
                        status=QueueItemStatus.BLOCKED,
                        errors=[str(e)],
                    ))
        return results
