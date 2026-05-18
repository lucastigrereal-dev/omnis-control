"""Tests for LangGraphProvider — fallback behavior when not installed."""
import pytest
from src.providers.langgraph_provider import LangGraphProvider
from src.providers.workflow import SequentialWorkflowProvider, WorkflowStep, WorkflowResult
from src.providers.base import ProviderStatus


def make_step(id: str, name: str = "") -> WorkflowStep:
    return WorkflowStep(id=id, name=name or id, fn=lambda s: {"done": True})


class TestLangGraphProviderFallback:
    def test_health_degraded_or_ok(self):
        p = LangGraphProvider()
        h = p.health_check()
        assert h.status.value in ("ok", "degraded")

    def test_execute_falls_back_to_sequential(self):
        p = LangGraphProvider(fallback=SequentialWorkflowProvider())
        steps = [make_step("s1"), make_step("s2")]
        result = p.execute(steps, dry_run=True)
        assert isinstance(result, WorkflowResult)
        assert result.steps_total == 2

    def test_execute_dry_run_completes(self):
        p = LangGraphProvider(fallback=SequentialWorkflowProvider())
        result = p.execute([make_step("s1")], dry_run=True)
        assert result.success

    def test_backend_indicates_state(self):
        p = LangGraphProvider()
        assert p.backend in ("langgraph", "sequential(langgraph_unavailable)")

    def test_name(self):
        assert LangGraphProvider().name == "workflow"


class TestLangGraphProviderFull:
    """If langgraph is installed, run full graph tests."""

    def test_execute_real_run_if_available(self):
        p = LangGraphProvider(fallback=SequentialWorkflowProvider())
        steps = [
            WorkflowStep(id="step1", name="s1", fn=lambda s: {"x": 10}),
            WorkflowStep(id="step2", name="s2", fn=lambda s: {"y": s.get("x", 0) * 2}),
        ]
        result = p.execute(steps, dry_run=False)
        assert result.steps_completed >= 1
