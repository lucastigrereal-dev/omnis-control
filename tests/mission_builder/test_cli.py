"""CLI tests for mission-builder plan and run commands."""
import json
import pytest
from pathlib import Path
from typer.testing import CliRunner
from src.cli import app
from src.mission_builder import package_exporter as exp_mod

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "intents.yaml"
runner = CliRunner()


def test_cli_plan_carousel(monkeypatch, tmp_path):
    monkeypatch.setattr(exp_mod, "PACKAGES_ROOT", tmp_path)
    result = runner.invoke(app, ["mission-builder", "plan", "cria um carrossel sobre Natal"])
    assert result.exit_code == 0, result.output
    assert "carousel" in result.output.lower() or "carrossel" in result.output.lower()


def test_cli_plan_campaign(monkeypatch, tmp_path):
    monkeypatch.setattr(exp_mod, "PACKAGES_ROOT", tmp_path)
    result = runner.invoke(app, ["mission-builder", "plan", "cria uma campanha de 10 posts"])
    assert result.exit_code == 0, result.output
    assert "campaign" in result.output.lower() or "campanha" in result.output.lower()


def test_cli_plan_unknown_fails():
    result = runner.invoke(app, ["mission-builder", "plan", "algo completamente generico"])
    assert result.exit_code != 0 or "unknown" in result.output.lower()


def test_cli_plan_json_output(monkeypatch, tmp_path):
    monkeypatch.setattr(exp_mod, "PACKAGES_ROOT", tmp_path)
    result = runner.invoke(app, ["mission-builder", "plan", "cria um reel", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["intent"] == "reels"


def test_cli_run_dry_run_creates_package(monkeypatch, tmp_path):
    monkeypatch.setattr(exp_mod, "PACKAGES_ROOT", tmp_path)
    result = runner.invoke(
        app,
        ["mission-builder", "run", "cria um carrossel de turismo", "--dry-run"],
    )
    assert result.exit_code == 0, result.output
    assert "Missao criada" in result.output or "pacote" in result.output.lower()


def test_cli_run_json_output(monkeypatch, tmp_path):
    monkeypatch.setattr(exp_mod, "PACKAGES_ROOT", tmp_path)
    result = runner.invoke(
        app,
        ["mission-builder", "run", "cria um reel curto", "--dry-run", "--json"],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "plan" in data
    assert data["plan"]["intent"] == "reels"


def test_cli_mission_help_unaffected():
    """Verify that `mission` command group is unaffected (P3.0 isolation)."""
    result = runner.invoke(app, ["mission", "--help"])
    assert result.exit_code == 0, result.output
    assert "mission" in result.output.lower()
