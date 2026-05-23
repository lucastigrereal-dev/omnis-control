"""Additional branch tests for execution_graph runner helper functions."""
from __future__ import annotations

from dataclasses import dataclass

from src.execution_graph.models import StepNode, StepStatus, StepRunLog
from src.execution_graph.retry import RetryConfig, RetryPolicy
from src.execution_graph.runner import _execute_real_step_result, _resolve_dry_step_result


def _node(step_id: str = "s1") -> StepNode:
    return StepNode(
        step_id=step_id,
        task_id=f"task_{step_id}",
        role_id="role_a",
        title=f"Step {step_id}",
        description="Test step",
        expected_output="output.md",
        depends_on=[],
    )


@dataclass
class _Result:
    status: str
    output: str = ""
    error: str = ""


class _AlwaysFailBridge:
    def execute_entry(self, entry):
        return _Result(status="failed", error="boom")


class _FailThenSuccessBridge:
    def __init__(self) -> None:
        self.calls = 0

    def execute_entry(self, entry):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("temporary")
        return _Result(status="success", output="ok-output")


def test_resolve_dry_step_result_failed_with_retry_message():
    node = _node("s_fail")
    logs: list[StepRunLog] = []
    retry_policy = RetryPolicy(
        config=RetryConfig(max_retries=2),
        per_step={"s_fail": RetryConfig(max_retries=2)},
    )

    status, message = _resolve_dry_step_result(
        node=node,
        fail_at="s_fail",
        retry_policy=retry_policy,
        logs=logs,
    )

    assert status == StepStatus.FAILED
    assert "FAILED after 3 attempts" in message
    assert len(logs) == 2
    assert all("retry" in log.message for log in logs)


def test_execute_real_step_result_failed_after_retries():
    node = _node("s1")
    logs: list[StepRunLog] = []
    retry_policy = RetryPolicy(
        config=RetryConfig(max_retries=2),
        per_step={"s1": RetryConfig(max_retries=2)},
    )

    status, message = _execute_real_step_result(
        node=node,
        entry=object(),
        bridge=_AlwaysFailBridge(),
        retry_policy=retry_policy,
        logs=logs,
    )

    assert status == StepStatus.FAILED
    assert "after 3 attempts" in message
    assert len(logs) == 2
    assert all(log.status == StepStatus.RUNNING.value for log in logs)


def test_execute_real_step_result_recovers_after_retry():
    node = _node("s1")
    logs: list[StepRunLog] = []
    retry_policy = RetryPolicy(
        config=RetryConfig(max_retries=2),
        per_step={"s1": RetryConfig(max_retries=2)},
    )
    bridge = _FailThenSuccessBridge()

    status, message = _execute_real_step_result(
        node=node,
        entry=object(),
        bridge=bridge,
        retry_policy=retry_policy,
        logs=logs,
    )

    assert status == StepStatus.DONE
    assert "completed" in message
    assert bridge.calls == 2
    assert len(logs) == 1

