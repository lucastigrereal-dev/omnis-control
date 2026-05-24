"""Approval Gate — enforces approval before risky orchestrator runs."""
from __future__ import annotations

from pathlib import Path

from src.mission_orchestrator.models import OrchestratorRun, RUN_STATUS_BLOCKED
from src.approval_center import store as store_mod
from src.approval_center.gate import (
    check_gate,
    GATE_BLOCKED,
    GATE_APPROVED,
    GATE_REJECTED,
    GATE_NOT_REQUIRED,
)


def check_approval_gate(
    run: OrchestratorRun,
    approvals_log: Path | None = None,
) -> str:
    """Check approval gate status for a run.

    Returns one of: "not_required", "approved", "rejected", "blocked_pending_approval".
    Does NOT modify the run — caller decides what to do.
    """
    return check_gate(
        approval_required=run.approval_required,
        approval_id=run.approval_id,
        approvals_log=approvals_log,
    )


def create_approval_request(
    run: OrchestratorRun,
    approvals_log: Path | None = None,
) -> str:
    """Create an approval request for a run that requires approval.

    Returns the approval request_id. Does NOT set run.approval_id — caller does.
    """
    from src.approval_center.service import request_approval

    log_path = approvals_log if approvals_log is not None else store_mod.DEFAULT_APPROVALS_LOG

    capability_ids = ", ".join(run.matched_capabilities) if run.matched_capabilities else "unknown"
    req = request_approval(
        subject=f"Orchestrator run: {run.request_text[:80]}",
        description=f"run_id={run.run_id} | capabilities={capability_ids}",
        capability_id=run.matched_capabilities[0] if run.matched_capabilities else "unknown",
        risk_level="high" if any(True for _ in run.matched_capabilities) else "medium",
        approvals_log=log_path,
    )
    return req.request_id
