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
    _now_iso,
)
from src.mission_orchestrator.errors import UnknownIntentError


def execute(
    run: OrchestratorRun,
    packages_root: Optional[Path] = None,
) -> OrchestratorRun:
    """Execute the orchestration run (dry-run: only steps s01 and s02).

    s01: detect intent (already done in plan)
    s02: create mission package via mission_builder
    s03-s04: skipped (require asset — manual step)
    s05: pending (requires human validation)
    """
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
