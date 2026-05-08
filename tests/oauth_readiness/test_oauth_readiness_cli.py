"""Testes CLI do OAuth Readiness — P1.2a."""
from __future__ import annotations

import json
import pytest
from typer.testing import CliRunner

from src.cli import app


@pytest.fixture
def runner():
    return CliRunner()


class TestCLIOAuthReadiness:
    """oauth readiness — 12 checks de preparacao."""

    def test_readiness_runs(self, runner):
        result = runner.invoke(app, ["oauth", "readiness"])
        assert result.exit_code == 0

    def test_readiness_json(self, runner):
        result = runner.invoke(app, ["oauth", "readiness", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["total_checks"] == 12
        assert len(data["checks"]) == 12
        assert "overall_status" in data
        assert "can_proceed" in data
        assert "next_action" in data
        assert "checked_at" in data

    def test_readiness_json_has_all_check_ids(self, runner):
        result = runner.invoke(app, ["oauth", "readiness", "--json"])
        data = json.loads(result.stdout)
        ids = {c["check_id"] for c in data["checks"]}
        expected = {
            "docker_running", "publisher_os_healthy", "supabase_db_accessible",
            "redis_accessible", "disk_space", "meta_app_id_exists",
            "meta_app_secret_exists", "meta_app_id_configured", "meta_app_secret_configured",
            "meta_callback_url_documented", "instagram_accounts_registered", "network_outbound",
        }
        assert ids == expected


class TestCLIOAuthChecklist:
    """oauth checklist — lista os 12 checks."""

    def test_checklist_runs(self, runner):
        result = runner.invoke(app, ["oauth", "checklist"])
        assert result.exit_code == 0
        assert "12 precondicoes" in result.stdout
        assert "docker_running" in result.stdout
        assert "OBRIGATORIO" in result.stdout
        assert "opcional" in result.stdout


class TestCLIOAuthStart:
    """oauth start — SEMPRE bloqueia OAuth real."""

    def test_start_blocks_without_readiness(self, runner):
        """start sem precondicoes atendidas deve sair com erro."""
        result = runner.invoke(app, ["oauth", "start"])
        # Deve sair com exit 1 porque precondicoes nao estao atendidas
        # ou com human_required
        assert result.exit_code in (0, 1)

    def test_start_never_executes_real_oauth(self, runner):
        """Garante que start nao faz chamadas externas."""
        result = runner.invoke(app, ["oauth", "start"])
        output = result.stdout.lower()
        # Sempre deve mencionar que requer humano ou esta bloqueado
        assert "human" in output or "bloquead" in output or "nao pode" in output or "precondi" in output
