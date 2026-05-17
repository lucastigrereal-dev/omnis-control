"""Tests for W148 — n8n E2E Pipeline."""
import pytest
from src.automation.n8n_pipeline import N8nPipeline, N8nPipelineResult
from src.automation.n8n_templates import N8nTemplateLibrary
from src.automation.models import AutomationWorkflow, AutomationTrigger, AutomationStep


@pytest.fixture
def pipeline():
    return N8nPipeline()


@pytest.fixture
def valid_wf():
    return N8nTemplateLibrary.daily_content_publish()


def test_pipeline_run_success(pipeline, valid_wf):
    result = pipeline.run(valid_wf)
    assert isinstance(result, N8nPipelineResult)
    assert result.success is True


def test_pipeline_run_dry_run_default(pipeline, valid_wf):
    result = pipeline.run(valid_wf)
    assert result.registry_entry.export.dry_run is True


def test_pipeline_run_registers_workflow(pipeline, valid_wf):
    result = pipeline.run(valid_wf)
    assert result.registry_entry is not None
    assert result.registry_entry.workflow_id == valid_wf.workflow_id


def test_pipeline_run_creates_schedule(pipeline, valid_wf):
    result = pipeline.run(valid_wf)
    assert result.schedule is not None
    assert result.schedule.cron_expr == "0 8 * * *"


def test_pipeline_run_auto_fires(pipeline, valid_wf):
    result = pipeline.run(valid_wf, auto_fire=True)
    assert result.trigger_result is not None
    assert result.trigger_result.status == "simulated"


def test_pipeline_no_auto_fire(pipeline, valid_wf):
    result = pipeline.run(valid_wf, auto_fire=False)
    assert result.trigger_result is None


def test_pipeline_safety_gate_blocks(pipeline):
    t = AutomationTrigger.new("manual")
    steps = [AutomationStep.new("delete_all", "transform")]
    bad_wf = AutomationWorkflow.new("Bad", "desc", t, steps)
    result = pipeline.run(bad_wf)
    assert result.success is False
    assert result.error != ""
    assert result.registry_entry is None


def test_pipeline_to_dict(pipeline, valid_wf):
    result = pipeline.run(valid_wf)
    d = result.to_dict()
    assert d["success"] is True
    assert "safety" in d
    assert "registry_entry" in d


def test_pipeline_with_tags(pipeline, valid_wf):
    result = pipeline.run(valid_wf, tags=["omnis", "daily"])
    assert "daily" in result.registry_entry.tags


def test_pipeline_custom_cron(pipeline, valid_wf):
    result = pipeline.run(valid_wf, cron_expr="0 20 * * *")
    assert result.schedule.cron_expr == "0 20 * * *"


def test_pipeline_all_templates(pipeline):
    for name, wf in N8nTemplateLibrary.all_templates().items():
        result = pipeline.run(wf)
        assert result.success, f"Template '{name}' pipeline failed: {result.error}"
