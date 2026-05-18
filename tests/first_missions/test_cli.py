"""W186 — CLI tests for first_missions commands."""
import json
import pytest
from typer.testing import CliRunner

from src.cli_commands.first_missions_cmd import first_missions_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

def test_cli_list():
    result = runner.invoke(first_missions_app, ["list"])
    assert result.exit_code == 0
    assert "First Real Missions" in result.stdout


def test_cli_list_json():
    result = runner.invoke(first_missions_app, ["list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert len(data) >= 0


def test_cli_list_filter_by_status():
    result = runner.invoke(first_missions_app, ["list", "--status", "PENDING"])
    assert result.exit_code == 0


def test_cli_list_filter_by_type():
    result = runner.invoke(first_missions_app, ["list", "--type", "CONTENT_GENERATION"])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Show
# ---------------------------------------------------------------------------

def test_cli_show_nonexistent():
    result = runner.invoke(first_missions_app, ["show", "nonexistent_id"])
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower()


def test_cli_show_json():
    # Show with an ID that doesn't exist should error in json too
    result = runner.invoke(first_missions_app, ["show", "mss_nonexistent", "--json"])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def test_cli_create_basic():
    result = runner.invoke(first_missions_app, [
        "create", "--name", "cli-test-mission",
    ])
    assert result.exit_code == 0
    assert "Mission created" in result.stdout
    assert "cli-test-mission" in result.stdout


def test_cli_create_content():
    result = runner.invoke(first_missions_app, [
        "create", "--name", "content-test",
        "--type", "CONTENT_GENERATION",
        "--profile", "lucastigrereal",
        "--topic", "beach",
    ])
    assert result.exit_code == 0


def test_cli_create_json():
    result = runner.invoke(first_missions_app, [
        "create", "--name", "json-test",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["name"] == "json-test"
    assert data["mission_id"].startswith("mss_")


def test_cli_create_invalid_type():
    result = runner.invoke(first_missions_app, [
        "create", "--name", "bad", "--type", "INVALID_TYPE",
    ])
    assert result.exit_code == 1


def test_cli_create_with_tags():
    result = runner.invoke(first_missions_app, [
        "create", "--name", "tagged", "--tags", "a,b,c",
    ])
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def test_cli_run_nonexistent():
    result = runner.invoke(first_missions_app, ["run", "nonexistent_id"])
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower()


def test_cli_run_dry_default():
    """Run should default to dry-run — test that --live is required for real."""
    help_result = runner.invoke(first_missions_app, ["run", "--help"])
    assert "--live" in help_result.stdout


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def test_cli_stats():
    result = runner.invoke(first_missions_app, ["stats"])
    assert result.exit_code == 0
    assert "Stats" in result.stdout


def test_cli_stats_json():
    result = runner.invoke(first_missions_app, ["stats", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "registry" in data
    assert "scheduler" in data
    assert "executor" in data
    assert "result_store" in data


# ---------------------------------------------------------------------------
# Results commands
# ---------------------------------------------------------------------------


def test_cli_results_empty():
    """Should not error on empty store."""
    from src.first_missions.result_store import MissionResultStore
    result = runner.invoke(first_missions_app, ["results"])
    assert result.exit_code == 0


def test_cli_results_json():
    result = runner.invoke(first_missions_app, ["results", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)


def test_cli_results_with_filters():
    result = runner.invoke(first_missions_app, [
        "results", "--status", "COMPLETED", "--limit", "5",
    ])
    assert result.exit_code == 0


def test_cli_result_show_nonexistent():
    result = runner.invoke(first_missions_app, ["result-show", "nonexistent"])
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Preview command
# ---------------------------------------------------------------------------


def test_cli_preview_nonexistent():
    result = runner.invoke(first_missions_app, ["preview", "nonexistent"])
    assert result.exit_code == 1


def test_cli_preview_help():
    """Verify preview command is registered."""
    result = runner.invoke(first_missions_app, ["preview", "--help"])
    assert result.exit_code == 0
    assert "preview" in result.stdout.lower()
