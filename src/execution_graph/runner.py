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


def _validate_graph_dry(graph: ExecutionGraph) -> None:
    if not graph.nodes:
        raise ExecutionGraphError("Cannot run empty graph")


def _validate_graph_real(graph: ExecutionGraph) -> None:
    if not graph.nodes:
        raise ExecutionGraphError("Cannot run empty graph")


def _resolve_dry_step(graph: ExecutionGraph, step_id: str) -> StepNode | None:
    return graph.node_map.get(step_id)


def _emit_dry_event(
    logs: list[StepRunLog],
    node: StepNode,
    status: str,
    message: str,
    role_id: str | None = None,
) -> StepRunLog:
    log = StepRunLog(
        step_id=node.step_id,
        role_id=role_id or node.role_id,
        status=status,
        message=message,
        timestamp=_now(),
    )
    logs.append(log)
    return log


def _collect_dry_results(
    graph: ExecutionGraph,
    graph_run_id: str,
    run_status: str,
    step_states: dict[str, str],
    logs: list[StepRunLog],
    started_at: str,
    include_snapshot: bool,
    approval_id: str | None,
    approval_required: bool,
) -> StepRun:
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


def _resolve_dry_step_result(
    node: StepNode,
    fail_at: str | None,
    retry_policy: RetryPolicy | None,
    logs: list[StepRunLog],
) -> tuple[StepStatus, str]:
    step_config = retry_policy.get_config(node.step_id) if retry_policy else None
    max_attempts = step_config.max_retries + 1 if step_config else 1

    if fail_at is None or node.step_id != fail_at:
        return StepStatus.DONE, f"Step '{node.title}' completed (output: {node.expected_output})"

    msg = f"Step '{node.title}' FAILED (injected failure)"
    if step_config and step_config.max_retries > 0:
        for attempt in range(1, max_attempts + 1):
            delay = step_config.delay_for_attempt(attempt)
            if attempt <= step_config.max_retries:
                _emit_dry_event(
                    logs,
                    node,
                    StepStatus.RUNNING.value,
                    message=(
                        f"Step '{node.title}' retry {attempt}/{step_config.max_retries} "
                        f"(backoff={step_config.backoff.value}, delay={delay:.1f}s)"
                    ),
                )
            if attempt == max_attempts:
                msg = (
                    f"Step '{node.title}' FAILED after {max_attempts} attempts "
                    f"(max_retries={step_config.max_retries})"
                )
    return StepStatus.FAILED, msg


def _collect_downstream_dry_skips(
    graph: ExecutionGraph,
    failed_step_id: str,
    failed_node: StepNode,
    skip_set: set[str],
    logs: list[StepRunLog],
    step_states: dict[str, str],
) -> None:
    for remaining in graph.topological_order[graph.topological_order.index(failed_step_id) + 1:]:
        remaining_node = graph.node_map.get(remaining)
        if remaining_node and remaining not in skip_set:
            _emit_dry_event(
                logs,
                remaining_node,
                StepStatus.SKIPPED.value,
                message=f"Skipped due to upstream failure ({failed_node.step_id})",
            )
            step_states[remaining_node.step_id] = StepStatus.SKIPPED.value


def _collect_dry_rollback(
    rollback_plan: RollbackPlan | None,
    skip_set: set[str],
    logs: list[StepRunLog],
    step_states: dict[str, str],
) -> None:
    if rollback_plan is None or rollback_plan.is_empty():
        return

    completed_for_rollback = {
        sid for sid, state in step_states.items()
        if state == StepStatus.DONE.value and sid not in skip_set
    }
    for entry in rollback_plan.execute_dry(completed_for_rollback):
        logs.append(StepRunLog(
            step_id=entry["step_id"],
            role_id="rollback",
            status=entry["status"],
            message=entry["message"],
            timestamp=_now(),
        ))


def _resolve_real_step(node: StepNode, bridge):
    from src.agentic.task_dispatcher import DispatchEntry

    return DispatchEntry(
        task_id=node.task_id or node.step_id,
        deliverable=node.expected_output or node.title,
        executor=node.assigned_role or "skill_runner",
        status="dispatched",
        dry_run=bridge.dry_run,
    )


def _execute_real_step_result(
    node: StepNode,
    entry,
    bridge,
    retry_policy: RetryPolicy | None,
    logs: list[StepRunLog],
) -> tuple[StepStatus, str]:
    step_config = retry_policy.get_config(node.step_id) if retry_policy else None
    max_attempts = step_config.max_retries + 1 if step_config else 1
    result = None
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            result = bridge.execute_entry(entry)
            if result.status in ("success", "dry_run"):
                break
            last_error = RuntimeError(result.error or f"Status: {result.status}")
        except Exception as e:
            last_error = e

        if attempt < max_attempts and step_config:
            delay = step_config.delay_for_attempt(attempt)
            _emit_real_event(
                logs,
                node,
                StepStatus.RUNNING.value,
                message=(
                    f"Step '{node.title}' retry {attempt}/{step_config.max_retries} "
                    f"(backoff={step_config.backoff.value}, delay={delay:.1f}s)"
                ),
            )

    if result is None or result.status == "failed":
        msg = f"Step '{node.title}' FAILED"
        if last_error:
            msg += f": {last_error}"
        if step_config:
            msg += f" after {max_attempts} attempts (max_retries={step_config.max_retries})"
        return StepStatus.FAILED, msg

    return StepStatus.DONE, f"Step '{node.title}' completed → {result.output[:200]}"


def _collect_downstream_real_skips(
    graph: ExecutionGraph,
    failed_step_id: str,
    failed_node: StepNode,
    logs: list[StepRunLog],
    step_states: dict[str, str],
) -> None:
    for remaining in graph.topological_order[graph.topological_order.index(failed_step_id) + 1:]:
        remaining_node = graph.node_map.get(remaining)
        if remaining_node:
            _emit_real_event(
                logs,
                remaining_node,
                StepStatus.SKIPPED.value,
                message=f"Skipped due to upstream failure ({failed_node.step_id})",
            )
            step_states[remaining_node.step_id] = StepStatus.SKIPPED.value


def _collect_real_rollback(
    rollback_plan: RollbackPlan | None,
    logs: list[StepRunLog],
    step_states: dict[str, str],
) -> None:
    if rollback_plan is None or rollback_plan.is_empty():
        return

    completed_for_rollback = {
        sid for sid, state in step_states.items()
        if state == StepStatus.DONE.value
    }
    for entry_data in rollback_plan.execute_dry(completed_for_rollback):
        logs.append(StepRunLog(
            step_id=entry_data["step_id"],
            role_id="rollback",
            status=entry_data["status"],
            message=entry_data["message"],
            timestamp=_now(),
        ))


def _collect_upstream_context(
    node: StepNode,
    context_store: dict[str, str] | None,
) -> str:
    """Build upstream context string from completed dependency outputs."""
    if context_store is None or not node.depends_on:
        return ""
    parts = [
        f"[{dep_id}]: {context_store[dep_id]}"
        for dep_id in node.depends_on
        if dep_id in context_store
    ]
    return "\n".join(parts)


def _emit_real_event(
    logs: list[StepRunLog],
    node: StepNode,
    status: str,
    message: str,
    role_id: str | None = None,
) -> StepRunLog:
    log = StepRunLog(
        step_id=node.step_id,
        role_id=role_id or node.role_id,
        status=status,
        message=message,
        timestamp=_now(),
    )
    logs.append(log)
    return log


def _collect_real_results(
    graph: ExecutionGraph,
    graph_run_id: str,
    run_status: str,
    step_states: dict[str, str],
    logs: list[StepRunLog],
    started_at: str,
    include_snapshot: bool,
) -> StepRun:
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
    )


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
    context_store: dict[str, str] | None = None,
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
    _validate_graph_dry(graph)

    graph_run_id = run_id or _make_run_id()
    started_at = _now()
    logs: list[StepRunLog] = []
    step_states: dict[str, str] = {}
    skip_set = skip_done or set()

    for step_id in graph.topological_order:
        node = _resolve_dry_step(graph, step_id)
        if node is None:
            continue

        # Skip already-done steps
        if step_id in skip_set:
            _emit_dry_event(
                logs,
                node,
                StepStatus.DONE.value,
                f"Step '{node.title}' already done — skipped",
            )
            step_states[node.step_id] = StepStatus.DONE.value
            continue

        # Circuit breaker check — block if circuit is open
        if circuit_registry is not None:
            breaker = circuit_registry.get(node.step_id)
            if not breaker.before_call():
                _emit_dry_event(
                    logs,
                    node,
                    StepStatus.SKIPPED.value,
                    message=f"Step '{node.title}' blocked — circuit {breaker.state.value} "
                            f"(failures={breaker.failure_count}, threshold={breaker.failure_threshold})",
                )
                step_states[node.step_id] = StepStatus.SKIPPED.value
                continue

        # Mark as running
        _emit_dry_event(
            logs,
            node,
            StepStatus.RUNNING.value,
            message=f"Step '{node.title}' started (role={node.role_id}, est={node.estimated_duration})",
        )
        step_states[node.step_id] = StepStatus.RUNNING.value

        status, msg = _resolve_dry_step_result(
            node=node,
            fail_at=fail_at,
            retry_policy=retry_policy,
            logs=logs,
        )

        _emit_dry_event(logs, node, status.value, msg)
        step_states[node.step_id] = status.value

        # Onda 8 Passo 4: accumulate output for downstream steps
        if status == StepStatus.DONE and context_store is not None:
            context_store[node.step_id] = node.expected_output

        # Circuit breaker reporting
        if circuit_registry is not None:
            if status == StepStatus.FAILED:
                circuit_registry.on_step_failure(node.step_id)
            elif status == StepStatus.DONE:
                circuit_registry.on_step_success(node.step_id)

        # If a step failed (after all retries), mark all downstream as skipped and abort
        if status == StepStatus.FAILED:
            _collect_downstream_dry_skips(
                graph=graph,
                failed_step_id=step_id,
                failed_node=node,
                skip_set=skip_set,
                logs=logs,
                step_states=step_states,
            )
            _collect_dry_rollback(
                rollback_plan=rollback_plan,
                skip_set=skip_set,
                logs=logs,
                step_states=step_states,
            )
            break

    run_status = RUN_STATUS_DONE
    if fail_at is not None and fail_at in step_states:
        if step_states[fail_at] == StepStatus.FAILED.value:
            run_status = RUN_STATUS_FAILED

    return _collect_dry_results(
        graph=graph,
        graph_run_id=graph_run_id,
        run_status=run_status,
        step_states=step_states,
        logs=logs,
        started_at=started_at,
        include_snapshot=include_snapshot,
        approval_id=approval_id,
        approval_required=approval_required,
    )


def run_graph_real(
    graph: ExecutionGraph,
    bridge,
    run_id: str | None = None,
    include_snapshot: bool = False,
    retry_policy: RetryPolicy | None = None,
    circuit_registry: CircuitBreakerRegistry | None = None,
    rollback_plan: RollbackPlan | None = None,
    context_store: dict[str, str] | None = None,
) -> StepRun:
    """Execute all steps in topological order, delegating to SkillRunnerBridge.

    Unlike run_graph_dry(), this actually dispatches work to real skill adapters.
    Uses the same circuit breaker, retry, and rollback infrastructure.
    """
    _validate_graph_real(graph)

    graph_run_id = run_id or _make_run_id()
    started_at = _now()
    logs: list[StepRunLog] = []
    step_states: dict[str, str] = {}

    for step_id in graph.topological_order:
        node = _resolve_dry_step(graph, step_id)
        if node is None:
            continue

        # Circuit breaker check
        if circuit_registry is not None:
            breaker = circuit_registry.get(node.step_id)
            if not breaker.before_call():
                _emit_real_event(
                    logs,
                    node,
                    StepStatus.SKIPPED.value,
                    message=f"Step '{node.title}' blocked — circuit {breaker.state.value} "
                            f"(failures={breaker.failure_count}, threshold={breaker.failure_threshold})",
                )
                step_states[node.step_id] = StepStatus.SKIPPED.value
                continue

        # Running
        _emit_real_event(
            logs,
            node,
            StepStatus.RUNNING.value,
            message=f"Step '{node.title}' started (role={node.role_id}, est={node.estimated_duration})",
        )
        step_states[node.step_id] = StepStatus.RUNNING.value

        # Build dispatch entry from step node
        entry = _resolve_real_step(node, bridge)

        # Onda 8 Passo 4: inject upstream output as context hint
        upstream = _collect_upstream_context(node, context_store)
        if upstream:
            entry.result_hint = upstream

        status, msg = _execute_real_step_result(
            node=node,
            entry=entry,
            bridge=bridge,
            retry_policy=retry_policy,
            logs=logs,
        )

        _emit_real_event(logs, node, status.value, msg)
        step_states[node.step_id] = status.value

        # Onda 8 Passo 4: capture output for downstream steps
        if status == StepStatus.DONE and context_store is not None:
            arrow = " → "
            if arrow in msg:
                context_store[node.step_id] = msg.split(arrow, 1)[1]
            else:
                context_store[node.step_id] = node.expected_output

        # Circuit breaker reporting
        if circuit_registry is not None:
            if status == StepStatus.FAILED:
                circuit_registry.on_step_failure(node.step_id)
            elif status == StepStatus.DONE:
                circuit_registry.on_step_success(node.step_id)

        # On failure, skip downstream and rollback
        if status == StepStatus.FAILED:
            _collect_downstream_real_skips(
                graph=graph,
                failed_step_id=step_id,
                failed_node=node,
                logs=logs,
                step_states=step_states,
            )
            _collect_real_rollback(
                rollback_plan=rollback_plan,
                logs=logs,
                step_states=step_states,
            )
            break

    # Determine overall status
    run_status = RUN_STATUS_DONE
    if any(s == StepStatus.FAILED.value for s in step_states.values()):
        run_status = RUN_STATUS_FAILED

    return _collect_real_results(
        graph=graph,
        graph_run_id=graph_run_id,
        run_status=run_status,
        step_states=step_states,
        logs=logs,
        started_at=started_at,
        include_snapshot=include_snapshot,
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
