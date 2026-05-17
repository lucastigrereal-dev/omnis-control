"""Tests for W147 — n8n Template Library."""
import pytest
from src.automation.n8n_templates import N8nTemplateLibrary
from src.automation.models import AutomationWorkflow
from src.automation.n8n_safety_gate import N8nSafetyGate


gate = N8nSafetyGate()


def test_all_templates_returns_dict():
    templates = N8nTemplateLibrary.all_templates()
    assert len(templates) == 4


def test_all_templates_are_workflows():
    for name, wf in N8nTemplateLibrary.all_templates().items():
        assert isinstance(wf, AutomationWorkflow), f"{name} is not AutomationWorkflow"


def test_daily_content_publish():
    wf = N8nTemplateLibrary.daily_content_publish()
    assert wf.trigger.trigger_type == "schedule"
    assert len(wf.steps) == 3


def test_mission_completed_hook():
    wf = N8nTemplateLibrary.mission_completed_hook()
    assert wf.trigger.trigger_type == "mission_completed"
    assert len(wf.steps) == 2


def test_lead_capture_webhook():
    wf = N8nTemplateLibrary.lead_capture_webhook()
    assert wf.trigger.trigger_type == "webhook"
    assert len(wf.steps) == 3


def test_weekly_metrics_report():
    wf = N8nTemplateLibrary.weekly_metrics_report()
    assert "weekly" in wf.name.lower()
    assert len(wf.steps) == 3


def test_all_templates_pass_safety_gate():
    for name, wf in N8nTemplateLibrary.all_templates().items():
        result = gate.check(wf)
        assert result.passed, f"Template '{name}' failed safety gate: {result.errors}"


def test_inactive_flag_respected():
    wf = N8nTemplateLibrary.daily_content_publish(active=False)
    assert wf.active is False


def test_templates_have_descriptions():
    for wf in N8nTemplateLibrary.all_templates().values():
        assert wf.description
