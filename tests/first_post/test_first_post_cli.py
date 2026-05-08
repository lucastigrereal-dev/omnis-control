"""Tests para First Post Preflight CLI — P1.3a."""
from __future__ import annotations

import json
import pytest
from typer.testing import CliRunner

from src.cli import app


@pytest.fixture
def runner():
    return CliRunner()


class TestCLIPostPreflight:
    """post preflight — 8 checks de preparacao."""

    def test_preflight_runs(self, runner):
        result = runner.invoke(app, ["post", "preflight"])
        assert result.exit_code == 0
        assert "First Post" in result.stdout or "Preflight" in result.stdout

    def test_preflight_json(self, runner):
        result = runner.invoke(app, ["post", "preflight", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["total_checks"] == 8
        assert len(data["checks"]) == 8
        assert "overall_status" in data
        assert "can_publish" in data
        assert "ready_items" in data
        assert "next_action" in data
        assert "checked_at" in data

    def test_preflight_json_has_all_check_ids(self, runner):
        result = runner.invoke(app, ["post", "preflight", "--json"])
        data = json.loads(result.stdout)
        ids = {c["check_id"] for c in data["checks"]}
        expected = {
            "queue_items", "approved_content", "assets_ready",
            "publisher_healthy", "disk_space", "caption_complete",
            "no_placeholders", "accounts_active",
        }
        assert ids == expected


class TestCLIPostStatus:
    """post status — status rapido."""

    def test_status_runs(self, runner):
        result = runner.invoke(app, ["post", "status"])
        assert result.exit_code == 0
        assert "ready_items" in result.stdout.lower() or "itens prontos" in result.stdout.lower()

    def test_status_json(self, runner):
        result = runner.invoke(app, ["post", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "overall_status" in data
        assert "ready_items" in data
        assert "can_publish" in data


class TestCLIPostPackage:
    """post package — empacota conteudo."""

    def test_package_no_args(self, runner):
        result = runner.invoke(app, ["post", "package"])
        # Pode falhar (exit 1) se nao houver conteudo pronto
        assert result.exit_code in (0, 1)

    def test_package_json(self, runner):
        result = runner.invoke(app, ["post", "package", "--json"])
        assert result.exit_code in (0, 1)
