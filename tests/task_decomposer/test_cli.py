"""CLI tests for Task Decomposer."""
import json
import pytest
from typer.testing import CliRunner
from src.cli import app

runner = CliRunner()


def test_cli_tasks_plan_help():
    result = runner.invoke(app, ["tasks-plan", "--help"])
    assert result.exit_code == 0
    assert "from-request" in result.output


def test_cli_tasks_plan_from_request():
    result = runner.invoke(app, ["tasks-plan", "from-request", "cria campanha de posts para hotel"])
    assert result.exit_code == 0


def test_cli_tasks_plan_from_request_json():
    result = runner.invoke(app, ["tasks-plan", "from-request", "cria campanha de posts para hotel", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["task_plan_id"].startswith("tplan_")
    assert len(data["tasks"]) >= 2


def test_cli_tasks_plan_app_is_high_risk():
    result = runner.invoke(app, ["tasks-plan", "from-request", "cria app CRM com dashboard", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["approval_required"] is True
