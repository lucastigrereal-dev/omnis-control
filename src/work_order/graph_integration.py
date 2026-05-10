"""Graph Integration — conecta execution_graph ao work_order system."""
from __future__ import annotations

from pathlib import Path

from src.execution_graph.models import ExecutionGraph, StepRun, StepRunLog, StepStatus
from src.work_order.models import WorkOrder, WorkOrderStatus


def build_and_persist_work_orders(
    graph: ExecutionGraph,
    step_run: StepRun,
    exports_root: Path | None = None,
) -> list[WorkOrder]:
    """Build work orders from a graph run and persist them to disk.

    Returns the list of WorkOrder objects (also saved to exports_root).
    """
    from src.work_order.builder import build_work_orders_from_graph
    from src.work_order.output_collector import _persist_work_order

    root = exports_root or Path("exports/work_orders")
    work_orders = build_work_orders_from_graph(graph, step_run)

    for wo in work_orders:
        wo_dir = root / wo.work_order_id
        _persist_work_order(wo, wo_dir)

    return work_orders


def sync_work_order_status(
    wo: WorkOrder,
    step_log: StepRunLog,
) -> WorkOrder:
    """Update a work order's status based on a step execution log entry.

    Force-sets status directly since the execution graph is the authority.
    Maps StepStatus -> WorkOrderStatus:
      RUNNING -> IN_PROGRESS_FUTURE
      DONE -> OUTPUT_PENDING
      FAILED -> REJECTED
      SKIPPED -> CLOSED
    """
    from datetime import datetime, timezone

    status_map: dict[str, WorkOrderStatus] = {
        StepStatus.RUNNING.value: WorkOrderStatus.IN_PROGRESS_FUTURE,
        StepStatus.DONE.value: WorkOrderStatus.OUTPUT_PENDING,
        StepStatus.FAILED.value: WorkOrderStatus.REJECTED,
        StepStatus.SKIPPED.value: WorkOrderStatus.CLOSED,
    }

    target = status_map.get(step_log.status)
    if target:
        wo.status = target
        wo.updated_at = datetime.now(timezone.utc).isoformat()

    return wo


def sync_all_work_orders_from_run(
    work_orders: list[WorkOrder],
    step_run: StepRun,
) -> list[WorkOrder]:
    """Sync all work orders with their corresponding step run logs."""
    wo_by_step: dict[str, WorkOrder] = {
        wo.graph_step_id: wo for wo in work_orders
    }

    outcome_logs = [
        log for log in step_run.logs
        if log.status in (StepStatus.DONE.value, StepStatus.FAILED.value, StepStatus.SKIPPED.value, StepStatus.RUNNING.value)
    ]

    for log in outcome_logs:
        wo = wo_by_step.get(log.step_id)
        if wo:
            sync_work_order_status(wo, log)

    return work_orders


def run_graph_with_work_orders(
    graph: ExecutionGraph,
    squad_plan=None,
    approval_id: str | None = None,
    approvals_log=None,
    exports_root: Path | None = None,
    fail_at: str | None = None,
) -> tuple[StepRun, list[WorkOrder]]:
    """Run a graph with full work order integration.

    1. Check approval gate (if squad requires it)
    2. Run the graph
    3. Build and persist work orders
    4. Sync work order status from step results

    Returns (StepRun, list[WorkOrder]).
    """
    from src.execution_graph.runner import run_graph_dry
    from src.execution_graph.approval_bridge import (
        check_approval_gate,
        GATE_BLOCKED,
        GATE_REJECTED,
    )

    root = exports_root or Path("exports/work_orders")
    approval_required = squad_plan.approval_required if squad_plan else False
    risk_level = squad_plan.risk_level if squad_plan else "low"

    gate = check_approval_gate(approval_required, approval_id, approvals_log)

    if gate == GATE_REJECTED:
        step_run = StepRun.blocked(
            graph=graph,
            reason=f"Approval request {approval_id} was rejected",
            approval_id=approval_id,
            approval_required=True,
        )
        work_orders = build_and_persist_work_orders(graph, step_run, root)
        for wo in work_orders:
            wo.status = WorkOrderStatus.REJECTED
        _persist_all(work_orders, root)
        return step_run, work_orders

    if gate == GATE_BLOCKED:
        from src.execution_graph.approval_bridge import request_graph_approval
        new_approval_id = request_graph_approval(graph, risk_level, approvals_log)
        step_run = StepRun.blocked(
            graph=graph,
            reason=f"Approval required — request {new_approval_id} created",
            approval_id=new_approval_id,
            approval_required=True,
        )
        work_orders = build_and_persist_work_orders(graph, step_run, root)
        for wo in work_orders:
            wo.status = WorkOrderStatus.BLOCKED
            wo.approval_id = new_approval_id
        _persist_all(work_orders, root)
        return step_run, work_orders

    step_run = run_graph_dry(
        graph,
        fail_at=fail_at,
        include_snapshot=True,
        approval_id=approval_id,
        approval_required=approval_required,
    )

    work_orders = build_and_persist_work_orders(graph, step_run, root)
    sync_all_work_orders_from_run(work_orders, step_run)
    _persist_all(work_orders, root)

    return step_run, work_orders


def _persist_all(work_orders: list[WorkOrder], root: Path):
    from src.work_order.output_collector import _persist_work_order
    for wo in work_orders:
        _persist_work_order(wo, root / wo.work_order_id)


def find_work_order_ids_for_run(
    graph_run_id: str,
    exports_root: Path | None = None,
) -> dict[str, str]:
    """Find work order IDs for a graph run. Returns {step_id: work_order_id}."""
    root = exports_root or Path("exports/work_orders")
    result: dict[str, str] = {}

    if not root.exists():
        return result

    for wo_dir in root.iterdir():
        manifest = wo_dir / "work_order.json"
        if manifest.exists():
            import json
            data = json.loads(manifest.read_text(encoding="utf-8"))
            if data.get("graph_run_id") == graph_run_id:
                result[data["graph_step_id"]] = data["work_order_id"]

    return result


def load_work_orders_for_run(
    graph_run_id: str,
    exports_root: Path | None = None,
) -> list[WorkOrder]:
    """Load all work orders for a given graph run from disk."""
    root = exports_root or Path("exports/work_orders")
    work_orders: list[WorkOrder] = []

    if not root.exists():
        return work_orders

    for wo_dir in root.iterdir():
        manifest = wo_dir / "work_order.json"
        if manifest.exists():
            import json
            data = json.loads(manifest.read_text(encoding="utf-8"))
            if data.get("graph_run_id") == graph_run_id:
                work_orders.append(WorkOrder.from_dict(data))

    return work_orders
