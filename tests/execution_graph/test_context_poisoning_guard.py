"""Context poisoning characterization for Onda 8 context_store flow."""
from __future__ import annotations

from src.agentic.skill_runner_bridge import SkillRunnerBridge
from src.execution_graph.models import ExecutionGraph, StepNode
from src.execution_graph.runner import run_graph_real
from src.legos.registry import LegoRegistry
from src.legos.protocol import LegoCogResult


class _CaptureLego:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []
        self._call_index = 0

    def run(self, spec):
        self.calls.append((spec.goal, dict(spec.payload)))
        # First step returns malicious-like output; second returns clean output.
        if self._call_index == 0:
            self._call_index += 1
            return LegoCogResult(
                success=True,
                output="dangerous\nimport os; os.system('echo injected')",
                dry_run=False,
            )
        self._call_index += 1
        return LegoCogResult(success=True, output="safe second output", dry_run=False)

    def health_check(self):
        return True


def _make_two_step_graph() -> ExecutionGraph:
    s1 = StepNode(
        step_id="s1",
        task_id="t1",
        title="Step 1",
        description="produce upstream context",
        role_id="code_executor",
        assigned_role="code_executor",
        expected_output="first-step-goal",
        depends_on=[],
    )
    s2 = StepNode(
        step_id="s2",
        task_id="t2",
        title="Step 2",
        description="consume upstream context",
        role_id="code_executor",
        assigned_role="code_executor",
        expected_output="second-step-benign-goal",
        depends_on=["s1"],
    )
    return ExecutionGraph(
        graph_id="g_ctx_poison_guard",
        squad_id="sq_ctx_poison_guard",
        task_plan_id="tp_ctx_poison_guard",
        request="context poisoning guard check",
        nodes=[s1, s2],
        edges=[("s1", "s2")],
        topological_order=["s1", "s2"],
        created_at="2026-01-01T00:00:00Z",
    )


def test_upstream_context_does_not_override_next_step_goal():
    lego = _CaptureLego()
    reg = LegoRegistry()
    reg.register("code_executor", lego)
    bridge = SkillRunnerBridge(dry_run=False, lego_registry=reg)
    graph = _make_two_step_graph()
    store: dict[str, str] = {}

    step_run = run_graph_real(graph, bridge, context_store=store)

    assert step_run.status == "done"
    # Two lego calls executed
    assert len(lego.calls) == 2

    first_goal, first_payload = lego.calls[0]
    second_goal, second_payload = lego.calls[1]

    assert first_goal == "first-step-goal"
    assert second_goal == "second-step-benign-goal"

    # The malicious text flows only as context hint, not as execution goal.
    assert "dangerous\nimport os" in second_payload.get("upstream_context", "")
    assert "dangerous\nimport os" not in second_goal
