"""Tests for execution graph rollback plan."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.execution_graph.rollback import (
    RollbackAction,
    RollbackPlan,
    RollbackStatus,
)
from src.execution_graph.models import (
    ExecutionGraph,
    StepNode,
    StepStatus,
    _make_graph_id,
)
from src.execution_graph.runner import run_graph_dry


def _make_step(step_id: str, title: str, depends_on: list[str] | None = None) -> StepNode:
    return StepNode(
        step_id=step_id,
        task_id="task_1",
        role_id="role_a",
        title=title,
        description=f"Description for {title}",
        expected_output=f"Output from {title}",
        depends_on=depends_on or [],
    )


def _make_graph(steps: list[StepNode]) -> ExecutionGraph:
    edges = []
    for n in steps:
        for dep in n.depends_on:
            edges.append((dep, n.step_id))
    return ExecutionGraph(
        graph_id=_make_graph_id(),
        request="test",
        squad_id="sq1",
        task_plan_id="tp1",
        nodes=steps,
        edges=edges,
        topological_order=[n.step_id for n in steps],
        created_at=datetime.now(timezone.utc).isoformat(),
    )


# ── RollbackAction ───────────────────────────────────────────

class TestRollbackAction:
    def test_defaults(self):
        a = RollbackAction(
            action_id="rb_1",
            step_id="s1",
            description="Undo deploy",
            target="deployment_v1",
        )
        assert a.action_id == "rb_1"
        assert a.step_id == "s1"
        assert a.status == RollbackStatus.PENDING

    def test_to_dict_roundtrip(self):
        a = RollbackAction(
            action_id="rb_x",
            step_id="s2",
            description="Revert DB migration",
            target="migration_003",
        )
        d = a.to_dict()
        restored = RollbackAction.from_dict(d)
        assert restored.action_id == "rb_x"
        assert restored.step_id == "s2"
        assert restored.description == "Revert DB migration"
        assert restored.target == "migration_003"
        assert restored.status == RollbackStatus.PENDING

    def test_from_dict_preserves_status(self):
        a = RollbackAction(
            action_id="rb_done",
            step_id="s3",
            description="x",
            target="y",
            status=RollbackStatus.EXECUTED,
        )
        restored = RollbackAction.from_dict(a.to_dict())
        assert restored.status == RollbackStatus.EXECUTED


# ── RollbackPlan ─────────────────────────────────────────────

class TestRollbackPlan:
    def test_empty_plan(self):
        p = RollbackPlan(plan_id="rp1", graph_run_id="gr1")
        assert p.is_empty() is True

    def test_add_action(self):
        p = RollbackPlan(plan_id="rp1", graph_run_id="gr1")
        p.add_action(RollbackAction("a1", "s1", "Undo", "target1"))
        assert p.is_empty() is False
        assert len(p.actions) == 1

    def test_actions_for_step(self):
        p = RollbackPlan(plan_id="rp1", graph_run_id="gr1")
        p.add_action(RollbackAction("a1", "s1", "Undo", "t1"))
        p.add_action(RollbackAction("a2", "s2", "Undo", "t2"))
        p.add_action(RollbackAction("a3", "s1", "Cleanup", "t3"))
        assert len(p.actions_for_step("s1")) == 2
        assert len(p.actions_for_step("s3")) == 0

    def test_pending_actions(self):
        p = RollbackPlan(plan_id="rp1", graph_run_id="gr1")
        p.add_action(RollbackAction("a1", "s1", "Undo", "t1"))
        p.add_action(RollbackAction("a2", "s2", "Undo", "t2",
                                     status=RollbackStatus.EXECUTED))
        assert len(p.pending_actions()) == 1

    def test_execute_dry_rolls_back_completed_steps(self):
        p = RollbackPlan(plan_id="rp1", graph_run_id="gr1")
        p.add_action(RollbackAction("a1", "s1", "Undo step 1", "output_1"))
        p.add_action(RollbackAction("a2", "s2", "Undo step 2", "output_2"))
        p.add_action(RollbackAction("a3", "s3", "Undo step 3", "output_3"))

        # Only s1 and s3 completed
        log = p.execute_dry(completed_step_ids={"s1", "s3"})

        assert p.actions_for_step("s1")[0].status == RollbackStatus.EXECUTED
        assert p.actions_for_step("s2")[0].status == RollbackStatus.SKIPPED
        assert p.actions_for_step("s3")[0].status == RollbackStatus.EXECUTED

        executed = [e for e in log if e["status"] == "executed"]
        skipped = [e for e in log if e["status"] == "skipped"]
        assert len(executed) == 2
        assert len(skipped) == 1

    def test_execute_dry_empty_completed_set(self):
        p = RollbackPlan(plan_id="rp1", graph_run_id="gr1")
        p.add_action(RollbackAction("a1", "s1", "Undo", "t1"))
        log = p.execute_dry(completed_step_ids=set())
        assert all(e["status"] == "skipped" for e in log)

    def test_build_for_graph(self):
        steps = [
            _make_step("s1", "Step 1"),
            _make_step("s2", "Step 2", depends_on=["s1"]),
        ]
        graph = _make_graph(steps)
        p = RollbackPlan.build_for_graph("rp1", "gr1", graph)
        assert len(p.actions) == 2
        assert p.actions[0].step_id == "s1"
        assert p.actions[1].step_id == "s2"

    def test_to_dict_roundtrip(self):
        p = RollbackPlan(plan_id="rp1", graph_run_id="gr1")
        p.add_action(RollbackAction("a1", "s1", "Undo", "t1"))
        p.add_action(RollbackAction("a2", "s2", "Clean", "t2"))
        restored = RollbackPlan.from_dict(p.to_dict())
        assert restored.plan_id == "rp1"
        assert restored.graph_run_id == "gr1"
        assert len(restored.actions) == 2


# ── Runner integration ───────────────────────────────────────

class TestRunnerRollbackIntegration:
    def test_rollback_executes_on_failure(self):
        """When a step fails, completed upstream steps should be rolled back."""
        steps = [
            _make_step("s1", "Step 1"),
            _make_step("s2", "Step 2", depends_on=["s1"]),
            _make_step("s3", "Step 3", depends_on=["s2"]),
        ]
        graph = _make_graph(steps)

        rp = RollbackPlan.build_for_graph("rp1", "gr1", graph)
        run = run_graph_dry(graph, fail_at="s2", rollback_plan=rp)

        assert run.status == "failed"
        # s1 completed, should be rolled back
        assert run.step_states["s1"] == "done"
        rollback_logs = [l for l in run.logs if l.role_id == "rollback"]
        assert len(rollback_logs) > 0
        executed_rb = [l for l in rollback_logs if "executed" in l.status]
        assert len(executed_rb) >= 1  # at least s1 rolled back

    def test_no_rollback_on_success(self):
        """When graph completes successfully, no rollback is executed."""
        steps = [
            _make_step("s1", "Step 1"),
            _make_step("s2", "Step 2", depends_on=["s1"]),
        ]
        graph = _make_graph(steps)

        rp = RollbackPlan.build_for_graph("rp1", "gr1", graph)
        run = run_graph_dry(graph, rollback_plan=rp)

        assert run.status == "done"
        rollback_logs = [l for l in run.logs if l.role_id == "rollback"]
        assert len(rollback_logs) == 0

    def test_no_rollback_when_plan_not_provided(self):
        """Without a rollback plan, failure just skips downstream, no rollback."""
        steps = [
            _make_step("s1", "Step 1"),
            _make_step("s2", "Step 2", depends_on=["s1"]),
        ]
        graph = _make_graph(steps)

        run = run_graph_dry(graph, fail_at="s2")
        assert run.status == "failed"
        rollback_logs = [l for l in run.logs if l.role_id == "rollback"]
        assert len(rollback_logs) == 0

    def test_rollback_skips_non_completed_steps(self):
        """Steps that didn't complete (pending, running before failure) are not rolled back."""
        steps = [
            _make_step("s1", "Step 1"),
            _make_step("s2", "Step 2", depends_on=["s1"]),
            _make_step("s3", "Step 3", depends_on=["s2"]),
        ]
        graph = _make_graph(steps)

        rp = RollbackPlan.build_for_graph("rp1", "gr1", graph)
        run = run_graph_dry(graph, fail_at="s2", rollback_plan=rp)

        # s3 was skipped (never ran), should not be rolled back
        assert run.step_states["s3"] == "skipped"
        rollback_logs = [l for l in run.logs if l.role_id == "rollback"]
        skipped_rb = [l for l in rollback_logs if "skipped" in l.status]
        # s3's rollback action should be skipped
        assert any("s3" in l.message for l in skipped_rb)

    def test_rollback_with_retry_and_circuit_breaker(self):
        """Full integration: retry + circuit breaker + rollback."""
        steps = [
            _make_step("s1", "Step 1"),
            _make_step("s2", "Step 2", depends_on=["s1"]),
        ]
        graph = _make_graph(steps)

        from src.execution_graph.retry import RetryPolicy, RetryConfig, BackoffStrategy
        from src.execution_graph.circuit_breaker import CircuitBreakerRegistry, CircuitBreaker

        retry = RetryPolicy(config=RetryConfig(max_retries=2, backoff=BackoffStrategy.FIXED))
        cb = CircuitBreakerRegistry(default_config=CircuitBreaker(failure_threshold=3))
        rollback = RollbackPlan.build_for_graph("rp_full", "gr1", graph)

        run = run_graph_dry(
            graph,
            fail_at="s2",
            retry_policy=retry,
            circuit_registry=cb,
            rollback_plan=rollback,
        )

        assert run.status == "failed"
        assert run.step_states["s1"] == "done"
        assert run.step_states["s2"] == "failed"

        # Circuit breaker reports the failure
        assert cb.get("s2").failure_count == 1

        # Rollback executed for s1
        rollback_logs = [l for l in run.logs if l.role_id == "rollback"]
        executed = [l for l in rollback_logs if "executed" in l.status]
        assert len(executed) >= 1

    def test_rollback_with_skip_done(self):
        """Previously done steps from resume should not be rolled back."""
        steps = [
            _make_step("s1", "Step 1"),
            _make_step("s2", "Step 2", depends_on=["s1"]),
            _make_step("s3", "Step 3", depends_on=["s2"]),
        ]
        graph = _make_graph(steps)

        rp = RollbackPlan.build_for_graph("rp1", "gr1", graph)
        # s1 was done in a previous run
        run = run_graph_dry(graph, fail_at="s3", skip_done={"s1"}, rollback_plan=rp)

        assert run.status == "failed"
        # s1 was already done (from skip_done), should not be rolled back
        rollback_logs = [l for l in run.logs if l.role_id == "rollback"]
        executed = [l for l in rollback_logs if "executed" in l.status]
        skipped_rb = [l for l in rollback_logs if "skipped" in l.status]
        # Only s2 gets rolled back (s1 was pre-existing done, s3 never ran)
        assert len(executed) == 1, f"Expected 1 executed rollback, got {len(executed)}: {[l.message for l in rollback_logs]}"
        assert "s2" in executed[0].step_id
        # s1 should be skipped (was in skip_done)
        assert any("s1" in l.step_id for l in skipped_rb)
