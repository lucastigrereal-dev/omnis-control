"""CLI tests for mission orchestrator."""
import json
import pytest
from typer.testing import CliRunner
from src.cli import app
from src.mission_orchestrator import service as svc

runner = CliRunner()


def test_cli_orchestrator_help():
    result = runner.invoke(app, ["orchestrator", "--help"])
    assert result.exit_code == 0
    assert "plan" in result.output
    assert "run" in result.output
    assert "list" in result.output
    assert "status" in result.output


def test_cli_orchestrator_plan_carrossel():
    result = runner.invoke(app, ["orchestrator", "plan", "cria um carrossel para hotel"])
    assert result.exit_code == 0, result.output
    assert "plan" in result.output.lower() or "intent" in result.output.lower()


def test_cli_orchestrator_plan_json(tmp_path, monkeypatch):
    result = runner.invoke(app, ["orchestrator", "plan", "reels hotel Natal", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["intent"] == "reels"
    assert data["status"] == "planned"
    assert len(data["steps"]) >= 2


def test_cli_orchestrator_run_json(tmp_path, monkeypatch):
    monkeypatch.setattr(svc, "DEFAULT_RUNS_ROOT", tmp_path / "runs")
    monkeypatch.setattr(svc, "DEFAULT_RUNS_LOG", tmp_path / "runs.jsonl")
    result = runner.invoke(app, ["orchestrator", "run", "carrossel hotel", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "dry_run"
    assert data["mission_id"] is not None


def test_cli_orchestrator_unknown_intent_error():
    result = runner.invoke(app, ["orchestrator", "plan", "algo que nao bate com nada"])
    assert result.exit_code != 0


def test_cli_orchestrator_list_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(svc, "DEFAULT_RUNS_LOG", tmp_path / "empty.jsonl")
    result = runner.invoke(app, ["orchestrator", "list"])
    assert result.exit_code == 0, result.output


def test_cli_orchestrator_status_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(svc, "DEFAULT_RUNS_LOG", tmp_path / "empty.jsonl")
    result = runner.invoke(app, ["orchestrator", "status", "run_ghost"])
    assert result.exit_code != 0


def test_cli_mission_builder_unaffected():
    result = runner.invoke(app, ["mission-builder", "--help"])
    assert result.exit_code == 0


def test_cli_mission_report_unaffected():
    result = runner.invoke(app, ["mission-report", "--help"])
    assert result.exit_code == 0
