"""Tests for WorkflowProvider — SequentialWorkflowProvider."""
import pytest
from src.providers.workflow import SequentialWorkflowProvider, WorkflowStep, WorkflowResult


def make_step(id: str, name: str, output: object = None, raises: bool = False) -> WorkflowStep:
    def fn(state):
        if raises:
            raise RuntimeError(f"Step {id} failed")
        return {"output": output or f"result_{id}"}
    return WorkflowStep(id=id, name=name, fn=fn)


class TestSequentialWorkflowProvider:
    def test_health_ok(self):
        assert SequentialWorkflowProvider().health_check().ok

    def test_dry_run_completes_all_steps(self):
        p = SequentialWorkflowProvider()
        steps = [make_step("s1", "Step 1"), make_step("s2", "Step 2")]
        result = p.execute(steps, dry_run=True)
        assert result.success
        assert result.steps_completed == 2
        assert result.steps_total == 2

    def test_dry_run_does_not_call_fn(self):
        called = []
        def fn(state):
            called.append(True)
            return {}
        step = WorkflowStep(id="s", name="s", fn=fn)
        SequentialWorkflowProvider().execute([step], dry_run=True)
        assert called == []

    def test_real_run_executes_fn(self):
        called = []
        def fn(state):
            called.append(True)
            return {"done": True}
        step = WorkflowStep(id="s", name="s", fn=fn)
        result = SequentialWorkflowProvider().execute([step], dry_run=False)
        assert called == [True]
        assert result.success

    def test_real_run_passes_state(self):
        def fn1(state):
            return {"x": 10}
        def fn2(state):
            return {"y": state["x"] * 2}
        steps = [
            WorkflowStep(id="s1", name="s1", fn=fn1),
            WorkflowStep(id="s2", name="s2", fn=fn2),
        ]
        result = SequentialWorkflowProvider().execute(steps, dry_run=False)
        assert result.outputs["s2"]["y"] == 20

    def test_failure_stops_execution(self):
        steps = [make_step("s1", "ok"), make_step("s2", "fail", raises=True), make_step("s3", "never")]
        result = SequentialWorkflowProvider().execute(steps, dry_run=False)
        assert result.status == "partial"
        assert result.steps_completed == 1
        assert len(result.errors) == 1

    def test_empty_steps(self):
        result = SequentialWorkflowProvider().execute([], dry_run=False)
        assert result.status == "completed"
        assert result.steps_completed == 0

    def test_workflow_id_unique(self):
        p = SequentialWorkflowProvider()
        r1 = p.execute([], dry_run=True)
        r2 = p.execute([], dry_run=True)
        assert r1.workflow_id != r2.workflow_id

    def test_backend(self):
        assert SequentialWorkflowProvider().backend == "sequential"
