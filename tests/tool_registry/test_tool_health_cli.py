"""Testes CLI do healthcheck — P1.1."""
from __future__ import annotations

import json
import pytest
from typer.testing import CliRunner

from src.cli import app
from src.tool_registry.registry import ToolRegistry
from src.tool_registry.discovery import discover_known_tools


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def populated_registry(tmp_path, monkeypatch):
    """Popula registry com todas as tools descobertas em tmp_path."""
    base = str(tmp_path / "tool_registry")

    def _mock_repo():
        return ToolRegistry(base_dir=base)

    monkeypatch.setattr("src.cli_commands.tools_cmd._repo", _mock_repo)

    registry = ToolRegistry(base_dir=base)
    tools = discover_known_tools()
    for t in tools:
        registry.add_tool(t)
    return base


class TestCLIToolsHealth:
    """tools health — healthcheck de uma ferramenta."""

    def test_health_nonexistent_returns_error(self, runner, populated_registry):
        result = runner.invoke(app, ["tools", "health", "ferramenta_inexistente"])
        assert result.exit_code == 1

    def test_health_local_filesystem_ok(self, runner, populated_registry):
        result = runner.invoke(app, ["tools", "health", "local_filesystem"])
        assert result.exit_code == 0
        assert "ok" in result.stdout.lower() or "OK" in result.stdout

    def test_health_local_filesystem_json(self, runner, populated_registry):
        result = runner.invoke(
            app, ["tools", "health", "local_filesystem", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["tool_id"] == "local_filesystem"
        assert data["health_status"] in ("ok", "degraded", "failed")

    def test_health_instagram_blocked(self, runner, populated_registry):
        result = runner.invoke(app, ["tools", "health", "instagram_graph_api"])
        assert result.exit_code == 0
        assert "blocked" in result.stdout.lower()

    def test_health_publer_not_checked(self, runner, populated_registry):
        result = runner.invoke(app, ["tools", "health", "publer"])
        assert result.exit_code == 0
        assert (
            "not_checked" in result.stdout.lower()
            or "not checked" in result.stdout.lower()
            or "nao possui" in result.stdout.lower()
        )

    def test_health_not_allowed_exit_1(self, runner, populated_registry):
        result = runner.invoke(app, ["tools", "health", "unknown_tool_xyz"])
        assert result.exit_code == 1


class TestCLIToolsHealthAll:
    """tools health-all — healthcheck em todas as ferramentas seguras."""

    def test_health_all_runs_safe_tools(self, runner, populated_registry):
        result = runner.invoke(app, ["tools", "health-all"])
        assert result.exit_code == 0
        assert "Resumo" in result.stdout
        assert "verificadas" in result.stdout

    def test_health_all_json(self, runner, populated_registry):
        result = runner.invoke(app, ["tools", "health-all", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) >= 4
        tool_ids = {r["tool_id"] for r in data}
        assert "instagram_graph_api" not in tool_ids
        assert "publer" not in tool_ids


class TestCLIToolsHealthReport:
    """tools health-report — relatorio de healthchecks."""

    def test_health_report_empty(self, runner, tmp_path, monkeypatch):
        """Sem tools cadastradas."""
        base = str(tmp_path / "tool_registry")

        def _mock_repo():
            return ToolRegistry(base_dir=base)

        monkeypatch.setattr("src.cli_commands.tools_cmd._repo", _mock_repo)
        result = runner.invoke(app, ["tools", "health-report"])
        assert result.exit_code == 0
        assert "Nenhum" in result.stdout or "discover" in result.stdout.lower()

    def test_health_report_after_health(self, runner, populated_registry):
        """Apos executar health, gera report."""
        # Primeiro executa um healthcheck
        runner.invoke(app, ["tools", "health", "local_filesystem"])
        # Depois gera report
        result = runner.invoke(app, ["tools", "health-report"])
        assert result.exit_code == 0
        assert "local_filesystem" in result.stdout

    def test_health_report_json(self, runner, populated_registry):
        runner.invoke(app, ["tools", "health", "local_filesystem"])
        result = runner.invoke(app, ["tools", "health-report", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        fs = [r for r in data if r["tool_id"] == "local_filesystem"]
        assert len(fs) >= 1
        assert "health_status" in fs[0]
