"""P5.0 — Orchestrator Integration Wire tests."""
import os
import socket
import pytest
from src.mission_orchestrator.planner import build_plan
from src.mission_orchestrator.errors import UnknownIntentError


def test_marketing_request_finds_sector_marketing():
    run = build_plan("cria carrossel campanha instagram")
    assert run.sector_id == "marketing"


def test_campaign_request_finds_capability():
    run = build_plan("cria campanha de posts para hotel")
    assert "campaign_package" in run.matched_capabilities or len(run.matched_capabilities) >= 1


def test_finance_request_with_no_capability_creates_gap():
    # "roi faturamento receita financeiro" → sector=finance, no capability keyword match
    run = build_plan("roi faturamento receita financeiro", allow_unknown=True)
    assert run.sector_id == "finance"
    assert run.matched_capabilities == []
    assert len(run.suggested_gap_ids) >= 1


def test_app_factory_request_marks_approval_required():
    # app_factory_spec has risk_level: high
    run = build_plan("cria app sistema api software", allow_unknown=True)
    assert "app_factory_spec" in run.matched_capabilities
    assert run.approval_required is True


def test_asset_import_marks_approval_required():
    # asset_inbox_import has risk_level: medium
    run = build_plan("importar arquivo imagem asset", allow_unknown=True)
    assert run.approval_required is True


def test_low_risk_capability_no_approval():
    # offline_package_carousel + campaign_package → both low risk
    run = build_plan("carrossel campanha post instagram")
    assert run.approval_required is False


def test_unknown_intent_with_capability_does_not_raise():
    # "importar arquivo" → asset_inbox_import matches even though mission_builder
    # doesn't know the intent → should NOT raise UnknownIntentError
    run = build_plan("importar arquivo imagem")
    assert len(run.matched_capabilities) >= 1


def test_matched_capabilities_in_to_dict():
    run = build_plan("carrossel instagram post campanha")
    d = run.to_dict()
    assert "matched_capabilities" in d
    assert "sector_id" in d
    assert "approval_required" in d
    assert "suggested_gap_ids" in d


def test_no_network_calls(monkeypatch):
    def _block(*args, **kwargs):
        raise AssertionError("Network blocked")
    monkeypatch.setattr(socket.socket, "connect", _block)
    run = build_plan("carrossel campanha instagram")
    assert run.sector_id is not None


def test_no_env_reads(monkeypatch):
    original = os.getenv
    def _assert_no_secret(key, *args, **kwargs):
        assert not key.startswith("META_") and not key.startswith("INSTAGRAM_")
        return original(key, *args, **kwargs)
    monkeypatch.setattr(os, "getenv", _assert_no_secret)
    build_plan("carrossel instagram post")
