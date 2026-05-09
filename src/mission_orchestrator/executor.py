"""Executor — runs the orchestration steps (dry-run only in this phase).

NUNCA publica. NUNCA chama Meta. NUNCA aciona OAuth.
Dry-run por padrão.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.mission_orchestrator.models import (
    OrchestratorRun,
    OrchestratorStep,
    RUN_STATUS_DRY_RUN,
    RUN_STATUS_COMPLETE,
    RUN_STATUS_FAILED,
    RUN_STATUS_BLOCKED,
    _now_iso,
)
from src.mission_orchestrator.errors import UnknownIntentError
from src.mission_orchestrator.approval_gate import (
    check_approval_gate,
    create_approval_request,
    GATE_NOT_REQUIRED,
    GATE_APPROVED,
    GATE_REJECTED,
    GATE_BLOCKED,
)

RUN_STATUS_BLOCKED_APPROVAL = "blocked_pending_approval"


def execute(
    run: OrchestratorRun,
    packages_root: Optional[Path] = None,
    approvals_log: Optional[Path] = None,
) -> OrchestratorRun:
    """Execute the orchestration run (dry-run: only steps s01 and s02).

    If run.approval_required is True and no approved approval_id is set,
    auto-creates an approval request and returns blocked status.
    """
    # P5.1 — Approval enforcement gate
    gate_status = check_approval_gate(run, approvals_log=approvals_log)

    if gate_status == GATE_REJECTED:
        run.status = RUN_STATUS_BLOCKED
        run.blockers.append("Approval rejected — cannot execute this run")
        run.completed_at = _now_iso()
        return run

    if gate_status == GATE_BLOCKED:
        # Auto-create approval request if one doesn't exist
        if run.approval_id is None:
            req_id = create_approval_request(run, approvals_log=approvals_log)
            run.approval_id = req_id
        run.status = RUN_STATUS_BLOCKED_APPROVAL
        run.blockers.append(
            f"Approval required. Use: jarvis approvals-center approve {run.approval_id}"
        )
        run.completed_at = _now_iso()
        return run

    try:
        _execute_s01(run)
        _execute_s02(run, packages_root)
    except Exception as exc:
        run.status = RUN_STATUS_FAILED
        run.blockers.append(f"Execution failed: {exc}")
        run.completed_at = _now_iso()
        return run

    run.status = RUN_STATUS_DRY_RUN
    run.completed_at = _now_iso()
    return run


def _execute_s01(run: OrchestratorRun) -> None:
    step = _get_step(run, "s01")
    if step is None:
        return
    step.status = "done"
    step.output = f"intent={run.intent}"


def _execute_s02(run: OrchestratorRun, packages_root: Optional[Path]) -> None:
    step = _get_step(run, "s02")
    if step is None:
        return
    from src.mission_builder.executor import run as mb_run

    kwargs: dict = {}
    if packages_root is not None:
        kwargs["packages_root"] = packages_root

    plan, manifest = mb_run(
        request_text=run.request_text,
        account_handle=run.account_handle or None,
        objective=run.objective,
        dry_run=True,
        allow_unknown=True,
        **kwargs,
    )
    if manifest is not None:
        run.mission_id = manifest.mission_id
        step.output = f"mission_id={manifest.mission_id}"
    else:
        step.output = "dry_run=False — no package created"
    step.status = "done"


def _get_step(run: OrchestratorRun, step_id: str) -> Optional[OrchestratorStep]:
    for s in run.steps:
        if s.step_id == step_id:
            return s
    return None
