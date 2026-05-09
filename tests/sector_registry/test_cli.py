"""CLI tests for sector registry."""
import json
import pytest
from typer.testing import CliRunner
from src.cli import app

runner = CliRunner()


def test_cli_sector_registry_help():
    result = runner.invoke(app, ["sector-registry", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "match" in result.output
    assert "show" in result.output


def test_cli_sector_registry_list():
    result = runner.invoke(app, ["sector-registry", "list"])
    assert result.exit_code == 0, result.output
    assert "marketing" in result.output.lower()


def test_cli_sector_registry_list_json():
    result = runner.invoke(app, ["sector-registry", "list", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) >= 5
    ids = [s["sector_id"] for s in data]
    assert "marketing" in ids


def test_cli_sector_registry_match_marketing():
    result = runner.invoke(app, ["sector-registry", "match", "carrossel hotel instagram"])
    assert result.exit_code == 0, result.output


def test_cli_sector_registry_match_json():
    result = runner.invoke(app, ["sector-registry", "match", "reels instagram post", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["sector_id"] == "marketing"
    assert data["confidence"] > 0


def test_cli_sector_registry_match_unknown():
    result = runner.invoke(app, ["sector-registry", "match", "xyzzy nonsense"])
    assert result.exit_code == 0
    assert "unknown" in result.output.lower() or "nenhum" in result.output.lower()


def test_cli_sector_registry_show_found():
    result = runner.invoke(app, ["sector-registry", "show", "marketing", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["sector_id"] == "marketing"


def test_cli_sector_registry_show_not_found():
    result = runner.invoke(app, ["sector-registry", "show", "nonexistent"])
    assert result.exit_code != 0
