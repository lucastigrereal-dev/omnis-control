"""Mission Bridge — conecta Mission Orchestrator → Squad → Execution Graph.

Single entry point: run_full_pipeline() chains the full P3+P7+P8 flow.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.mission_orchestrator.models import OrchestratorRun


def build_graph_from_orchestrator(
    orch_run: OrchestratorRun,
) -> "ExecutionGraph":
    """Build an ExecutionGraph from an orchestrator run with squad already composed."""
    from src.squad_composer.composer import compose_squad
    from src.task_decomposer.decomposer import decompose_squad
    from src.execution_graph.builder import build_graph

    squad = compose_squad(orch_run.request_text)
    orch_run.squad_id = squad.squad_id
    task_plan = decompose_squad(squad)
    graph = build_graph(squad, task_plan)
    return graph


def run_graph_from_orchestrator(
    orch_run: OrchestratorRun,
    fail_at: str | None = None,
    approval_id: str | None = None,
    approvals_log=None,
) -> "StepRun":
    """Build + run graph from orchestrator run with approval gate."""
    from src.execution_graph.runner import run_graph_dry

    graph = build_graph_from_orchestrator(orch_run)

    approval_required = orch_run.approval_required
    if approval_id is not None:
        pass  # use provided approval_id

    step_run = run_graph_dry(
        graph,
        fail_at=fail_at,
        include_snapshot=True,
        approval_id=approval_id,
        approval_required=approval_required,
    )
    orch_run.graph_run_id = step_run.graph_run_id
    return step_run


def run_full_pipeline(
    request_text: str,
    account_handle: str = "",
    objective: str = "engajamento",
    dry_run: bool = True,
    allow_unknown: bool = False,
    approval_id: str | None = None,
    fail_at: str | None = None,
    runs_root: Optional[Path] = None,
    runs_log: Optional[Path] = None,
    packages_root: Optional[Path] = None,
    approvals_log=None,
) -> tuple[OrchestratorRun, "StepRun"]:
    """Run the full pipeline: Orchestrator → Squad → Graph.

    Returns (orchestrator_run, step_run).
    """
    from src.mission_orchestrator import service as orch_svc
    from src.execution_graph.store import write_manifest, DEFAULT_STORE_ROOT

    # Phase 1: Orchestrator plan + execute (s01-s05)
    if approval_id:
        orch_run = orch_svc.run_with_approval(
            request_text=request_text,
            account_handle=account_handle,
            objective=objective,
            dry_run=dry_run,
            allow_unknown=allow_unknown,
            approval_id=approval_id,
            runs_root=runs_root or orch_svc.DEFAULT_RUNS_ROOT,
            runs_log=runs_log or orch_svc.DEFAULT_RUNS_LOG,
            packages_root=packages_root,
            approvals_log=approvals_log,
        )
    else:
        orch_run = orch_svc.run(
            request_text=request_text,
            account_handle=account_handle,
            objective=objective,
            dry_run=dry_run,
            allow_unknown=allow_unknown,
            runs_root=runs_root or orch_svc.DEFAULT_RUNS_ROOT,
            runs_log=runs_log or orch_svc.DEFAULT_RUNS_LOG,
            packages_root=packages_root,
        )

    if orch_run.status in ("failed", "blocked", "blocked_pending_approval"):
        return orch_run, None

    # Phase 2: Squad → Graph
    graph = build_graph_from_orchestrator(orch_run)

    from src.execution_graph.runner import run_graph_dry
    step_run = run_graph_dry(
        graph,
        fail_at=fail_at,
        include_snapshot=True,
        approval_id=approval_id,
        approval_required=orch_run.approval_required,
    )

    orch_run.graph_run_id = step_run.graph_run_id
    orch_run.squad_id = graph.squad_id

    # Mark s06, s07 as done
    _mark_step(orch_run, "s06", "done", f"squad_id={graph.squad_id}")
    _mark_step(orch_run, "s07", "done", f"graph_run_id={step_run.graph_run_id}")

    # Persist graph run
    store_root = DEFAULT_STORE_ROOT
    run_dir = store_root / step_run.graph_run_id
    write_manifest(run_dir, step_run.to_dict())

    return orch_run, step_run


def run_full_pipeline_real(
    request_text: str,
    account_handle: str = "",
    objective: str = "engajamento",
    dry_run: bool = True,
    allow_unknown: bool = False,
    approval_id: str | None = None,
    fail_at: str | None = None,
    runs_root: Optional[Path] = None,
    runs_log: Optional[Path] = None,
    packages_root: Optional[Path] = None,
    approvals_log=None,
    catalog_path: str | None = None,
    registry=None,
) -> tuple[OrchestratorRun, "StepRun"]:
    """Run full pipeline with real SkillRunnerBridge → ModelRouter → LLM.

    Same as run_full_pipeline() but uses run_graph_real() with SkillRunnerBridge
    instead of run_graph_dry() for step execution.
    """
    from src.mission_orchestrator import service as orch_svc
    from src.execution_graph.store import write_manifest, DEFAULT_STORE_ROOT
    from src.execution_graph.runner import run_graph_real
    from src.agentic.skill_runner_bridge import SkillRunnerBridge
    from src.skills_bridge.adapter import RealSkillAdapter
    from src.skills_bridge.skill_catalog import SkillCatalog
    from src.skills_bridge.selection import SkillSelector

    # Phase 1: Orchestrator plan + execute
    if approval_id:
        orch_run = orch_svc.run_with_approval(
            request_text=request_text,
            account_handle=account_handle,
            objective=objective,
            dry_run=dry_run,
            allow_unknown=allow_unknown,
            approval_id=approval_id,
            runs_root=runs_root or orch_svc.DEFAULT_RUNS_ROOT,
            runs_log=runs_log or orch_svc.DEFAULT_RUNS_LOG,
            packages_root=packages_root,
            approvals_log=approvals_log,
        )
    else:
        orch_run = orch_svc.run(
            request_text=request_text,
            account_handle=account_handle,
            objective=objective,
            dry_run=dry_run,
            allow_unknown=allow_unknown,
            runs_root=runs_root or orch_svc.DEFAULT_RUNS_ROOT,
            runs_log=runs_log or orch_svc.DEFAULT_RUNS_LOG,
            packages_root=packages_root,
        )

    if orch_run.status in ("failed", "blocked", "blocked_pending_approval"):
        return orch_run, None

    # Phase 2: Squad → Graph
    graph = build_graph_from_orchestrator(orch_run)

    # Phase 3: Set up SkillRunnerBridge with catalog + real adapter
    if catalog_path:
        catalog = SkillCatalog(catalog_path=catalog_path)
        selector = SkillSelector(dry_run=dry_run, catalog=catalog)
    else:
        catalog = None
        selector = SkillSelector(dry_run=dry_run)

    if dry_run:
        from src.skills_bridge.adapter import MockSkillAdapter
        adapter = MockSkillAdapter(dry_run=True)
    else:
        adapter = RealSkillAdapter(registry=registry, dry_run=False)

    bridge = SkillRunnerBridge(dry_run=dry_run, adapter=adapter)
    bridge.selector = selector

    # Phase 4: Execute graph with real bridge
    step_run = run_graph_real(
        graph,
        bridge,
        include_snapshot=True,
    )

    orch_run.graph_run_id = step_run.graph_run_id
    orch_run.squad_id = graph.squad_id

    _mark_step(orch_run, "s06", "done", f"squad_id={graph.squad_id}")
    _mark_step(orch_run, "s07", "done", f"graph_run_id={step_run.graph_run_id}")

    # Persist graph run
    store_root = DEFAULT_STORE_ROOT
    run_dir = store_root / step_run.graph_run_id
    write_manifest(run_dir, step_run.to_dict())

    return orch_run, step_run


def _mark_step(
    orch_run: OrchestratorRun,
    step_id: str,
    status: str,
    output: str = "",
) -> None:
    for s in orch_run.steps:
        if s.step_id == step_id:
            s.status = status
            if output:
                s.output = output
            return
