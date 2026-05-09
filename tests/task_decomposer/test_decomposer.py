"""Tests for Task Decomposer."""
import socket
import os
import pytest
from src.squad_composer.composer import compose_squad
from src.task_decomposer.decomposer import decompose_squad


def make_plan(request="cria campanha de 10 posts para hotel"):
    squad = compose_squad(request)
    return decompose_squad(squad)


def test_marketing_squad_generates_tasks():
    plan = make_plan("cria campanha de 10 posts para hotel")
    assert len(plan.tasks) >= 2


def test_marketing_tasks_in_order():
    plan = make_plan("cria campanha de 10 posts para hotel")
    role_ids = [t.role_id for t in plan.tasks]
    if "marketing_strategist" in role_ids and "copywriter" in role_ids:
        strat_idx = role_ids.index("marketing_strategist")
        copy_idx = role_ids.index("copywriter")
        assert strat_idx < copy_idx


def test_app_squad_generates_high_risk_plan():
    plan = make_plan("cria app CRM com dashboard")
    assert plan.approval_required is True
    assert plan.risk_level == "high"


def test_app_squad_has_qa_task():
    plan = make_plan("cria app CRM com dashboard")
    role_ids = [t.role_id for t in plan.tasks]
    assert "qa_auditor" in role_ids


def test_dependency_graph_has_no_cycle():
    plan = make_plan("cria campanha de 10 posts para hotel")
    from src.task_decomposer.decomposer import _detect_cycle
    assert _detect_cycle(plan.dependency_graph) is False


def test_task_dependencies_are_valid_task_ids():
    plan = make_plan("cria campanha de 10 posts para hotel")
    all_ids = {t.task_id for t in plan.tasks}
    for t in plan.tasks:
        for dep in t.depends_on:
            assert dep in all_ids, f"Dependency {dep} not found in task IDs"


def test_no_network_calls(monkeypatch):
    def _block(*args, **kwargs):
        raise AssertionError("Network blocked")
    monkeypatch.setattr(socket.socket, "connect", _block)
    make_plan()


def test_no_env_reads(monkeypatch):
    original = os.getenv
    def _guard(key, *args, **kwargs):
        assert not key.startswith("META_") and not key.startswith("INSTAGRAM_")
        return original(key, *args, **kwargs)
    monkeypatch.setattr(os, "getenv", _guard)
    make_plan()
