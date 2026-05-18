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


def squad_execution_as_workflow(
    squad_request: dict[str, Any],
    *,
    dry_run: bool = True,
    provider: Optional[WorkflowProvider] = None,
) -> WorkflowResult:
    """Run squad_execution via WorkflowProvider.

    Replaces: SquadPlanner().plan() + SquadExecutor().execute()
    Swap provider= for LangGraphProvider to get per-agent checkpointing.
    """
    from src.squad_execution.planner import plan_squad_run
    from src.squad_execution.executor import execute_squad_run

    wf = provider or SequentialWorkflowProvider()

    def step_plan(state: dict) -> dict:
        result = plan_squad_run(state.get("request", ""), dry_run=state.get("dry_run", True))
        return {"squad_plan": result, "agents": getattr(result, "agents", [])}

    def step_execute(state: dict) -> dict:
        plan = state.get("squad_plan")
        if plan is None:
            return {"status": "skipped", "reason": "no_plan"}
        result = execute_squad_run(plan, dry_run=state.get("dry_run", True))
        return {"status": getattr(result, "status", "done"), "run_id": getattr(result, "run_id", "")}

    steps = [
        WorkflowStep(id="plan_squad",    name="Plan Squad",    fn=step_plan),
        WorkflowStep(id="execute_squad", name="Execute Squad", fn=step_execute),
    ]
    return wf.execute(steps, initial_state={**squad_request, "dry_run": dry_run}, dry_run=dry_run)


def autonomous_execution_as_workflow(
    config_data: dict[str, Any],
    *,
    dry_run: bool = True,
    provider: Optional[WorkflowProvider] = None,
) -> WorkflowResult:
    """Run autonomous_execution via WorkflowProvider.

    Replaces: AutonomousExecutor().execute(config)
    Preserves checkpoint/circuit-breaker logic inside the step fn.
    """
    from src.autonomous_execution.executor import AutonomousExecutor
    from src.autonomous_execution.models import AutonomousConfig

    wf = provider or SequentialWorkflowProvider()

    def step_configure(state: dict) -> dict:
        cfg = AutonomousConfig(**{k: v for k, v in state.items() if k in AutonomousConfig.__dataclass_fields__}) \
            if hasattr(AutonomousConfig, "__dataclass_fields__") else AutonomousConfig()
        return {"config": cfg, "ready": True}

    def step_execute(state: dict) -> dict:
        cfg = state.get("config")
        if cfg is None or state.get("dry_run", True):
            return {"status": "dry_run", "actions": []}
        executor = AutonomousExecutor(config=cfg)
        result = executor.execute()
        return {"status": getattr(result, "status", "done"), "actions": getattr(result, "actions_taken", [])}

    steps = [
        WorkflowStep(id="configure", name="Configure Autonomous", fn=step_configure),
        WorkflowStep(id="execute",   name="Execute Autonomous",   fn=step_execute),
    ]
    return wf.execute(steps, initial_state={**config_data, "dry_run": dry_run}, dry_run=dry_run)


def skill_execution_as_workflow(
    request_data: dict[str, Any],
    *,
    dry_run: bool = True,
    provider: Optional[WorkflowProvider] = None,
) -> WorkflowResult:
    """Run skill_execution pipeline via WorkflowProvider.

    Replaces: SkillExecutionRequest → BoundaryChecker → PermissionGate → DryRunExecutor
    All 4 boundary/permission stages become named workflow steps.
    """
    from src.skill_execution.request import SkillExecutionRequest
    from src.skill_execution.boundaries import BoundaryChecker
    from src.skill_execution.permission_gate import PermissionGate
    from src.skill_execution.dryrun_executor import DryRunExecutor

    wf = provider or SequentialWorkflowProvider()
    checker = BoundaryChecker()
    gate = PermissionGate()
    executor = DryRunExecutor()

    def step_validate(state: dict) -> dict:
        req = SkillExecutionRequest(**{k: v for k, v in state.items()
                                       if k in SkillExecutionRequest.__dataclass_fields__}) \
            if hasattr(SkillExecutionRequest, "__dataclass_fields__") \
            else SkillExecutionRequest(skill_id=state.get("skill_id", ""))
        result = checker.check(req)
        return {"request": req, "boundary_ok": getattr(result, "passed", True), "boundary_result": result}

    def step_permission(state: dict) -> dict:
        req = state.get("request")
        if req is None or not state.get("boundary_ok", True):
            return {"permission_ok": False, "reason": "boundary_failed"}
        result = gate.evaluate(req)
        return {"permission_ok": getattr(result, "approved", True), "permission_result": result}

    def step_execute(state: dict) -> dict:
        if not state.get("permission_ok", True) or state.get("dry_run", True):
            return {"status": "dry_run" if state.get("dry_run", True) else "blocked"}
        req = state.get("request")
        result = executor.execute(req)
        return {"status": getattr(result, "status", "done").value
                if hasattr(getattr(result, "status", ""), "value") else "done",
                "output": getattr(result, "output", {})}

    steps = [
        WorkflowStep(id="validate",   name="Validate Boundaries", fn=step_validate),
        WorkflowStep(id="permission", name="Check Permission",    fn=step_permission),
        WorkflowStep(id="execute",    name="Execute Skill",       fn=step_execute),
    ]
    return wf.execute(steps, initial_state={**request_data, "dry_run": dry_run}, dry_run=dry_run)
