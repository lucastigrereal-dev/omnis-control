"""Tests for OutputGenerator CLI commands."""
from __future__ import annotations

import json

from typer.testing import CliRunner

from src.cli_commands.output_generator_cmd import output_generator_app

runner = CliRunner()


def test_list_command():
    result = runner.invoke(output_generator_app, ["list"])
    assert result.exit_code == 0
    # Rich table may truncate long IDs — check for partial match
    assert "markdown_basic" in result.stdout
    assert "json_basic_writer" in result.stdout


def test_list_no_error():
    result = runner.invoke(output_generator_app, ["list"])
    assert "Error" not in result.stdout


def test_show_existing_generator():
    result = runner.invoke(output_generator_app, ["show", "markdown_basic_writer"])
    assert result.exit_code == 0
    assert "markdown_basic_writer" in result.stdout


def test_show_json_output():
    result = runner.invoke(
        output_generator_app, ["show", "markdown_basic_writer", "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["generator_id"] == "markdown_basic_writer"


def test_show_missing_generator():
    result = runner.invoke(output_generator_app, ["show", "ghost_generator"])
    assert result.exit_code == 1
    assert "nao encontrado" in result.stdout.lower()


def test_select_active_type():
    result = runner.invoke(output_generator_app, ["select", "markdown"])
    assert result.exit_code == 0
    assert "SELECTED" in result.stdout


def test_select_json_output():
    result = runner.invoke(output_generator_app, ["select", "markdown", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["status"] == "selected"


def test_select_no_generator_type():
    result = runner.invoke(output_generator_app, ["select", "video_plan"])
    assert result.exit_code == 0
    assert "NO_GENERATOR" in result.stdout or "no_generator" in result.stdout.lower()
