"""Security characterization for Onda 8 Lego bridge integration."""
from __future__ import annotations

from src.agentic.skill_runner_bridge import SkillRunnerBridge
from src.execution_graph.models import ExecutionGraph, StepNode, StepStatus
from src.execution_graph.runner import run_graph_real
from src.legos.registry import default_registry


def _make_code_graph(goal: str) -> ExecutionGraph:
    node = StepNode(
        step_id="s0",
        task_id="t0",
        title="Execute code task",
        description="Run code executor through graph bridge",
        role_id="code_executor",
        assigned_role="code_executor",
        expected_output=goal,
        depends_on=[],
    )
    return ExecutionGraph(
        graph_id="g_code_security_01",
        squad_id="sq_code_security_01",
        task_plan_id="tp_code_security_01",
        request="security check for code executor bridge",
        nodes=[node],
        edges=[],
        topological_order=["s0"],
        created_at="2026-01-01T00:00:00Z",
    )


def test_run_graph_real_blocks_unsafe_goal_payload_via_lego_bridge(monkeypatch):
    """RCE hardening must still hold when code executor is called via run_graph_real()."""
    monkeypatch.setattr(
        "src.legos.code_executor_lego.CodeExecutorLego.health_check",
        lambda _self: False,
    )

    def _should_not_run(*_args, **_kwargs):
        raise AssertionError("subprocess.run should not be called for unsafe payload")

    monkeypatch.setattr("subprocess.run", _should_not_run)

    bridge = SkillRunnerBridge(dry_run=False, lego_registry=default_registry())
    graph = _make_code_graph("gerar script\nimport os; os.system('echo pwned')")

    step_run = run_graph_real(graph, bridge)

    assert step_run.status == "failed"
    assert step_run.step_states["s0"] == StepStatus.FAILED.value
    assert any(
        "unsafe_goal_payload" in log.message
        for log in step_run.logs
        if log.step_id == "s0"
    )
