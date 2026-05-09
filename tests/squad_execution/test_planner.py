"""Tests for Squad Execution Planner."""
import socket
import os
import pytest
from src.squad_execution.planner import plan_squad_run
from src.squad_execution.models import SQUAD_RUN_STATUS_PLANNED_READY, SQUAD_RUN_STATUS_BLOCKED_APPROVAL


def test_marketing_run_is_planned_ready():
    plan = plan_squad_run("cria campanha de posts para hotel")
    assert plan.status == SQUAD_RUN_STATUS_PLANNED_READY


def test_app_run_is_blocked():
    plan = plan_squad_run("cria app CRM com dashboard")
    assert plan.status == SQUAD_RUN_STATUS_BLOCKED_APPROVAL


def test_plan_has_roles():
    plan = plan_squad_run("cria campanha de posts para hotel")
    assert len(plan.roles) >= 2


def test_no_network_calls(monkeypatch):
    def _block(*args, **kwargs):
        raise AssertionError("Network blocked")
    monkeypatch.setattr(socket.socket, "connect", _block)
    plan_squad_run("cria campanha de posts")


def test_no_env_reads(monkeypatch):
    original = os.getenv
    def _guard(key, *args, **kwargs):
        assert not key.startswith("META_") and not key.startswith("INSTAGRAM_")
        return original(key, *args, **kwargs)
    monkeypatch.setattr(os, "getenv", _guard)
    plan_squad_run("cria campanha de posts")
