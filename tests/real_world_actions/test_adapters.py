"""Tests for P27 Action Adapters."""
import pytest

from src.real_world_actions.adapters import ActionAdapter, get_adapter, register_adapter, list_providers
from src.real_world_actions.adapters.email_adapter import EmailAdapter
from src.real_world_actions.adapters.instagram_adapter import InstagramAdapter
from src.real_world_actions.adapters.webhook_adapter import WebhookAdapter
from src.real_world_actions.adapters.github_adapter import GitHubAdapter
from src.real_world_actions.adapters.n8n_adapter import N8nAdapter
from src.real_world_actions.adapters.slack_adapter import SlackAdapter
from src.real_world_actions.adapters.mock_adapter import MockAdapter


class TestMockAdapter:
    @pytest.fixture
    def adapter(self):
        return MockAdapter()

    def test_provider(self, adapter):
        assert adapter.provider == "mock"

    def test_supported_actions(self, adapter):
        assert "health_check" in adapter.supported_actions

    def test_execute_echo(self, adapter):
        result = adapter.execute("echo", {"msg": "hello"})
        assert result["echo"]["msg"] == "hello"

    def test_execute_health_check(self, adapter):
        result = adapter.execute("health_check", {})
        assert result["status"] == "healthy"

    def test_health_check_returns_true(self, adapter):
        assert adapter.health_check() is True

    def test_validate_params_empty(self, adapter):
        assert adapter.validate_params("any", {}) == []


class TestEmailAdapter:
    @pytest.fixture
    def adapter(self):
        return EmailAdapter()

    def test_provider(self, adapter):
        assert adapter.provider == "gmail"

    def test_send_email(self, adapter):
        result = adapter.execute("send_email", {"to": "a@b.com", "subject": "Test", "body": "Hello"})
        assert result["status"] == "dry_run"
        assert result["to"] == "a@b.com"

    def test_validate_requires_to(self, adapter):
        errors = adapter.validate_params("send_email", {})
        assert len(errors) >= 1

    def test_health_check(self, adapter):
        assert adapter.health_check() is True


class TestInstagramAdapter:
    @pytest.fixture
    def adapter(self):
        return InstagramAdapter()

    def test_provider(self, adapter):
        assert adapter.provider == "instagram"

    def test_post_instagram(self, adapter):
        result = adapter.execute("post_instagram", {"caption": "Hello world", "media_url": "https://img.jpg"})
        assert result["status"] == "dry_run"
        assert result["caption"] == "Hello world"

    def test_validate_requires_caption(self, adapter):
        errors = adapter.validate_params("post_instagram", {})
        assert len(errors) >= 1

    def test_health_check(self, adapter):
        assert adapter.health_check() is True


class TestWebhookAdapter:
    @pytest.fixture
    def adapter(self):
        return WebhookAdapter()

    def test_provider(self, adapter):
        assert adapter.provider == "webhook"

    def test_call_webhook(self, adapter):
        result = adapter.execute("call_webhook", {"url": "https://hook.example.com", "payload": {"k": "v"}})
        assert result["status"] == "dry_run"
        assert result["url"] == "https://hook.example.com"

    def test_validate_requires_url(self, adapter):
        errors = adapter.validate_params("call_webhook", {})
        assert len(errors) >= 1

    def test_health_check(self, adapter):
        assert adapter.health_check() is True


class TestGitHubAdapter:
    @pytest.fixture
    def adapter(self):
        return GitHubAdapter()

    def test_provider(self, adapter):
        assert adapter.provider == "github"

    def test_git_push(self, adapter):
        result = adapter.execute("git_push", {"branch": "main"})
        assert result["status"] == "dry_run"
        assert result["branch"] == "main"

    def test_create_pr(self, adapter):
        result = adapter.execute("create_pr", {"title": "Fix bug", "head": "fix/bug"})
        assert result["status"] == "dry_run"
        assert result["title"] == "Fix bug"

    def test_validate_push_requires_branch(self, adapter):
        errors = adapter.validate_params("git_push", {})
        assert len(errors) >= 1

    def test_validate_pr_requires_title(self, adapter):
        errors = adapter.validate_params("create_pr", {})
        assert len(errors) >= 1

    def test_health_check(self, adapter):
        assert adapter.health_check() is True


class TestN8nAdapter:
    @pytest.fixture
    def adapter(self):
        return N8nAdapter()

    def test_provider(self, adapter):
        assert adapter.provider == "n8n"

    def test_trigger_workflow(self, adapter):
        result = adapter.execute("trigger_n8n_workflow", {"workflow_id": "wf_123"})
        assert result["status"] == "dry_run"
        assert result["workflow_id"] == "wf_123"

    def test_validate_requires_workflow_id_or_url(self, adapter):
        errors = adapter.validate_params("trigger_n8n_workflow", {})
        assert len(errors) >= 1

    def test_health_check(self, adapter):
        assert adapter.health_check() is True


class TestSlackAdapter:
    @pytest.fixture
    def adapter(self):
        return SlackAdapter()

    def test_provider(self, adapter):
        assert adapter.provider == "slack"

    def test_send_message(self, adapter):
        result = adapter.execute("send_slack_message", {"channel": "#general", "text": "Hello"})
        assert result["status"] == "dry_run"
        assert result["channel"] == "#general"

    def test_validate_requires_channel_and_text(self, adapter):
        errors = adapter.validate_params("send_slack_message", {})
        assert len(errors) >= 2

    def test_health_check(self, adapter):
        assert adapter.health_check() is True


class TestAdapterRegistryIntegration:
    @pytest.fixture(autouse=True)
    def setup_registry(self):
        # Register all adapters
        from src.real_world_actions.adapters.email_adapter import register as reg_email
        from src.real_world_actions.adapters.instagram_adapter import register as reg_ig
        from src.real_world_actions.adapters.webhook_adapter import register as reg_wh
        from src.real_world_actions.adapters.github_adapter import register as reg_gh
        from src.real_world_actions.adapters.n8n_adapter import register as reg_n8n
        from src.real_world_actions.adapters.slack_adapter import register as reg_slack
        from src.real_world_actions.adapters.mock_adapter import register as reg_mock
        reg_email()
        reg_ig()
        reg_wh()
        reg_gh()
        reg_n8n()
        reg_slack()
        reg_mock()

    def test_all_adapters_registered(self):
        providers = list_providers()
        assert "gmail" in providers
        assert "github" in providers
        assert "n8n" in providers
        assert "mock" in providers

    def test_get_adapter_returns_instance(self):
        adapter = get_adapter("github")
        assert adapter is not None
        assert adapter.provider == "github"

    def test_get_missing_adapter_returns_none(self):
        assert get_adapter("nonexistent") is None

    def test_all_adapters_implement_contract(self):
        for provider in list_providers():
            adapter = get_adapter(provider)
            assert adapter is not None
            assert hasattr(adapter, 'provider')
            assert hasattr(adapter, 'supported_actions')
            assert hasattr(adapter, 'execute')
            assert hasattr(adapter, 'health_check')
            assert hasattr(adapter, 'validate_params')
            # Each adapter returns a non-empty provider string
            assert adapter.provider
            assert len(adapter.supported_actions) >= 1
