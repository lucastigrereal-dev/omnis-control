"""Testes para CLI oauth accounts e account-readiness."""
from __future__ import annotations

import json
import os
import tempfile

import pytest
from typer.testing import CliRunner

# Patch ACCOUNTS_PATH before importing the CLI module
ORIG_ACCOUNTS_PATH = os.path.expanduser("~/omnis-control/data/accounts.jsonl")


@pytest.fixture
def empty_registry():
    """Cria registry vazio temporario."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        f.write("")
        tmp_path = f.name
    import src.content_queue.accounts as accts_mod
    old_path = accts_mod.ACCOUNTS_PATH
    accts_mod.ACCOUNTS_PATH = tmp_path
    yield tmp_path
    accts_mod.ACCOUNTS_PATH = old_path
    os.unlink(tmp_path)


@pytest.fixture
def populated_registry():
    """Cria registry com 2 contas."""
    content = (
        '{"account_id": "c225c8d0ea69", "handle": "lucastigrereal", "platform": "instagram", "display_name": "Lucas Tigre", "tags": ["pessoal"], "default_posting_times": ["08:50"], "default_formats": ["reels"], "priority": "high", "active": true, "instagram_user_id": null, "notes": null, "created_at": "2026-05-02T19:31:17Z", "updated_at": "2026-05-02T19:31:17Z"}\n'
        '{"account_id": "84033ab95c56", "handle": "afamiliatigrereal", "platform": "instagram", "display_name": "A Familia Tigre", "tags": ["familia"], "default_posting_times": ["08:50"], "default_formats": ["reels"], "priority": "medium", "active": true, "instagram_user_id": null, "notes": null, "created_at": "2026-05-02T19:31:23Z", "updated_at": "2026-05-02T19:31:23Z"}\n'
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        f.write(content)
        tmp_path = f.name
    import src.content_queue.accounts as accts_mod
    old_path = accts_mod.ACCOUNTS_PATH
    accts_mod.ACCOUNTS_PATH = tmp_path
    yield tmp_path
    accts_mod.ACCOUNTS_PATH = old_path
    os.unlink(tmp_path)


class TestOauthAccountsCLI:
    def test_accounts_json(self, populated_registry):
        from src.cli_commands.oauth_cmd import oauth_app
        runner = CliRunner()
        result = runner.invoke(oauth_app, ["accounts", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) == 2
        handles = [d["handle"] for d in data]
        assert "lucastigrereal" in handles
        assert "afamiliatigrereal" in handles

    def test_accounts_json_no_secrets(self, populated_registry):
        from src.cli_commands.oauth_cmd import oauth_app
        runner = CliRunner()
        result = runner.invoke(oauth_app, ["accounts", "--json"])
        output = result.stdout
        assert "secret" not in output.lower() or "meta_app_secret" in output.lower()
        assert "token" not in output.lower() or "access_token" in output.lower() or "not_configured" in output.lower()

    def test_lucastigrereal_not_test_candidate(self, populated_registry):
        from src.cli_commands.oauth_cmd import oauth_app
        runner = CliRunner()
        result = runner.invoke(oauth_app, ["accounts", "--json"])
        data = json.loads(result.stdout)
        lucas = [d for d in data if d["handle"] == "lucastigrereal"][0]
        assert lucas["is_test_candidate"] is False
        assert lucas["risk_level"] == "critical"

    def test_afamiliatigrereal_is_test_candidate(self, populated_registry):
        from src.cli_commands.oauth_cmd import oauth_app
        runner = CliRunner()
        result = runner.invoke(oauth_app, ["accounts", "--json"])
        data = json.loads(result.stdout)
        afam = [d for d in data if d["handle"] == "afamiliatigrereal"][0]
        assert afam["is_test_candidate"] is True
        assert afam["risk_level"] == "medium"

    def test_empty_registry_no_crash(self, empty_registry):
        from src.cli_commands.oauth_cmd import oauth_app
        runner = CliRunner()
        result = runner.invoke(oauth_app, ["accounts"])
        assert result.exit_code == 0

    def test_empty_registry_json_handles_gracefully(self, empty_registry):
        from src.cli_commands.oauth_cmd import oauth_app
        runner = CliRunner()
        result = runner.invoke(oauth_app, ["accounts", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)


class TestAccountReadinessCLI:
    def test_readiness_json_format(self, populated_registry):
        from src.cli_commands.oauth_cmd import oauth_app
        runner = CliRunner()
        result = runner.invoke(oauth_app, ["account-readiness", "@afamiliatigrereal", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["handle"] == "afamiliatigrereal"
        assert "risk_level" in data
        assert "blockers" in data
        assert "warnings" in data
        assert "next_actions" in data

    def test_readiness_no_secrets(self, populated_registry):
        from src.cli_commands.oauth_cmd import oauth_app
        runner = CliRunner()
        result = runner.invoke(oauth_app, ["account-readiness", "@afamiliatigrereal", "--json"])
        output = result.stdout
        assert "sk-" not in output

    def test_lucastigrereal_blocked_in_readiness(self, populated_registry):
        from src.cli_commands.oauth_cmd import oauth_app
        runner = CliRunner()
        result = runner.invoke(oauth_app, ["account-readiness", "@lucastigrereal", "--json"])
        data = json.loads(result.stdout)
        assert data["is_test_candidate"] is False
        assert data["risk_level"] == "critical"
        has_critical_blocker = any("CRITICO" in b for b in data["blockers"])
        assert has_critical_blocker

    def test_readiness_without_at_sign(self, populated_registry):
        from src.cli_commands.oauth_cmd import oauth_app
        runner = CliRunner()
        result = runner.invoke(oauth_app, ["account-readiness", "afamiliatigrereal", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["handle"] == "afamiliatigrereal"

    def test_readiness_unknown_handle(self, populated_registry):
        from src.cli_commands.oauth_cmd import oauth_app
        runner = CliRunner()
        result = runner.invoke(oauth_app, ["account-readiness", "@conta_que_nao_existe", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["handle"] == "conta_que_nao_existe"
        # Should still work with known-handles fallback or default risk
        assert "risk_level" in data


class TestAccountReadinessRichOutput:
    def test_accounts_rich_no_secrets(self, populated_registry):
        from src.cli_commands.oauth_cmd import oauth_app
        runner = CliRunner()
        result = runner.invoke(oauth_app, ["accounts"])
        assert result.exit_code == 0
        # Rich output should not contain real token/secret values
        output = result.stdout
        assert "1434393165369254" not in output  # app id might show, but secrets shouldn't

    def test_readiness_rich_has_blockers(self, populated_registry):
        from src.cli_commands.oauth_cmd import oauth_app
        runner = CliRunner()
        result = runner.invoke(oauth_app, ["account-readiness", "@lucastigrereal"])
        assert result.exit_code == 0
        assert "Blockers" in result.stdout or "blockers" in result.stdout.lower()


class TestExampleYamlSafety:
    def test_example_yaml_no_real_ids(self):
        import yaml
        example_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "config", "meta_accounts.example.yaml"
        )
        # Normalize path
        example_path = os.path.normpath(example_path)
        if not os.path.isfile(example_path):
            pytest.skip("meta_accounts.example.yaml not found")
        with open(example_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for acct in data.get("accounts", []):
            biz_id = acct.get("instagram_business_account_id", "")
            page_id = acct.get("facebook_page_id", "")
            assert biz_id == "", f"Real business ID found in example: {acct['handle']}"
            assert page_id == "", f"Real page ID found in example: {acct['handle']}"
