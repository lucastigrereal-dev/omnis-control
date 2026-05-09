"""CLI tests for Role Registry."""
import json
import pytest
from typer.testing import CliRunner
from src.cli import app

runner = CliRunner()


def test_cli_role_registry_help():
    result = runner.invoke(app, ["role-registry", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "show" in result.output
    assert "match" in result.output


def test_cli_role_registry_list():
    result = runner.invoke(app, ["role-registry", "list"])
    assert result.exit_code == 0


def test_cli_role_registry_list_json():
    result = runner.invoke(app, ["role-registry", "list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) >= 8
    ids = [r["role_id"] for r in data]
    assert "copywriter" in ids


def test_cli_role_registry_show():
    result = runner.invoke(app, ["role-registry", "show", "copywriter"])
    assert result.exit_code == 0
    assert "Copywriter" in result.output


def test_cli_role_registry_show_not_found():
    result = runner.invoke(app, ["role-registry", "show", "ghost_role"])
    assert result.exit_code != 0


def test_cli_role_registry_match_sector():
    result = runner.invoke(app, ["role-registry", "match", "--sector", "marketing"])
    assert result.exit_code == 0


def test_cli_role_registry_match_output_json():
    result = runner.invoke(app, ["role-registry", "match", "--output", "video_plan", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert any(r["role_id"] == "video_planner" for r in data)


def test_cli_role_registry_match_no_args():
    result = runner.invoke(app, ["role-registry", "match"])
    assert result.exit_code != 0
