"""Tests for execution graph circuit breaker."""
from __future__ import annotations

import pytest

from src.execution_graph.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitState,
)
from src.execution_graph.models import (
    ExecutionGraph,
    StepNode,
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


def _simple_graph(steps: list[StepNode]) -> ExecutionGraph:
    from datetime import datetime, timezone
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


# ── CircuitBreaker unit tests ───────────────────────────────

class TestCircuitBreaker:
    def test_defaults(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_threshold == 5
        assert cb.cooldown_seconds == 30.0
        assert cb.failure_count == 0

    def test_before_call_closed_allows(self):
        cb = CircuitBreaker()
        assert cb.before_call() is True

    def test_stays_closed_under_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(2):
            cb.on_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 2

    def test_trips_open_at_threshold(self):
        cb = CircuitBreaker(failure_threshold=2)
        cb.on_failure()
        cb.on_failure()
        assert cb.state == CircuitState.OPEN

    def test_open_blocks_calls(self):
        cb = CircuitBreaker(failure_threshold=1)
        cb.on_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.before_call() is False

    def test_half_open_probe_succeeds(self):
        cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=0)
        cb.on_failure()
        assert cb.state == CircuitState.OPEN
        # Cooldown is 0s, so instantly half-open
        assert cb.before_call() is True
        assert cb.state == CircuitState.HALF_OPEN
        cb.on_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_half_open_failure_retrips(self):
        cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=0)
        cb.on_failure()
        cb.before_call()  # enters half_open
        cb.on_failure()  # fails the probe
        assert cb.state == CircuitState.OPEN

    def test_only_one_half_open_probe_by_default(self):
        cb = CircuitBreaker(failure_threshold=1, cooldown_seconds=0)
        cb.on_failure()
        assert cb.before_call() is True  # probe 1
        assert cb.before_call() is False  # no more probes till probe resolves

    def test_reset(self):
        cb = CircuitBreaker(failure_threshold=1)
        cb.on_failure()
        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_success_resets_failure_count_in_closed(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.on_failure()
        cb.on_failure()
        cb.on_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_is_open(self):
        cb = CircuitBreaker(failure_threshold=1)
        assert cb.is_open() is False
        cb.on_failure()
        assert cb.is_open() is True

    def test_to_dict_roundtrip(self):
        cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=15.0)
        cb.on_failure()
        cb.on_failure()
        restored = CircuitBreaker.from_dict(cb.to_dict())
        assert restored.failure_threshold == 3
        assert restored.cooldown_seconds == 15.0
        assert restored.failure_count == 2


# ── CircuitBreakerRegistry tests ─────────────────────────────

class TestCircuitBreakerRegistry:
    def test_creates_breaker_on_demand(self):
        reg = CircuitBreakerRegistry()
        breaker = reg.get("step_a")
        assert isinstance(breaker, CircuitBreaker)
        assert breaker.state == CircuitState.CLOSED

    def test_before_step_allows_normally(self):
        reg = CircuitBreakerRegistry()
        assert reg.before_step("s1") is True

    def test_on_step_failure_accumulates(self):
        reg = CircuitBreakerRegistry(default_config=CircuitBreaker(failure_threshold=2))
        reg.on_step_failure("s1")
        reg.on_step_failure("s1")
        assert reg.get("s1").state == CircuitState.OPEN

    def test_before_step_blocks_after_trip(self):
        reg = CircuitBreakerRegistry(default_config=CircuitBreaker(failure_threshold=1))
        reg.on_step_failure("s1")
        assert reg.before_step("s1") is False

    def test_on_step_success_resets(self):
        reg = CircuitBreakerRegistry(default_config=CircuitBreaker(failure_threshold=3))
        reg.on_step_failure("s1")
        reg.on_step_failure("s1")
        reg.on_step_success("s1")
        assert reg.get("s1").failure_count == 0

    def test_independent_per_step(self):
        reg = CircuitBreakerRegistry(default_config=CircuitBreaker(failure_threshold=1))
        reg.on_step_failure("s1")
        assert reg.get("s1").state == CircuitState.OPEN
        assert reg.get("s2").state == CircuitState.CLOSED

    def test_reset_all(self):
        reg = CircuitBreakerRegistry(default_config=CircuitBreaker(failure_threshold=1))
        reg.on_step_failure("s1")
        reg.on_step_failure("s2")
        reg.reset_all()
        assert reg.get("s1").state == CircuitState.CLOSED
        assert reg.get("s2").state == CircuitState.CLOSED

    def test_to_dict(self):
        reg = CircuitBreakerRegistry(default_config=CircuitBreaker(failure_threshold=3))
        reg.on_step_failure("s1")
        d = reg.to_dict()
        assert "breakers" in d
        assert "default_config" in d
        assert d["breakers"]["s1"]["failure_count"] == 1


# ── Runner integration ───────────────────────────────────────

class TestRunnerCircuitBreakerIntegration:
    def test_circuit_breaker_blocks_step_when_open(self):
        steps = [_make_step("s1", "Step 1")]
        graph = _simple_graph(steps)

        reg = CircuitBreakerRegistry(default_config=CircuitBreaker(failure_threshold=1))
        # Trip the circuit for s1
        reg.on_step_failure("s1")

        run = run_graph_dry(graph, circuit_registry=reg)
        assert run.step_states["s1"] == "skipped"
        blocked_logs = [l for l in run.logs if "blocked" in l.message.lower()]
        assert len(blocked_logs) == 1
        assert "circuit open" in blocked_logs[0].message

    def test_circuit_allows_when_closed(self):
        steps = [_make_step("s1", "Step 1")]
        graph = _simple_graph(steps)
        reg = CircuitBreakerRegistry()
        run = run_graph_dry(graph, circuit_registry=reg)
        assert run.step_states["s1"] == "done"

    def test_failure_increments_circuit_count(self):
        steps = [_make_step("s1", "Step 1")]
        graph = _simple_graph(steps)
        reg = CircuitBreakerRegistry()

        run = run_graph_dry(graph, fail_at="s1", circuit_registry=reg)
        assert run.step_states["s1"] == "failed"
        assert reg.get("s1").failure_count == 1

    def test_success_resets_circuit(self):
        steps = [
            _make_step("s1", "Step 1"),
            _make_step("s2", "Step 2"),
        ]
        graph = _simple_graph(steps)
        reg = CircuitBreakerRegistry(default_config=CircuitBreaker(failure_threshold=3))
        reg.on_step_failure("s1")
        reg.on_step_failure("s1")

        run = run_graph_dry(graph, circuit_registry=reg)
        assert run.step_states["s1"] == "done"
        assert reg.get("s1").failure_count == 0

    def test_circuit_breaker_with_retry(self):
        """Circuit breaker counts each retry attempt failure."""
        steps = [_make_step("s1", "Step 1")]
        graph = _simple_graph(steps)

        from src.execution_graph.retry import RetryPolicy, RetryConfig, BackoffStrategy
        reg = CircuitBreakerRegistry(default_config=CircuitBreaker(failure_threshold=2))
        rp = RetryPolicy(config=RetryConfig(max_retries=2, backoff=BackoffStrategy.FIXED))

        run = run_graph_dry(graph, fail_at="s1", retry_policy=rp, circuit_registry=reg)
        assert run.status == "failed"
        # Circuit breaker reports 1 failure (per step execution, not per retry attempt)
        assert reg.get("s1").failure_count == 1

    def test_independent_circuits_per_step_in_graph(self):
        steps = [
            _make_step("s1", "Step 1"),
            _make_step("s2", "Step 2", depends_on=["s1"]),
        ]
        graph = _simple_graph(steps)
        reg = CircuitBreakerRegistry(default_config=CircuitBreaker(failure_threshold=1))

        # Trip only s2
        reg.on_step_failure("s2")

        run = run_graph_dry(graph, circuit_registry=reg)
        # s1 runs fine
        assert run.step_states["s1"] == "done"
        # s2 is blocked by circuit
        assert run.step_states["s2"] == "skipped"
