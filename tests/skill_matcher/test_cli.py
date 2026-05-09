"""CLI tests for skill matcher."""
import json
import pytest
from typer.testing import CliRunner
from src.cli import app

runner = CliRunner()


def test_cli_skill_matcher_help():
    result = runner.invoke(app, ["skill-matcher", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "match" in result.output
    assert "show" in result.output


def test_cli_skill_matcher_list():
    result = runner.invoke(app, ["skill-matcher", "list"])
    assert result.exit_code == 0, result.output
    assert "marketing" in result.output.lower()


def test_cli_skill_matcher_list_json():
    result = runner.invoke(app, ["skill-matcher", "list", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) >= 5


def test_cli_skill_matcher_match_json():
    result = runner.invoke(app, ["skill-matcher", "match", "carrossel instagram post", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["capability_id"] is not None


def test_cli_skill_matcher_match_no_results():
    result = runner.invoke(app, ["skill-matcher", "match", "xyzzy nonsense"])
    assert result.exit_code == 0


def test_cli_skill_matcher_show_found():
    result = runner.invoke(app, ["skill-matcher", "show", "offline_package_carousel", "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["capability_id"] == "offline_package_carousel"


def test_cli_skill_matcher_show_not_found():
    result = runner.invoke(app, ["skill-matcher", "show", "nonexistent_cap"])
    assert result.exit_code != 0
