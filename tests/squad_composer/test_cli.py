"""CLI tests for Squad Composer."""
import json
import pytest
from typer.testing import CliRunner
from src.cli import app

runner = CliRunner()


def test_cli_squad_help():
    result = runner.invoke(app, ["squad", "--help"])
    assert result.exit_code == 0
    assert "compose" in result.output


def test_cli_squad_compose_marketing():
    result = runner.invoke(app, ["squad", "compose", "cria campanha de posts para hotel"])
    assert result.exit_code == 0


def test_cli_squad_compose_json():
    result = runner.invoke(app, ["squad", "compose", "cria campanha de posts para hotel", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["squad_id"].startswith("squad_")
    assert data["sector"] == "marketing"
    ids = [r["role_id"] for r in data["roles"]]
    assert "copywriter" in ids


def test_cli_squad_compose_app_is_high_risk():
    result = runner.invoke(app, ["squad", "compose", "cria app CRM com dashboard", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["approval_required"] is True
