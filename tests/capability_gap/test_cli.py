"""CLI tests for capability gap."""
import json
import pytest
from typer.testing import CliRunner
from src.cli import app
from src.capability_gap import store as store_mod

runner = CliRunner()


def test_cli_capability_gap_help():
    result = runner.invoke(app, ["capability-gap", "--help"])
    assert result.exit_code == 0
    assert "detect" in result.output
    assert "list" in result.output
    assert "show" in result.output


def test_cli_detect_covered_json():
    result = runner.invoke(app, ["capability-gap", "detect", "carrossel instagram post", "--json", "--no-save"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "covered"
    assert len(data["matched_capabilities"]) >= 1


def test_cli_detect_unknown_json():
    result = runner.invoke(app, ["capability-gap", "detect", "xyzzy nonsense", "--json", "--no-save"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "unknown_sector"
    assert len(data["gaps"]) >= 1


def test_cli_detect_saves_gap(tmp_path, monkeypatch):
    from src.capability_gap import store as store_mod
    from src.capability_gap.store import GapStore
    log = tmp_path / "gaps.jsonl"
    monkeypatch.setattr(store_mod, "DEFAULT_GAPS_LOG", log)
    result = runner.invoke(app, ["capability-gap", "detect", "xyzzy nonsense blah"])
    assert result.exit_code == 0
    assert log.exists()


def test_cli_list_empty(tmp_path, monkeypatch):
    from src.capability_gap import store as store_mod
    monkeypatch.setattr(store_mod, "DEFAULT_GAPS_LOG", tmp_path / "empty.jsonl")
    result = runner.invoke(app, ["capability-gap", "list"])
    assert result.exit_code == 0


def test_cli_show_not_found(tmp_path, monkeypatch):
    from src.capability_gap import store as store_mod
    monkeypatch.setattr(store_mod, "DEFAULT_GAPS_LOG", tmp_path / "empty.jsonl")
    result = runner.invoke(app, ["capability-gap", "show", "gap_ghost"])
    assert result.exit_code != 0
