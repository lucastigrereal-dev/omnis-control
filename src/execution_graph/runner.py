"""Step Runner Dry-Run — simulate execution of steps in a graph."""
from __future__ import annotations

from datetime import datetime, timezone

from src.execution_graph.models import (
    ExecutionGraph,
    StepNode,
    StepStatus,
    StepRun,
    StepRunLog,
    RUN_STATUS_RUNNING,
    RUN_STATUS_DONE,
    RUN_STATUS_FAILED,
    _make_run_id,
)
from src.execution_graph.errors import ExecutionGraphError


def run_graph_dry(graph: ExecutionGraph, fail_at: str | None = None) -> StepRun:
    """Simulate executing all steps in topological order. No side effects.

    Args:
        graph: The ExecutionGraph to simulate.
        fail_at: Optional step_id — if provided, that step will FAIL instead of DONE.
    """
    if not graph.nodes:
        raise ExecutionGraphError("Cannot run empty graph")

    graph_run_id = _make_run_id()
    started_at = _now()
    logs: list[StepRunLog] = []
    step_states: dict[str, str] = {}

    for step_id in graph.topological_order:
        node = graph.node_map.get(step_id)
        if node is None:
            continue

        # Mark as running
        running_log = StepRunLog(
            step_id=node.step_id,
            role_id=node.role_id,
            status=StepStatus.RUNNING.value,
            message=f"Step '{node.title}' started (role={node.role_id}, est={node.estimated_duration})",
            timestamp=_now(),
        )
        logs.append(running_log)
        step_states[node.step_id] = StepStatus.RUNNING.value

        # Simulate execution — determine outcome
        if fail_at is not None and node.step_id == fail_at:
            status = StepStatus.FAILED
            msg = f"Step '{node.title}' FAILED (injected failure)"
        else:
            status = StepStatus.DONE
            msg = f"Step '{node.title}' completed (output: {node.expected_output})"

        outcome_log = StepRunLog(
            step_id=node.step_id,
            role_id=node.role_id,
            status=status.value,
            message=msg,
            timestamp=_now(),
        )
        logs.append(outcome_log)
        step_states[node.step_id] = status.value

        # If a step failed, mark all downstream as skipped and abort
        if status == StepStatus.FAILED:
            for remaining in graph.topological_order[graph.topological_order.index(step_id) + 1:]:
                remaining_node = graph.node_map.get(remaining)
                if remaining_node:
                    skipped_log = StepRunLog(
                        step_id=remaining_node.step_id,
                        role_id=remaining_node.role_id,
                        status=StepStatus.SKIPPED.value,
                        message=f"Skipped due to upstream failure ({node.step_id})",
                        timestamp=_now(),
                    )
                    logs.append(skipped_log)
                    step_states[remaining_node.step_id] = StepStatus.SKIPPED.value
            break

    run_status = RUN_STATUS_DONE
    if fail_at is not None and fail_at in step_states:
        if step_states[fail_at] == StepStatus.FAILED.value:
            run_status = RUN_STATUS_FAILED

    return StepRun(
        graph_run_id=graph_run_id,
        graph_id=graph.graph_id,
        request=graph.request,
        status=run_status,
        step_states=step_states,
        logs=logs,
        started_at=started_at,
        finished_at=_now(),
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
