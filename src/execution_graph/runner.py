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
from src.execution_graph.retry import RetryPolicy, RetryConfig
from src.execution_graph.circuit_breaker import CircuitBreakerRegistry, CircuitState
from src.execution_graph.rollback import RollbackPlan


def run_graph_dry(
    graph: ExecutionGraph,
    fail_at: str | None = None,
    skip_done: set[str] | None = None,
    run_id: str | None = None,
    include_snapshot: bool = False,
    approval_id: str | None = None,
    approval_required: bool = False,
    retry_policy: RetryPolicy | None = None,
    circuit_registry: CircuitBreakerRegistry | None = None,
    rollback_plan: RollbackPlan | None = None,
) -> StepRun:
    """Simulate executing all steps in topological order. No side effects.

    Args:
        graph: The ExecutionGraph to simulate.
        fail_at: Optional step_id — if provided, that step will FAIL instead of DONE.
        skip_done: Optional set of step_ids to skip (already done in previous run).
        run_id: Optional graph_run_id to reuse (for resume).
        include_snapshot: If True, include graph.to_dict() in the result.
        approval_id: Optional approval request ID that authorized this run.
        approval_required: Whether approval was checked before running.
        retry_policy: Optional retry policy for failed steps.
        circuit_registry: Optional circuit breaker registry for step-level circuit protection.
        rollback_plan: Optional rollback plan — executed on failure to undo completed steps.
    """
    if not graph.nodes:
        raise ExecutionGraphError("Cannot run empty graph")

    graph_run_id = run_id or _make_run_id()
    started_at = _now()
    logs: list[StepRunLog] = []
    step_states: dict[str, str] = {}
    skip_set = skip_done or set()

    for step_id in graph.topological_order:
        node = graph.node_map.get(step_id)
        if node is None:
            continue

        # Skip already-done steps
        if step_id in skip_set:
            skip_log = StepRunLog(
                step_id=node.step_id,
                role_id=node.role_id,
                status=StepStatus.DONE.value,
                message=f"Step '{node.title}' already done — skipped",
                timestamp=_now(),
            )
            logs.append(skip_log)
            step_states[node.step_id] = StepStatus.DONE.value
            continue

        # Circuit breaker check — block if circuit is open
        if circuit_registry is not None:
            breaker = circuit_registry.get(node.step_id)
            if not breaker.before_call():
                blocked_log = StepRunLog(
                    step_id=node.step_id,
                    role_id=node.role_id,
                    status=StepStatus.SKIPPED.value,
                    message=f"Step '{node.title}' blocked — circuit {breaker.state.value} "
                            f"(failures={breaker.failure_count}, threshold={breaker.failure_threshold})",
                    timestamp=_now(),
                )
                logs.append(blocked_log)
                step_states[node.step_id] = StepStatus.SKIPPED.value
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
        step_config = retry_policy.get_config(node.step_id) if retry_policy else None
        max_attempts = step_config.max_retries + 1 if step_config else 1

        status = StepStatus.DONE
        msg = ""

        if fail_at is not None and node.step_id == fail_at:
            status = StepStatus.FAILED
            msg = f"Step '{node.title}' FAILED (injected failure)"

            # Simulate retry attempts
            if step_config and step_config.max_retries > 0:
                for attempt in range(1, max_attempts + 1):
                    delay = step_config.delay_for_attempt(attempt)
                    if attempt <= step_config.max_retries:
                        retry_log = StepRunLog(
                            step_id=node.step_id,
                            role_id=node.role_id,
                            status=StepStatus.RUNNING.value,
                            message=(
                                f"Step '{node.title}' retry {attempt}/{step_config.max_retries} "
                                f"(backoff={step_config.backoff.value}, delay={delay:.1f}s)"
                            ),
                            timestamp=_now(),
                        )
                        logs.append(retry_log)
                    if attempt == max_attempts:
                        # Final attempt — still failed
                        msg = (
                            f"Step '{node.title}' FAILED after {max_attempts} attempts "
                            f"(max_retries={step_config.max_retries})"
                        )
                    # In dry-run, don't actually wait — log captures the delay
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

        # Circuit breaker reporting
        if circuit_registry is not None:
            if status == StepStatus.FAILED:
                circuit_registry.on_step_failure(node.step_id)
            elif status == StepStatus.DONE:
                circuit_registry.on_step_success(node.step_id)

        # If a step failed (after all retries), mark all downstream as skipped and abort
        if status == StepStatus.FAILED:
            for remaining in graph.topological_order[graph.topological_order.index(step_id) + 1:]:
                remaining_node = graph.node_map.get(remaining)
                if remaining_node:
                    if remaining not in skip_set:
                        skipped_log = StepRunLog(
                            step_id=remaining_node.step_id,
                            role_id=remaining_node.role_id,
                            status=StepStatus.SKIPPED.value,
                            message=f"Skipped due to upstream failure ({node.step_id})",
                            timestamp=_now(),
                        )
                        logs.append(skipped_log)
                        step_states[remaining_node.step_id] = StepStatus.SKIPPED.value

            # Execute rollback for completed steps
            if rollback_plan is not None and not rollback_plan.is_empty():
                completed_for_rollback = {
                    sid for sid, s in step_states.items()
                    if s == StepStatus.DONE.value and sid not in skip_set
                }
                rb_logs = rollback_plan.execute_dry(completed_for_rollback)
                for entry in rb_logs:
                    rb_step_log = StepRunLog(
                        step_id=entry["step_id"],
                        role_id="rollback",
                        status=entry["status"],
                        message=entry["message"],
                        timestamp=_now(),
                    )
                    logs.append(rb_step_log)
            break

    run_status = RUN_STATUS_DONE
    if fail_at is not None and fail_at in step_states:
        if step_states[fail_at] == StepStatus.FAILED.value:
            run_status = RUN_STATUS_FAILED

    snapshot = graph.to_dict() if include_snapshot else None

    return StepRun(
        graph_run_id=graph_run_id,
        graph_id=graph.graph_id,
        request=graph.request,
        status=run_status,
        step_states=step_states,
        logs=logs,
        started_at=started_at,
        finished_at=_now(),
        graph_snapshot=snapshot,
        approval_id=approval_id,
        approval_required=approval_required,
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
