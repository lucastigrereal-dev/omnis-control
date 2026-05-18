"""Tests for omnis local command group."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from src.cli_local import app, _create_mission_stub

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _invoke(*args, **kwargs):
    return runner.invoke(app, list(args), **kwargs)


# ---------------------------------------------------------------------------
# _create_mission_stub unit tests
# ---------------------------------------------------------------------------


def test_create_mission_stub_creates_contract(tmp_path):
    folder = _create_mission_stub("test_type", {"key": "val"}, missions_dir=tmp_path)
    contract = folder / "mission_contract.json"
    assert contract.exists()
    data = json.loads(contract.read_text())
    assert data["mission_type"] == "test_type"
    assert data["dry_run"] is True
    assert data["params"]["key"] == "val"


def test_create_mission_stub_creates_brief(tmp_path):
    folder = _create_mission_stub("brief_test", {"foo": "bar"}, missions_dir=tmp_path)
    brief = folder / "01_mission_brief.md"
    assert brief.exists()
    content = brief.read_text()
    assert "brief_test" in content
    assert "foo" in content


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------


def test_campaign_dry_run_output_and_stub(tmp_path, monkeypatch):
    monkeypatch.setattr("src.cli_local.MISSIONS_DIR", tmp_path)
    result = _invoke(
        "campaign",
        "--profile", "@oinatalrn",
        "--theme", "praias",
        "--objective", "awareness",
    )
    assert result.exit_code == 0, result.output
    assert "DRY RUN" in result.output
    assert "@oinatalrn" in result.output
    # stub must be created
    stubs = list(tmp_path.iterdir())
    assert len(stubs) == 1
    assert (stubs[0] / "mission_contract.json").exists()


def test_carousel_dry_run(tmp_path, monkeypatch):
    monkeypatch.setattr("src.cli_local.MISSIONS_DIR", tmp_path)
    result = _invoke("carousel", "--profile", "@lucastigrereal", "--theme", "food")
    assert result.exit_code == 0, result.output
    assert "DRY RUN" in result.output
    assert "carousel" in result.output.lower()


def test_reels_dry_run(tmp_path, monkeypatch):
    monkeypatch.setattr("src.cli_local.MISSIONS_DIR", tmp_path)
    result = _invoke("reels", "--profile", "@agenteviajabrasil", "--theme", "viagem")
    assert result.exit_code == 0, result.output
    assert "DRY RUN" in result.output


def test_app_dry_run_and_stub(tmp_path, monkeypatch):
    monkeypatch.setattr("src.cli_local.MISSIONS_DIR", tmp_path)
    result = _invoke("app", "--name", "MyApp", "--domain", "crm")
    assert result.exit_code == 0, result.output
    assert "DRY RUN" in result.output
    assert "MyApp" in result.output
    stubs = list(tmp_path.iterdir())
    assert len(stubs) == 1
    data = json.loads((stubs[0] / "mission_contract.json").read_text())
    assert data["params"]["name"] == "MyApp"


def test_forge_dry_run_and_stub(tmp_path, monkeypatch):
    monkeypatch.setattr("src.cli_local.MISSIONS_DIR", tmp_path)
    result = _invoke("forge", "--skill-name", "lead-qualifier", "--description", "qualifies leads")
    assert result.exit_code == 0, result.output
    assert "DRY RUN" in result.output
    assert "lead-qualifier" in result.output
    stubs = list(tmp_path.iterdir())
    assert len(stubs) == 1
    data = json.loads((stubs[0] / "mission_contract.json").read_text())
    assert data["params"]["skill_name"] == "lead-qualifier"


def test_cockpit_prints_path():
    result = _invoke("cockpit")
    assert result.exit_code == 0, result.output
    assert "cockpit" in result.output.lower()


def test_status_no_missions_dir(tmp_path, monkeypatch):
    missing = tmp_path / "no_missions_here"
    monkeypatch.setattr("src.cli_local.MISSIONS_DIR", missing)
    result = _invoke("status")
    assert result.exit_code == 0, result.output
    assert "not found" in result.output.lower() or "no missions" in result.output.lower()


def test_status_lists_missions(tmp_path, monkeypatch):
    monkeypatch.setattr("src.cli_local.MISSIONS_DIR", tmp_path)
    # Create two stubs
    _create_mission_stub("campaign", {"profile": "x"}, missions_dir=tmp_path)
    _create_mission_stub("reels", {"profile": "y"}, missions_dir=tmp_path)
    result = _invoke("status")
    assert result.exit_code == 0, result.output
    assert "Total missions: 2" in result.output
    assert "campaign" in result.output
    assert "reels" in result.output
