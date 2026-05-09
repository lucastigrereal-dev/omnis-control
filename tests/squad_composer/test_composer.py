"""Tests for Squad Composer."""
import socket
import os
import pytest
from src.squad_composer.composer import compose_squad


def test_marketing_campaign_includes_strategist():
    plan = compose_squad("cria campanha de 10 posts para hotel")
    ids = [r.role_id for r in plan.roles]
    assert "marketing_strategist" in ids


def test_marketing_campaign_includes_copywriter():
    plan = compose_squad("cria campanha de 10 posts para hotel")
    ids = [r.role_id for r in plan.roles]
    assert "copywriter" in ids


def test_marketing_campaign_includes_qa():
    plan = compose_squad("cria campanha de 10 posts para hotel")
    ids = [r.role_id for r in plan.roles]
    assert "qa_auditor" in ids


def test_video_request_includes_video_planner():
    plan = compose_squad("cria roteiro para reels")
    ids = [r.role_id for r in plan.roles]
    assert "video_planner" in ids


def test_app_request_includes_architect():
    plan = compose_squad("cria app CRM com dashboard")
    ids = [r.role_id for r in plan.roles]
    assert "app_architect" in ids


def test_app_request_is_high_risk():
    plan = compose_squad("cria app CRM com dashboard")
    assert plan.approval_required is True
    assert plan.risk_level == "high"


def test_unknown_sector_returns_squad_with_qa():
    plan = compose_squad("faça algo completamente aleatório xyz")
    ids = [r.role_id for r in plan.roles]
    assert "qa_auditor" in ids


def test_no_network_calls(monkeypatch):
    def _block(*args, **kwargs):
        raise AssertionError("Network blocked")
    monkeypatch.setattr(socket.socket, "connect", _block)
    compose_squad("cria campanha de posts")


def test_no_env_reads(monkeypatch):
    original = os.getenv
    def _guard(key, *args, **kwargs):
        assert not key.startswith("META_") and not key.startswith("INSTAGRAM_")
        return original(key, *args, **kwargs)
    monkeypatch.setattr(os, "getenv", _guard)
    compose_squad("cria campanha de posts")
