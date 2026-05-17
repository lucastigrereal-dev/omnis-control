"""Tests for W144 — n8n Workflow Registry."""
import pytest
from src.automation.n8n_registry import N8nWorkflowRegistry, N8nRegistryEntry
from src.automation.models import AutomationWorkflow, AutomationTrigger, AutomationStep


@pytest.fixture
def registry():
    return N8nWorkflowRegistry()


@pytest.fixture
def wf():
    trigger = AutomationTrigger.new("webhook")
    steps = [AutomationStep.new("Process", "transform")]
    return AutomationWorkflow.new("My Workflow", "desc", trigger, steps)


def test_register_returns_entry(registry, wf):
    entry = registry.register(wf)
    assert isinstance(entry, N8nRegistryEntry)
    assert entry.workflow_id == wf.workflow_id


def test_count_after_register(registry, wf):
    registry.register(wf)
    assert registry.count() == 1


def test_get_by_entry_id(registry, wf):
    entry = registry.register(wf)
    found = registry.get(entry.entry_id)
    assert found is not None
    assert found.entry_id == entry.entry_id


def test_get_missing_returns_none(registry):
    assert registry.get("nonexistent") is None


def test_list_all(registry, wf):
    registry.register(wf)
    assert len(registry.list_all()) == 1


def test_find_by_workflow_id(registry, wf):
    registry.register(wf)
    found = registry.find_by_workflow_id(wf.workflow_id)
    assert found is not None
    assert found.workflow_name == wf.name


def test_find_by_tag(registry, wf):
    registry.register(wf, tags=["production", "daily"])
    results = registry.find_by_tag("daily")
    assert len(results) == 1


def test_find_by_tag_no_match(registry, wf):
    registry.register(wf, tags=["staging"])
    assert registry.find_by_tag("production") == []


def test_entry_to_dict(registry, wf):
    entry = registry.register(wf)
    d = entry.to_dict()
    assert "entry_id" in d
    assert "export" in d
    assert d["workflow_name"] == wf.name


def test_export_jsonl_safe_path(registry, wf, tmp_path):
    registry.register(wf)
    out = tmp_path / "registry.jsonl"
    count = registry.export_jsonl(str(out))
    assert count == 1
    assert out.exists()


def test_export_jsonl_unsafe_path_raises(registry, wf):
    registry.register(wf)
    with pytest.raises(ValueError, match="safe zone"):
        registry.export_jsonl("C:/production/registry.jsonl")


def test_multiple_workflows(registry):
    for i in range(3):
        t = AutomationTrigger.new("manual")
        wf = AutomationWorkflow.new(f"WF{i}", "desc", t)
        registry.register(wf)
    assert registry.count() == 3
