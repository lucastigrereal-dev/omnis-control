"""Tests — WorkflowRegistry (Onda 13).

Cobertura:
  - register / get / list_all / names / count
  - health_check_all: all_ok, importable, failed
  - WorkflowEntry to_dict
  - WorkflowHealthReport to_dict + all_ok property
  - default() registry com 4 workflows padrão
  - run() por nome
  - erro para workflow inexistente ou sem factory
"""
from __future__ import annotations

import pytest

from src.workflows.workflow_registry import (
    WorkflowRegistry,
    WorkflowEntry,
    WorkflowHealthReport,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _entry(name: str = "test_wf", factory=None) -> WorkflowEntry:
    return WorkflowEntry(
        name=name,
        version="1.0",
        description=f"Test workflow {name}",
        cost_local_pct=100,
        dry_run_safe=True,
        tags=["test"],
        factory=factory,
    )


class _FakeWorkflow:
    def run(self, **kwargs):
        return {"success": True, "kwargs": kwargs}


# ── register / get / list ─────────────────────────────────────────────────────

def test_register_and_get():
    reg = WorkflowRegistry()
    e = _entry("wf1")
    reg.register(e)
    assert reg.get("wf1") is e


def test_get_unknown_returns_none():
    reg = WorkflowRegistry()
    assert reg.get("nonexistent") is None


def test_list_all_returns_all():
    reg = WorkflowRegistry()
    reg.register(_entry("wf_a"))
    reg.register(_entry("wf_b"))
    assert len(reg.list_all()) == 2


def test_names_property():
    reg = WorkflowRegistry()
    reg.register(_entry("alpha"))
    reg.register(_entry("beta"))
    assert "alpha" in reg.names
    assert "beta" in reg.names


def test_count_property():
    reg = WorkflowRegistry()
    reg.register(_entry("wf1"))
    reg.register(_entry("wf2"))
    reg.register(_entry("wf3"))
    assert reg.count == 3


# ── health_check_all ──────────────────────────────────────────────────────────

def test_health_all_ok_when_factories_present():
    reg = WorkflowRegistry()
    reg.register(_entry("wf1", factory=_FakeWorkflow))
    reg.register(_entry("wf2", factory=_FakeWorkflow))
    report = reg.health_check_all()
    assert report.all_ok is True
    assert report.failed == 0


def test_health_fails_when_no_factory():
    reg = WorkflowRegistry()
    reg.register(_entry("wf_broken", factory=None))
    report = reg.health_check_all()
    assert report.all_ok is False
    assert report.failed == 1


def test_health_importable_count():
    reg = WorkflowRegistry()
    reg.register(_entry("wf_ok", factory=_FakeWorkflow))
    reg.register(_entry("wf_bad", factory=None))
    report = reg.health_check_all()
    assert report.importable == 1
    assert report.failed == 1


def test_health_total_count():
    reg = WorkflowRegistry()
    reg.register(_entry("a", factory=_FakeWorkflow))
    reg.register(_entry("b", factory=_FakeWorkflow))
    reg.register(_entry("c"))
    report = reg.health_check_all()
    assert report.total == 3


def test_health_entries_list_length():
    reg = WorkflowRegistry()
    reg.register(_entry("x"))
    reg.register(_entry("y"))
    report = reg.health_check_all()
    assert len(report.entries) == 2


def test_health_empty_registry():
    reg = WorkflowRegistry()
    report = reg.health_check_all()
    assert report.all_ok is True
    assert report.total == 0


# ── run ───────────────────────────────────────────────────────────────────────

def test_run_by_name():
    reg = WorkflowRegistry()
    reg.register(_entry("fake", factory=_FakeWorkflow))
    result = reg.run("fake", topic="test")
    assert result["success"] is True


def test_run_unknown_raises_key_error():
    reg = WorkflowRegistry()
    with pytest.raises(KeyError, match="unknown_wf"):
        reg.run("unknown_wf")


def test_run_no_factory_raises_runtime_error():
    reg = WorkflowRegistry()
    reg.register(_entry("no_factory", factory=None))
    with pytest.raises(RuntimeError, match="no_factory"):
        reg.run("no_factory")


# ── WorkflowEntry model ───────────────────────────────────────────────────────

def test_entry_to_dict_has_name():
    e = _entry("my_wf")
    assert e.to_dict()["name"] == "my_wf"


def test_entry_to_dict_has_cost_local_pct():
    e = _entry()
    assert e.to_dict()["cost_local_pct"] == 100


def test_entry_to_dict_has_dry_run_safe():
    e = _entry()
    assert e.to_dict()["dry_run_safe"] is True


def test_entry_to_dict_no_factory_field():
    e = _entry(factory=_FakeWorkflow)
    d = e.to_dict()
    assert "factory" not in d


# ── WorkflowHealthReport model ────────────────────────────────────────────────

def test_health_report_to_dict():
    report = WorkflowHealthReport(total=2, importable=2, failed=0)
    d = report.to_dict()
    assert d["total"] == 2
    assert d["all_ok"] is True


def test_health_report_all_ok_false():
    report = WorkflowHealthReport(total=3, importable=2, failed=1)
    assert report.all_ok is False


# ── default() registry ────────────────────────────────────────────────────────

def test_default_registry_has_20_workflows():
    reg = WorkflowRegistry.default()
    assert reg.count == 20


def test_default_registry_has_deep_research():
    reg = WorkflowRegistry.default()
    assert reg.get("deep_research") is not None


def test_default_registry_has_video_edit():
    reg = WorkflowRegistry.default()
    assert reg.get("video_edit") is not None


def test_default_registry_has_app_factory():
    reg = WorkflowRegistry.default()
    assert reg.get("app_factory") is not None


def test_default_registry_has_code_run():
    reg = WorkflowRegistry.default()
    assert reg.get("code_run") is not None


def test_default_registry_all_ok():
    reg = WorkflowRegistry.default()
    report = reg.health_check_all()
    assert report.all_ok is True


def test_default_all_cost_local_pct_100():
    reg = WorkflowRegistry.default()
    for entry in reg.list_all():
        assert entry.cost_local_pct == 100


def test_default_all_dry_run_safe():
    reg = WorkflowRegistry.default()
    for entry in reg.list_all():
        assert entry.dry_run_safe is True
