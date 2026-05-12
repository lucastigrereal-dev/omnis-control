"""Tests for OutputGenerator CLI commands."""
from __future__ import annotations

import json
import tempfile

from typer.testing import CliRunner

from src.cli_commands.output_generator_cmd import output_generator_app
from src.work_order.models import (
    OutputContract,
    OutputType,
    WorkOrder,
    WorkOrderStatus,
    make_work_order_id,
)

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


def test_write_markdown_missing_work_order():
    result = runner.invoke(output_generator_app, ["write-markdown", "wo_nonexistent123"])
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


def test_write_markdown_in_help():
    result = runner.invoke(output_generator_app, ["--help"])
    assert result.exit_code == 0
    assert "write-markdown" in result.stdout


def test_write_json_in_help():
    result = runner.invoke(output_generator_app, ["--help"])
    assert result.exit_code == 0
    assert "write-json" in result.stdout


def test_write_spec_in_help():
    result = runner.invoke(output_generator_app, ["--help"])
    assert result.exit_code == 0
    assert "write-spec" in result.stdout


def test_write_json_missing_work_order():
    result = runner.invoke(output_generator_app, ["write-json", "wo_nonexistent123"])
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


def test_write_spec_missing_work_order():
    result = runner.invoke(output_generator_app, ["write-spec", "wo_nonexistent123"])
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


def test_write_csv_in_help():
    result = runner.invoke(output_generator_app, ["--help"])
    assert result.exit_code == 0
    assert "write-csv" in result.stdout


def test_write_csv_missing_work_order():
    result = runner.invoke(output_generator_app, ["write-csv", "wo_nonexistent123"])
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


def test_package_in_help():
    result = runner.invoke(output_generator_app, ["--help"])
    assert result.exit_code == 0
    assert "package" in result.stdout


def test_package_missing_work_order():
    result = runner.invoke(output_generator_app, ["package", "wo_nonexistent123"])
    assert result.exit_code == 1
    assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()
