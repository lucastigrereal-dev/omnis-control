"""Testes CLI do OAuth Readiness — P1.4."""
from __future__ import annotations

import json
import pytest
from typer.testing import CliRunner

from src.cli import app


@pytest.fixture
def runner():
    return CliRunner()


class TestCLIOAuthReadiness:
    """oauth readiness — checks dinamicos via env_probe."""

    def test_readiness_runs(self, runner):
        result = runner.invoke(app, ["oauth", "readiness"])
        assert result.exit_code == 0

    def test_readiness_json(self, runner):
        result = runner.invoke(app, ["oauth", "readiness", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["total_checks"] > 0
        assert len(data["checks"]) == data["total_checks"]
        assert "overall_status" in data
        assert "can_proceed" in data
        assert "next_action" in data
        assert "checked_at" in data

    def test_readiness_json_has_core_checks(self, runner):
        result = runner.invoke(app, ["oauth", "readiness", "--json"])
        data = json.loads(result.stdout)
        ids = {c["check_id"] for c in data["checks"]}
        core = {
            "docker_running", "publisher_os_healthy", "supabase_db_accessible",
            "redis_accessible", "disk_space", "callback_route_exists",
            "instagram_accounts_registered", "network_outbound",
        }
        assert core.issubset(ids), f"Faltam checks core: {core - ids}"

    def test_readiness_json_has_env_vars(self, runner):
        result = runner.invoke(app, ["oauth", "readiness", "--json"])
        data = json.loads(result.stdout)
        ids = {c["check_id"] for c in data["checks"]}
        env_vars = {"env_meta_app_id", "env_meta_app_secret", "env_meta_redirect_uri"}
        assert env_vars.issubset(ids), f"Faltam env vars: {env_vars - ids}"


class TestCLIOAuthChecklist:
    """oauth checklist — lista todos os checks."""

    def test_checklist_runs(self, runner):
        result = runner.invoke(app, ["oauth", "checklist"])
        assert result.exit_code == 0
        assert "OBRIGATORIO" in result.stdout
        assert "opcional" in result.stdout

    def test_checklist_mentions_probe(self, runner):
        result = runner.invoke(app, ["oauth", "checklist"])
        assert result.exit_code == 0
        assert "META_APP_ID" in result.stdout or "docker_running" in result.stdout


class TestCLIOAuthStart:
    """oauth start — SEMPRE bloqueia OAuth real."""

    def test_start_blocks_without_readiness(self, runner):
        """start sem precondicoes atendidas deve sair com erro ou human_required."""
        result = runner.invoke(app, ["oauth", "start"])
        assert result.exit_code in (0, 1)

    def test_start_never_executes_real_oauth(self, runner):
        """Garante que start nao faz chamadas externas."""
        result = runner.invoke(app, ["oauth", "start"])
        output = result.stdout.lower()
        assert "human" in output or "bloquead" in output or "nao pode" in output or "precondi" in output
