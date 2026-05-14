"""Tests for P27 ActionRegistry."""
import pytest

from src.real_world_actions.registry import ActionRegistry
from src.real_world_actions.models import ActionDefinition, ACTION_SEND, ACTION_READ, ACTION_DEPLOY, RISK_HIGH, RISK_LOW
from src.real_world_actions.errors import UnknownActionError


class TestActionRegistry:
    @pytest.fixture
    def registry(self):
        r = ActionRegistry()
        r.seed_defaults()
        return r

    @pytest.fixture
    def empty_registry(self):
        return ActionRegistry()

    def test_seed_defaults_populates(self, registry):
        assert registry.count >= 5

    def test_find_by_name(self, registry):
        a = registry.find("send_email")
        assert a.name == "send_email"
        assert a.provider == "gmail"

    def test_find_by_name_missing_raises(self, registry):
        with pytest.raises(UnknownActionError):
            registry.find("nonexistent")

    def test_find_by_name_returns_none_safe(self, registry):
        assert registry.find_by_name("nonexistent") is None

    def test_register_new_action(self, empty_registry):
        a = ActionDefinition.new("custom_action", "mock", ACTION_READ)
        empty_registry.register(a)
        assert empty_registry.count == 1
        assert empty_registry.find("custom_action") is a

    def test_unregister(self, registry):
        a = registry.find("send_email")
        registry.unregister(a.action_id)
        assert registry.find_by_name("send_email") is None
        assert registry.count == 7  # seeded 8, removed 1

    def test_get_by_id(self, registry):
        a = registry.find("send_email")
        assert registry.get(a.action_id) is a

    def test_get_missing_raises(self, registry):
        with pytest.raises(UnknownActionError):
            registry.get("rwa_nonexistent")

    def test_list_by_provider(self, registry):
        gh_actions = registry.list_by_provider("github")
        assert all(a.provider == "github" for a in gh_actions)
        assert len(gh_actions) >= 1

    def test_list_by_risk(self, registry):
        critical = registry.list_by_risk(RISK_HIGH)
        assert all(a.risk_level == RISK_HIGH for a in critical)

    def test_list_by_type(self, registry):
        sends = registry.list_by_type(ACTION_SEND)
        assert len(sends) >= 4
        assert all(a.action_type == ACTION_SEND for a in sends)

    def test_list_enabled(self, registry):
        enabled = registry.list_enabled()
        assert len(enabled) == registry.count

    def test_enable_disable(self, registry):
        a = registry.find("send_email")
        registry.disable(a.action_id)
        assert a.enabled is False
        assert registry.find("send_email") not in registry.list_enabled()
        registry.enable(a.action_id)
        assert a.enabled is True

    def test_disable_missing_raises(self, registry):
        with pytest.raises(UnknownActionError):
            registry.disable("rwa_nonexistent")

    def test_provider_names(self, registry):
        providers = registry.provider_names()
        assert "gmail" in providers
        assert "github" in providers

    def test_action_names(self, registry):
        names = registry.action_names()
        assert "send_email" in names
        assert "git_push" in names

    def test_to_dict_from_dict_roundtrip(self, registry):
        d = registry.to_dict()
        r2 = ActionRegistry.from_dict(d)
        assert r2.count == registry.count
        assert r2.action_names() == registry.action_names()

    def test_empty_registry_count(self, empty_registry):
        assert empty_registry.count == 0
        assert empty_registry.enabled_count == 0
        assert empty_registry.provider_names() == []
