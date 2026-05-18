"""Provider adapters — bridge existing OMNIS modules into Provider interfaces.

These adapters let existing orchestrators/modules use WorkflowProvider
without rewriting them. The original code is preserved unchanged.
"""
from __future__ import annotations

from typing import Any, Optional

from src.providers.workflow import WorkflowProvider, WorkflowStep, WorkflowResult, SequentialWorkflowProvider


def runtime_orchestrator_as_workflow(
    order_data: dict[str, Any],
    *,
    dry_run: bool = True,
    provider: Optional[WorkflowProvider] = None,
) -> WorkflowResult:
    """Run the runtime_orchestrator pipeline via WorkflowProvider.

    Replaces: OrchestratorService().run(order_data)
    Now: runtime_orchestrator_as_workflow(order_data, dry_run=True)

    The WorkflowProvider handles state passing, dry-run, and error isolation.
    Swap provider= for LangGraphProvider to get checkpointing for free.
    """
    from src.runtime_orchestrator.service import OrchestratorService

    svc = OrchestratorService(dry_run=dry_run)
    wf = provider or SequentialWorkflowProvider()

    steps = [
        WorkflowStep(id="parse_order",       name="Parse Order",        fn=lambda s: svc._parse_order(s)),
        WorkflowStep(id="validate_contract", name="Validate Contract",  fn=lambda s: svc._validate_contract(s)),
        WorkflowStep(id="evaluate_risk",     name="Evaluate Risk",      fn=lambda s: svc._evaluate_risk(s)),
        WorkflowStep(id="check_approval",    name="Check Approval",     fn=lambda s: svc._check_approval(s)),
        WorkflowStep(id="select_skill",      name="Select Skill",       fn=lambda s: svc._select_skill(s)),
        WorkflowStep(id="execute_dryrun",    name="Execute (dry-run)",  fn=lambda s: svc._execute_dryrun(s)),
        WorkflowStep(id="log_decision",      name="Log Decision",       fn=lambda s: svc._log_decision(s)),
        WorkflowStep(id="sink_event",        name="Sink Event",         fn=lambda s: svc._sink_event(s)),
        WorkflowStep(id="write_report",      name="Write Report",       fn=lambda s: svc._write_report(s)),
    ]

    return wf.execute(steps, initial_state=order_data, dry_run=dry_run)


def mission_plan_as_workflow(
    request_text: str,
    *,
    account_handle: str = "",
    objective: str = "engajamento",
    dry_run: bool = True,
    provider: Optional[WorkflowProvider] = None,
) -> WorkflowResult:
    """Run mission_orchestrator.plan + execute via WorkflowProvider.

    Replaces the direct mission_orchestrator.service.run() call.
    Adds: dry_run isolation, step-by-step outputs, error containment per step.
    """
    from src.mission_orchestrator.planner import build_plan
    from src.mission_orchestrator.executor import execute as mission_execute

    wf = provider or SequentialWorkflowProvider()

    def step_plan(state: dict) -> dict:
        orch_run = build_plan(
            request_text=state.get("request_text", ""),
            account_handle=state.get("account_handle", ""),
            objective=state.get("objective", "engajamento"),
            dry_run=state.get("dry_run", True),
        )
        return {"orch_run": orch_run, "run_id": orch_run.run_id, "steps": len(orch_run.steps)}

    def step_execute(state: dict) -> dict:
        orch_run = state.get("orch_run")
        if orch_run is None:
            raise ValueError("orch_run not found in state — step_plan must run first")
        result = mission_execute(orch_run)
        return {"status": result.status, "run_id": result.run_id}

    steps = [
        WorkflowStep(id="plan",    name="Build Mission Plan", fn=step_plan),
        WorkflowStep(id="execute", name="Execute Mission",    fn=step_execute),
    ]

    return wf.execute(
        steps,
        initial_state={
            "request_text": request_text,
            "account_handle": account_handle,
            "objective": objective,
            "dry_run": dry_run,
        },
        dry_run=dry_run,
    )
