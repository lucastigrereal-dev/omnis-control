"""Tests for quality CLI."""
import json
import pytest
from typer.testing import CliRunner
from unittest.mock import patch

import src.cli_commands.quality_cmd as quality_cmd_mod
from src.cli_commands.quality_cmd import quality_app
from src.quality_layer.models import QualityResult, QualityGrade
from src.quality_layer.errors import PackageNotFoundError


runner = CliRunner()

FAKE_RESULT = QualityResult(
    package_id="carousel_test",
    score=95,
    grade=QualityGrade.READY,
    checks_passed=["Manifest.json presente", "caption.md presente"],
    checks_failed=[],
    warnings=[],
)

FAKE_BLOCKED = QualityResult(
    package_id="carousel_test",
    score=40,
    grade=QualityGrade.BLOCKED,
    checks_passed=[],
    checks_failed=["Manifest.json presente", "caption.md nao vazio"],
    warnings=["HTML preview nao encontrado"],
)


class TestQualityPackageCmd:
    def test_success_shows_score(self):
        with patch.object(quality_cmd_mod, "score_package", return_value=FAKE_RESULT):
            result = runner.invoke(quality_app, ["package", "carousel_test"])
        assert "95" in result.output

    def test_success_exit_zero(self):
        with patch.object(quality_cmd_mod, "score_package", return_value=FAKE_RESULT):
            result = runner.invoke(quality_app, ["package", "carousel_test"])
        assert result.exit_code == 0

    def test_not_found_exits_nonzero(self):
        with patch.object(quality_cmd_mod, "score_package", side_effect=PackageNotFoundError("x")):
            result = runner.invoke(quality_app, ["package", "bad_id"])
        assert result.exit_code != 0

    def test_json_flag_outputs_valid_json(self):
        with patch.object(quality_cmd_mod, "score_package", return_value=FAKE_RESULT):
            result = runner.invoke(quality_app, ["package", "carousel_test", "--json"])
        data = json.loads(result.output)
        assert data["score"] == 95
        assert data["grade"] == "ready_for_human_review"

    def test_blocked_shows_failed_checks(self):
        with patch.object(quality_cmd_mod, "score_package", return_value=FAKE_BLOCKED):
            result = runner.invoke(quality_app, ["package", "carousel_test"])
        assert "FALHOU" in result.output

    def test_warnings_shown(self):
        with patch.object(quality_cmd_mod, "score_package", return_value=FAKE_BLOCKED):
            result = runner.invoke(quality_app, ["package", "carousel_test"])
        assert "AVISO" in result.output
