"""CLI tests for Capability Forge Lite."""
import json
import pytest
from typer.testing import CliRunner
from src.cli import app
from src.capability_forge_real import store as store_mod
from src.capability_gap import store as gap_store_mod
from src.capability_gap.models import CapabilityGap
from src.capability_gap.store import GapStore

runner = CliRunner()


def save_gap(tmp_path, risk_level="high") -> CapabilityGap:
    gap = CapabilityGap.new("cria app crm", "apps", "apps_capability", "crm_app", risk_level=risk_level)
    GapStore(tmp_path / "gaps.jsonl").save(gap)
    return gap


def test_cli_forge_lite_help():
    result = runner.invoke(app, ["forge-lite", "--help"])
    assert result.exit_code == 0
    assert "propose" in result.output
    assert "list" in result.output
    assert "show" in result.output


def test_cli_propose_json(tmp_path, monkeypatch):
    monkeypatch.setattr(gap_store_mod, "DEFAULT_GAPS_LOG", tmp_path / "gaps.jsonl")
    monkeypatch.setattr(store_mod, "DEFAULT_PROPOSALS_LOG", tmp_path / "proposals.jsonl")
    gap = save_gap(tmp_path)
    result = runner.invoke(app, ["forge-lite", "propose", gap.gap_id, "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["proposal_id"].startswith("prop_")
    assert data["gap_id"] == gap.gap_id
    assert data["approval_required"] is True


def test_cli_propose_gap_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(gap_store_mod, "DEFAULT_GAPS_LOG", tmp_path / "gaps.jsonl")
    monkeypatch.setattr(store_mod, "DEFAULT_PROPOSALS_LOG", tmp_path / "proposals.jsonl")
    result = runner.invoke(app, ["forge-lite", "propose", "gap_ghost"])
    assert result.exit_code != 0


def test_cli_list_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DEFAULT_PROPOSALS_LOG", tmp_path / "proposals.jsonl")
    result = runner.invoke(app, ["forge-lite", "list"])
    assert result.exit_code == 0


def test_cli_show_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(store_mod, "DEFAULT_PROPOSALS_LOG", tmp_path / "proposals.jsonl")
    result = runner.invoke(app, ["forge-lite", "show", "prop_ghost"])
    assert result.exit_code != 0


def test_cli_low_risk_propose_no_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(gap_store_mod, "DEFAULT_GAPS_LOG", tmp_path / "gaps.jsonl")
    monkeypatch.setattr(store_mod, "DEFAULT_PROPOSALS_LOG", tmp_path / "proposals.jsonl")
    gap = save_gap(tmp_path, risk_level="low")
    result = runner.invoke(app, ["forge-lite", "propose", gap.gap_id, "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["approval_required"] is False
