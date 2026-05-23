"""RuntimeBridge — conecta ExecutionGraph StepRun ao ExecutionQueue."""
from __future__ import annotations

from src.execution_graph.models import StepRun, StepRunLog, StepStatus
from src.execution_queue.models import QueueItem, QueueItemStatus
from src.execution_queue.queue import ExecutionQueue
from src.runtime_bridge.models import BridgeResult, _SKIP_STATUSES, map_step_status
from src.runtime_bridge.errors import BridgeMappingError


def _final_logs(step_run: StepRun) -> list[StepRunLog]:
    """Extract the final log for each step_id from a StepRun.

    The last log entry per step_id wins. Non-final statuses (pending, ready)
    are excluded. Running is kept as fallback only if no final outcome exists.
    """
    step_final: dict[str, StepRunLog] = {}

    for log in step_run.logs:
        if not log.step_id:
            # blocked() creates empty step_id — keep as-is
            step_final[log.message] = log
            continue
        if log.status in _SKIP_STATUSES and log.status != StepStatus.RUNNING.value:
            continue
        if log.status == StepStatus.RUNNING.value:
            # Only keep running if no final status seen yet
            if log.step_id not in step_final:
                step_final[log.step_id] = log
        else:
            # Final status (done, failed, skipped) — always overwrite
            step_final[log.step_id] = log

    return list(step_final.values())


class RuntimeBridge:
    """Ponte entre ExecutionGraph e ExecutionQueue.

    Injeta ExecutionQueue no construtor. Nunca instancia queue internamente.
    """

    def __init__(self, queue: ExecutionQueue, dry_run: bool = True) -> None:
        self.queue = queue
        self.dry_run = dry_run

    def bridge(
        self,
        step_run: StepRun,
        *,
        risk_level: str = "LOW",
        requires_approval: bool = False,
    ) -> BridgeResult:
        """Convert a StepRun into QueueItems. No side effects on queue."""
        result = BridgeResult(graph_run_id=step_run.graph_run_id)

        if not step_run.logs:
            return result

        # Handle blocked runs — the single log has empty step_id
        if step_run.status == "blocked_pending_approval":
            item = QueueItem(
                contract_id=step_run.graph_id,
                title=step_run.request[:100],
                risk_level=risk_level,
                requires_approval=True,
                dry_run_required=self.dry_run,
                status=QueueItemStatus.BLOCKED,
                result=step_run.logs[0].message if step_run.logs else "",
            )
            result.queue_items.append(item)
            result.mapping[step_run.graph_id] = item.item_id
            result.items_blocked += 1
            return result

        for log in _final_logs(step_run):
            if log.status in (StepStatus.RUNNING.value, StepStatus.PENDING.value, StepStatus.READY.value):
                continue

            try:
                qstatus = map_step_status(log.status)
            except (BridgeMappingError, ValueError) as e:
                result.errors.append(str(e))
                continue

            item = QueueItem(
                contract_id=step_run.graph_id,
                title=log.message,
                risk_level=risk_level,
                requires_approval=requires_approval,
                dry_run_required=self.dry_run,
                status=qstatus,
            )

            if log.status == StepStatus.FAILED.value:
                item.errors.append(log.message)
            if log.status == StepStatus.SKIPPED.value:
                item.errors.append(log.message)

            result.queue_items.append(item)
            result.mapping[log.step_id] = item.item_id

            if qstatus == QueueItemStatus.BLOCKED:
                result.items_blocked += 1
            elif qstatus == QueueItemStatus.READY:
                result.items_ready += 1

        return result

    def bridge_and_validate(self, step_run: StepRun, **kw) -> BridgeResult:
        """Bridge then push items through the queue validation pipeline."""
        result = self.bridge(step_run, **kw)
        result.items_ready = 0
        result.items_blocked = 0
        for item in result.queue_items:
            if item.status in (QueueItemStatus.BLOCKED, QueueItemStatus.FAILED):
                result.items_blocked += 1
                continue
            # Reset to QUEUED so the queue's state machine can drive transitions
            item.status = QueueItemStatus.QUEUED
            self.queue.enqueue(item)
            self.queue.validate(item)
            if item.status == QueueItemStatus.READY:
                result.items_ready += 1
            elif item.status == QueueItemStatus.BLOCKED:
                result.items_blocked += 1
        return result

    def bridge_and_run(self, step_run: StepRun, **kw) -> BridgeResult:
        """Bridge, then run each item through the queue.

        Respects dry_run: when True, only validates (via bridge_and_validate).
        When False, sets items to READY and runs them through the queue directly,
        bypassing the validate pipeline (since the bridge already mapped the status).
        """
        if self.dry_run:
            return self.bridge_and_validate(step_run, **kw)

        # Non-dry-run path: bridge → READY → enqueue → run
        result = self.bridge(step_run, **kw)
        result.items_ready = 0
        for item in result.queue_items:
            if item.status == QueueItemStatus.BLOCKED:
                continue
            item.status = QueueItemStatus.READY
            self.queue.enqueue(item)
            result.items_ready += 1
        for item in result.queue_items:
            if item.status == QueueItemStatus.READY:
                self.queue.run(item)
        return result
