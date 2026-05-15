"""Tests for execution graph retry policy."""
from __future__ import annotations

import pytest

from src.execution_graph.retry import (
    BackoffStrategy,
    RetryConfig,
    RetryPolicy,
    RETRYABLE_STATUSES,
)
from datetime import datetime, timezone

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
    edges: list[tuple[str, str]] = []
    for n in steps:
        for dep in n.depends_on:
            edges.append((dep, n.step_id))
    top_order = [n.step_id for n in steps]
    return ExecutionGraph(
        graph_id=_make_graph_id(),
        request="test request",
        squad_id="sq1",
        task_plan_id="tp1",
        nodes=steps,
        edges=edges,
        topological_order=top_order,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


# ── RetryConfig ──────────────────────────────────────────────

class TestRetryConfig:
    def test_defaults(self):
        c = RetryConfig()
        assert c.max_retries == 3
        assert c.backoff == BackoffStrategy.EXPONENTIAL
        assert c.base_delay_seconds == 1.0
        assert c.max_delay_seconds == 60.0
        assert "failed" in c.retryable_statuses

    def test_fixed_backoff_delay(self):
        c = RetryConfig(backoff=BackoffStrategy.FIXED, base_delay_seconds=5.0)
        assert c.delay_for_attempt(1) == 5.0
        assert c.delay_for_attempt(3) == 5.0

    def test_linear_backoff_delay(self):
        c = RetryConfig(backoff=BackoffStrategy.LINEAR, base_delay_seconds=2.0, max_delay_seconds=10.0)
        assert c.delay_for_attempt(1) == 2.0
        assert c.delay_for_attempt(3) == 6.0
        assert c.delay_for_attempt(10) == 10.0  # capped

    def test_exponential_backoff_delay(self):
        c = RetryConfig(backoff=BackoffStrategy.EXPONENTIAL, base_delay_seconds=1.0)
        assert c.delay_for_attempt(1) == 1.0
        assert c.delay_for_attempt(2) == 2.0
        assert c.delay_for_attempt(3) == 4.0
        assert c.delay_for_attempt(4) == 8.0

    def test_exponential_max_delay_cap(self):
        c = RetryConfig(backoff=BackoffStrategy.EXPONENTIAL, base_delay_seconds=1.0, max_delay_seconds=3.0)
        assert c.delay_for_attempt(1) == 1.0
        assert c.delay_for_attempt(2) == 2.0
        assert c.delay_for_attempt(3) == 3.0
        assert c.delay_for_attempt(10) == 3.0

    def test_to_dict_roundtrip(self):
        c = RetryConfig(max_retries=5, backoff=BackoffStrategy.LINEAR, base_delay_seconds=2.0)
        restored = RetryConfig.from_dict(c.to_dict())
        assert restored.max_retries == 5
        assert restored.backoff == BackoffStrategy.LINEAR
        assert restored.base_delay_seconds == 2.0

    def test_zero_retries(self):
        c = RetryConfig(max_retries=0)
        assert c.max_retries == 0


# ── RetryPolicy ──────────────────────────────────────────────

class TestRetryPolicy:
    def test_default_policy(self):
        p = RetryPolicy(config=RetryConfig(max_retries=3))
        assert p.get_config("any_step").max_retries == 3

    def test_per_step_override(self):
        default = RetryConfig(max_retries=3)
        override = RetryConfig(max_retries=1, backoff=BackoffStrategy.FIXED)
        p = RetryPolicy(config=default, per_step={"step_x": override})
        assert p.get_config("step_x").max_retries == 1
        assert p.get_config("step_y").max_retries == 3

    def test_is_retryable(self):
        p = RetryPolicy(config=RetryConfig())
        assert p.is_retryable("failed") is True
        assert p.is_retryable("timeout") is True
        assert p.is_retryable("done") is False

    def test_to_dict_roundtrip(self):
        default = RetryConfig(max_retries=2)
        override = RetryConfig(max_retries=0)
        p = RetryPolicy(config=default, per_step={"s1": override})
        restored = RetryPolicy.from_dict(p.to_dict())
        assert restored.config.max_retries == 2
        assert restored.per_step["s1"].max_retries == 0


# ── Runner integration ───────────────────────────────────────

class TestRunnerRetryIntegration:
    def test_no_retry_policy_fails_immediately(self):
        """Without retry policy, a step fails on first attempt."""
        steps = [
            _make_step("s1", "Step 1"),
            _make_step("s2", "Step 2", depends_on=["s1"]),
        ]
        graph = _make_graph(steps=steps)
        run = run_graph_dry(graph, fail_at="s1")
        assert run.status == "failed"
        assert run.step_states["s1"] == "failed"
        assert run.step_states["s2"] == "skipped"
        # No retry messages
        retry_logs = [l for l in run.logs if "retry" in l.message.lower()]
        assert len(retry_logs) == 0

    def test_retry_policy_retries_failed_step(self):
        """With retry policy, a failed step is retried up to max_retries."""
        steps = [
            _make_step("s1", "Step 1"),
            _make_step("s2", "Step 2", depends_on=["s1"]),
        ]
        graph = _make_graph(steps=steps)
        policy = RetryPolicy(config=RetryConfig(max_retries=3, backoff=BackoffStrategy.FIXED))
        run = run_graph_dry(graph, fail_at="s1", retry_policy=policy)
        assert run.status == "failed"
        assert run.step_states["s1"] == "failed"
        # Should have 3 retry log entries
        retry_logs = [l for l in run.logs if "retry" in l.message.lower()]
        assert len(retry_logs) == 3

    def test_retry_logs_show_backoff_delay(self):
        steps = [_make_step("s1", "Step 1")]
        graph = _make_graph(steps=steps)
        policy = RetryPolicy(config=RetryConfig(max_retries=2, backoff=BackoffStrategy.EXPONENTIAL, base_delay_seconds=1.0))
        run = run_graph_dry(graph, fail_at="s1", retry_policy=policy)
        retry_logs = [l for l in run.logs if "retry" in l.message.lower()]
        assert len(retry_logs) == 2
        assert "delay=1.0s" in retry_logs[0].message
        assert "delay=2.0s" in retry_logs[1].message

    def test_retry_log_mentions_exhaustion(self):
        steps = [_make_step("s1", "Step 1")]
        graph = _make_graph(steps=steps)
        policy = RetryPolicy(config=RetryConfig(max_retries=1))
        run = run_graph_dry(graph, fail_at="s1", retry_policy=policy)
        final_fail = [l for l in run.logs if "FAILED after" in l.message]
        assert len(final_fail) == 1
        assert "2 attempts" in final_fail[0].message

    def test_successful_step_no_retries(self):
        """A step that succeeds does not trigger retries."""
        steps = [_make_step("s1", "Step 1")]
        graph = _make_graph(steps=steps)
        policy = RetryPolicy(config=RetryConfig(max_retries=5))
        run = run_graph_dry(graph, retry_policy=policy)
        assert run.status == "done"
        retry_logs = [l for l in run.logs if "retry" in l.message.lower()]
        assert len(retry_logs) == 0

    def test_per_step_override_higher_retries(self):
        """A specific step can have higher retry count than default."""
        steps = [
            _make_step("s1", "Step 1"),
            _make_step("s2", "Step 2", depends_on=["s1"]),
        ]
        graph = _make_graph(steps=steps)
        policy = RetryPolicy(
            config=RetryConfig(max_retries=1),
            per_step={"s1": RetryConfig(max_retries=5)},
        )
        run = run_graph_dry(graph, fail_at="s1", retry_policy=policy)
        retry_logs = [l for l in run.logs if "retry" in l.message.lower()]
        assert len(retry_logs) == 5
