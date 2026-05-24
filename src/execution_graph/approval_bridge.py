"""Approval Bridge — conecta execution_graph ao approval_center."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.execution_graph.models import ExecutionGraph, StepRun, RUN_STATUS_DONE, RUN_STATUS_FAILED
from src.approval_center import store as store_mod
from src.approval_center.gate import (
    check_gate,
    GATE_BLOCKED,
    GATE_APPROVED,
    GATE_REJECTED,
    GATE_NOT_REQUIRED,
)

RUN_STATUS_BLOCKED = "blocked_pending_approval"

BASE = Path(__file__).resolve().parent.parent.parent


def check_approval_gate(
    approval_required: bool,
    approval_id: str | None = None,
    approvals_log=None,
) -> str:
    """Check approval gate status for a graph run.

    Returns one of: "not_required", "approved", "rejected", "blocked_pending_approval".
    """
    return check_gate(
        approval_required=approval_required,
        approval_id=approval_id,
        approvals_log=approvals_log,
    )


def request_graph_approval(
    graph: ExecutionGraph,
    risk_level: str = "medium",
    approvals_log=None,
) -> str:
    """Create an approval request for a graph run. Returns the request_id."""
    from src.approval_center.service import request_approval

    log_path = approvals_log if approvals_log is not None else store_mod.DEFAULT_APPROVALS_LOG

    node_list = ", ".join(n.title for n in graph.nodes[:5])
    if len(graph.nodes) > 5:
        node_list += f", ... ({len(graph.nodes)} total)"

    req = request_approval(
        subject=f"Graph run: {graph.request[:80]}",
        description=f"graph_id={graph.graph_id} | squad={graph.squad_id} | steps={node_list}",
        capability_id=graph.squad_id,
        risk_level=risk_level,
        approvals_log=log_path,
    )
    return req.request_id


def run_graph_with_approval_gate(
    graph: ExecutionGraph,
    squad_plan=None,
    approval_id: str | None = None,
    approvals_log=None,
    fail_at: str | None = None,
) -> StepRun:
    """Run a graph with approval gate enforcement.

    If the squad requires approval and no approved request exists,
    returns a StepRun with status "blocked_pending_approval" and the
    approval request details.
    """
    from src.execution_graph.runner import run_graph_dry

    approval_required = squad_plan.approval_required if squad_plan else False
    risk_level = squad_plan.risk_level if squad_plan else "low"

    gate = check_approval_gate(approval_required, approval_id, approvals_log)

    if gate == GATE_NOT_REQUIRED or gate == GATE_APPROVED:
        return run_graph_dry(
            graph,
            fail_at=fail_at,
            include_snapshot=True,
            approval_id=approval_id,
            approval_required=approval_required,
        )

    if gate == GATE_REJECTED:
        return StepRun.blocked(
            graph=graph,
            reason=f"Approval request {approval_id} was rejected",
            approval_id=approval_id,
            approval_required=True,
        )

    # GATE_BLOCKED — auto-create approval request
    new_approval_id = request_graph_approval(graph, risk_level, approvals_log)

    return StepRun.blocked(
        graph=graph,
        reason=f"Approval required — request {new_approval_id} created. Run: jarvis approvals-center approve {new_approval_id}",
        approval_id=new_approval_id,
        approval_required=True,
    )
