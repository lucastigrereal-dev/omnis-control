"""Tests for W143 — n8n Bridge."""
import pytest
from src.automation.n8n_bridge import N8nBridge, N8nWorkflowExport, N8nTriggerResult
from src.automation.models import AutomationWorkflow, AutomationTrigger, AutomationStep


@pytest.fixture
def sample_workflow():
    trigger = AutomationTrigger.new("webhook", config={"path": "/omnis/hook"})
    steps = [
        AutomationStep.new("Transform data", "transform", config={"field": "content"}),
        AutomationStep.new("Notify team", "notify", config={"channel": "#omnis"}),
    ]
    return AutomationWorkflow.new("Test Workflow", "Integration test", trigger, steps)


@pytest.fixture
def bridge():
    return N8nBridge()


def test_export_workflow_returns_export(bridge, sample_workflow):
    result = bridge.export_workflow(sample_workflow)
    assert isinstance(result, N8nWorkflowExport)
    assert result.workflow_id == sample_workflow.workflow_id


def test_export_dry_run_default(bridge, sample_workflow):
    result = bridge.export_workflow(sample_workflow)
    assert result.dry_run is True


def test_export_node_count(bridge, sample_workflow):
    result = bridge.export_workflow(sample_workflow)
    # trigger + 2 steps = 3 nodes
    assert result.node_count == 3


def test_export_n8n_json_structure(bridge, sample_workflow):
    result = bridge.export_workflow(sample_workflow)
    j = result.n8n_json
    assert "name" in j
    assert "nodes" in j
    assert "connections" in j
    assert j["name"] == sample_workflow.name
    assert len(j["nodes"]) == 3


def test_export_trigger_node_type(bridge, sample_workflow):
    result = bridge.export_workflow(sample_workflow)
    trigger_node = result.n8n_json["nodes"][0]
    assert trigger_node["type"] == "n8n-nodes-base.webhook"


def test_export_step_node_types(bridge, sample_workflow):
    result = bridge.export_workflow(sample_workflow)
    nodes = result.n8n_json["nodes"]
    assert nodes[1]["type"] == "n8n-nodes-base.set"
    assert nodes[2]["type"] == "n8n-nodes-base.slack"


def test_export_connections_built(bridge, sample_workflow):
    result = bridge.export_workflow(sample_workflow)
    connections = result.n8n_json["connections"]
    assert len(connections) == 2  # trigger→step1, step1→step2


def test_export_to_dict(bridge, sample_workflow):
    result = bridge.export_workflow(sample_workflow)
    d = result.to_dict()
    assert d["dry_run"] is True
    assert "n8n_json" in d
    assert d["node_count"] == 3


def test_trigger_workflow_dry_run(bridge, sample_workflow):
    result = bridge.trigger_workflow(sample_workflow)
    assert isinstance(result, N8nTriggerResult)
    assert result.dry_run is True
    assert result.status == "simulated"


def test_trigger_workflow_execution_id_prefix(bridge, sample_workflow):
    result = bridge.trigger_workflow(sample_workflow)
    assert result.execution_id.startswith("dry_")


def test_trigger_workflow_message_contains_name(bridge, sample_workflow):
    result = bridge.trigger_workflow(sample_workflow)
    assert "Test Workflow" in result.message
    assert "DRY-RUN" in result.message


def test_trigger_to_dict(bridge, sample_workflow):
    result = bridge.trigger_workflow(sample_workflow)
    d = result.to_dict()
    assert "execution_id" in d
    assert d["status"] == "simulated"


def test_export_no_steps_workflow(bridge):
    trigger = AutomationTrigger.new("manual")
    wf = AutomationWorkflow.new("Empty", "no steps", trigger)
    result = bridge.export_workflow(wf)
    assert result.node_count == 1
    assert result.n8n_json["connections"] == {}


def test_schedule_trigger_type(bridge):
    trigger = AutomationTrigger.new("schedule", config={"cron": "0 8 * * *"})
    wf = AutomationWorkflow.new("Scheduled", "daily", trigger)
    result = bridge.export_workflow(wf)
    assert result.n8n_json["nodes"][0]["type"] == "n8n-nodes-base.scheduleTrigger"
