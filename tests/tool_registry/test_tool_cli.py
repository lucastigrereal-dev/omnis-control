"""Testes CLI do Tool Registry — P0.8."""
from __future__ import annotations

import json
import pytest
from typer.testing import CliRunner

from src.cli import app
from src.tool_registry.registry import ToolRegistry


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def empty_registry(tmp_path, monkeypatch):
    """Redireciona ToolRegistry para tmp_path."""
    base = str(tmp_path / "tool_registry")

    def _mock_repo():
        return ToolRegistry(base_dir=base)

    monkeypatch.setattr("src.cli_commands.tools_cmd._repo", _mock_repo)
    return base


class TestCLIToolsDiscover:
    """tools discover — descobre e popula."""

    def test_discover_output(self, runner, empty_registry):
        result = runner.invoke(app, ["tools", "discover"])
        assert result.exit_code == 0
        assert "Discovery concluido" in result.stdout
        assert "Adicionadas" in result.stdout

    def test_discover_json(self, runner, empty_registry):
        result = runner.invoke(app, ["tools", "discover", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["added"] >= 15

    def test_discover_idempotent(self, runner, empty_registry):
        runner.invoke(app, ["tools", "discover"])
        result2 = runner.invoke(app, ["tools", "discover"])
        assert result2.exit_code == 0
        assert "Puladas" in result2.stdout


class TestCLIToolsList:
    """tools list — lista com filtros."""

    def test_list_after_discover(self, runner, empty_registry):
        runner.invoke(app, ["tools", "discover"])
        result = runner.invoke(app, ["tools", "list"])
        assert result.exit_code == 0
        assert "instagram_graph_api" in result.stdout or "Ferramentas" in result.stdout

    def test_list_json(self, runner, empty_registry):
        runner.invoke(app, ["tools", "discover"])
        result = runner.invoke(app, ["tools", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) >= 15

    def test_list_filter_by_status(self, runner, empty_registry):
        runner.invoke(app, ["tools", "discover"])
        result = runner.invoke(app, ["tools", "list", "--status", "blocked"])
        assert result.exit_code == 0

    def test_list_filter_by_category(self, runner, empty_registry):
        runner.invoke(app, ["tools", "discover"])
        result = runner.invoke(app, ["tools", "list", "--category", "publishing"])
        assert result.exit_code == 0


class TestCLIToolsShow:
    """tools show — detalhes de uma ferramenta."""

    def test_show_instagram(self, runner, empty_registry):
        runner.invoke(app, ["tools", "discover"])
        result = runner.invoke(app, ["tools", "show", "instagram_graph_api"])
        assert result.exit_code == 0
        assert "blocked" in result.stdout.lower()

    def test_show_json(self, runner, empty_registry):
        runner.invoke(app, ["tools", "discover"])
        result = runner.invoke(app, ["tools", "show", "instagram_graph_api", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["tool_id"] == "instagram_graph_api"
        assert data["status"] == "blocked"

    def test_show_nonexistent(self, runner, empty_registry):
        result = runner.invoke(app, ["tools", "show", "nonexistent"])
        assert result.exit_code == 1


class TestCLIToolsStatus:
    """tools status — resumo."""

    def test_status_empty(self, runner, empty_registry):
        result = runner.invoke(app, ["tools", "status"])
        assert result.exit_code == 0
        assert "vazio" in result.stdout.lower() or "0" in result.stdout

    def test_status_after_discover(self, runner, empty_registry):
        runner.invoke(app, ["tools", "discover"])
        result = runner.invoke(app, ["tools", "status"])
        assert result.exit_code == 0
        assert "Tool Registry" in result.stdout

    def test_status_json(self, runner, empty_registry):
        runner.invoke(app, ["tools", "discover"])
        result = runner.invoke(app, ["tools", "status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "by_status" in data
        assert "by_category" in data


class TestCLIToolsUpdateStatus:
    """tools update-status — altera status com log."""

    def test_update_status(self, runner, empty_registry):
        runner.invoke(app, ["tools", "discover"])
        result = runner.invoke(app, ["tools", "update-status", "docker", "manual"])
        assert result.exit_code == 0
        assert "Status atualizado" in result.stdout
