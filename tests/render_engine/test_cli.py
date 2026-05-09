"""Tests for render CLI commands."""
import json
import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path

import src.cli_commands.render_cmd as render_cmd_mod
from src.cli_commands.render_cmd import render_app
from src.render_engine.models import RenderResult, RenderStatus
from src.render_engine.errors import PackageNotFoundError


runner = CliRunner()

FAKE_RESULT = RenderResult(
    render_id="render_abc12345",
    package_id="carousel_0b79aa1c_test",
    status=RenderStatus.OK,
    html_path="/tmp/preview.html",
    render_manifest_path="/tmp/render_manifest.json",
    files_generated=["preview.html", "render_manifest.json"],
)


class TestRenderPackageCmd:
    def test_success_output_contains_render_id(self):
        with patch.object(render_cmd_mod, "render_package", return_value=FAKE_RESULT):
            result = runner.invoke(render_app, ["package", "carousel_0b79aa1c_test"])
        assert "render_abc12345" in result.output

    def test_success_exit_code_zero(self):
        with patch.object(render_cmd_mod, "render_package", return_value=FAKE_RESULT):
            result = runner.invoke(render_app, ["package", "carousel_0b79aa1c_test"])
        assert result.exit_code == 0

    def test_not_found_exits_nonzero(self):
        with patch.object(render_cmd_mod, "render_package", side_effect=PackageNotFoundError("x")):
            result = runner.invoke(render_app, ["package", "bad_id"])
        assert result.exit_code != 0

    def test_json_flag_outputs_json(self):
        with patch.object(render_cmd_mod, "render_package", return_value=FAKE_RESULT):
            result = runner.invoke(render_app, ["package", "carousel_0b79aa1c_test", "--json"])
        data = json.loads(result.output)
        assert data["render_id"] == "render_abc12345"

    def test_failed_result_exits_nonzero(self):
        failed = RenderResult(
            render_id="render_fail",
            package_id="pkg",
            status=RenderStatus.FAILED,
            errors=["Something broke"],
        )
        with patch.object(render_cmd_mod, "render_package", return_value=failed):
            result = runner.invoke(render_app, ["package", "bad_pkg"])
        assert result.exit_code != 0


class TestRenderListCmd:
    def test_empty_message_when_no_renders(self):
        with patch.object(render_cmd_mod, "list_renders", return_value=[]):
            result = runner.invoke(render_app, ["list"])
        assert "Nenhum" in result.output

    def test_shows_render_ids(self):
        with patch.object(render_cmd_mod, "list_renders", return_value=[FAKE_RESULT.to_dict()]):
            result = runner.invoke(render_app, ["list"])
        assert "render_abc12345" in result.output


class TestRenderShowCmd:
    def test_not_found_exits_nonzero(self):
        with patch.object(render_cmd_mod, "get_render", return_value=None):
            result = runner.invoke(render_app, ["show", "bad_id"])
        assert result.exit_code != 0

    def test_shows_json_when_found(self):
        with patch.object(render_cmd_mod, "get_render", return_value=FAKE_RESULT.to_dict()):
            result = runner.invoke(render_app, ["show", "render_abc"])
        data = json.loads(result.output)
        assert data["render_id"] == "render_abc12345"
