"""Tests for W146 — n8n Safety Gate."""
import pytest
from src.automation.n8n_safety_gate import N8nSafetyGate, SafetyCheckResult
from src.automation.models import AutomationWorkflow, AutomationTrigger, AutomationStep


@pytest.fixture
def gate():
    return N8nSafetyGate()


@pytest.fixture
def valid_wf():
    t = AutomationTrigger.new("webhook")
    steps = [AutomationStep.new("Process", "transform")]
    return AutomationWorkflow.new("Valid Workflow", "test", t, steps)


def test_valid_workflow_passes(gate, valid_wf):
    result = gate.check(valid_wf)
    assert result.passed is True
    assert result.errors == []


def test_no_steps_gives_warning(gate):
    t = AutomationTrigger.new("manual")
    wf = AutomationWorkflow.new("Empty", "desc", t)
    result = gate.check(wf)
    assert result.passed is True
    assert any("no steps" in w for w in result.warnings)


def test_too_many_steps_fails(gate):
    t = AutomationTrigger.new("manual")
    steps = [AutomationStep.new(f"Step{i}", "transform") for i in range(25)]
    wf = AutomationWorkflow.new("Big", "desc", t, steps)
    result = gate.check(wf)
    assert result.passed is False
    assert any("Too many steps" in e for e in result.errors)


def test_forbidden_step_name_fails(gate):
    t = AutomationTrigger.new("manual")
    steps = [AutomationStep.new("delete_all", "transform")]
    wf = AutomationWorkflow.new("Bad", "desc", t, steps)
    result = gate.check(wf)
    assert result.passed is False
    assert any("Forbidden step name" in e for e in result.errors)


def test_forbidden_config_key_in_step_fails(gate):
    t = AutomationTrigger.new("manual")
    steps = [AutomationStep.new("Call", "http_request", config={"api_key": "secret123"})]
    wf = AutomationWorkflow.new("Bad", "desc", t, steps)
    result = gate.check(wf)
    assert result.passed is False
    assert any("api_key" in e for e in result.errors)


def test_forbidden_config_key_in_trigger_fails(gate):
    t = AutomationTrigger.new("webhook", config={"token": "abc"})
    wf = AutomationWorkflow.new("Bad", "desc", t)
    result = gate.check(wf)
    assert result.passed is False
    assert any("token" in e for e in result.errors)


def test_inactive_workflow_warns(gate):
    t = AutomationTrigger.new("manual")
    wf = AutomationWorkflow.new("Inactive", "desc", t, active=False)
    result = gate.check(wf)
    assert result.passed is True
    assert any("inactive" in w for w in result.warnings)


def test_to_dict(gate, valid_wf):
    result = gate.check(valid_wf)
    d = result.to_dict()
    assert d["passed"] is True
    assert "errors" in d


def test_assert_safe_passes(gate, valid_wf):
    gate.assert_safe(valid_wf)  # no raise


def test_assert_safe_raises_on_invalid(gate):
    t = AutomationTrigger.new("manual")
    steps = [AutomationStep.new("delete_all", "transform")]
    wf = AutomationWorkflow.new("Bad", "desc", t, steps)
    with pytest.raises(ValueError, match="Safety gate failed"):
        gate.assert_safe(wf)
