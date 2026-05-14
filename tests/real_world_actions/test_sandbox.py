"""Tests for P27 ActionSandbox."""
import pytest

from src.real_world_actions.sandbox import ActionSandbox
from src.real_world_actions.registry import ActionRegistry
from src.real_world_actions.models import (
    ActionDefinition, STATUS_BLOCKED, STATUS_DRY_RUN,
    ACTION_READ, ACTION_SEND, ACTION_DEPLOY,
)


class TestActionSandbox:
    @pytest.fixture
    def registry(self):
        r = ActionRegistry()
        r.seed_defaults()
        return r

    @pytest.fixture
    def sandbox(self, registry):
        return ActionSandbox(registry)

    def test_validate_no_schema_returns_empty(self, sandbox):
        a = ActionDefinition.new("test", "mock", ACTION_READ)
        assert sandbox.validate(a, {"anything": "goes"}) == []

    def test_validate_missing_required_field(self, sandbox):
        a = ActionDefinition.new("test", "mock", ACTION_READ,
                                 input_schema={"required": ["to"], "properties": {"to": {"type": "string"}}})
        errors = sandbox.validate(a, {})
        assert len(errors) >= 1
        assert any("to" in e for e in errors)

    def test_validate_type_mismatch(self, sandbox):
        a = ActionDefinition.new("test", "mock", ACTION_READ,
                                 input_schema={"properties": {"count": {"type": "number"}}})
        errors = sandbox.validate(a, {"count": "not-a-number"})
        assert len(errors) >= 1

    def test_validate_valid_params(self, sandbox):
        a = ActionDefinition.new("test", "mock", ACTION_READ,
                                 input_schema={"required": ["to"], "properties": {"to": {"type": "string"}}})
        assert sandbox.validate(a, {"to": "hello"}) == []

    def test_is_allowed_enabled(self, sandbox):
        a = ActionDefinition.new("test", "mock", ACTION_READ)
        assert sandbox.is_allowed(a) is True

    def test_is_allowed_disabled(self, sandbox):
        a = ActionDefinition.new("test", "mock", ACTION_READ)
        a.enabled = False
        assert sandbox.is_allowed(a) is False

    def test_preflight_known_action(self, sandbox):
        result = sandbox.preflight("send_email", {"to": "a@b.com"})
        assert result.status == STATUS_DRY_RUN
        assert result.output["action"] == "send_email"
        assert "would_execute" in result.output
        assert "requires_approval" in result.output
        assert "risk_level" in result.output

    def test_preflight_unknown_action_raises(self, sandbox):
        with pytest.raises(Exception):
            sandbox.preflight("nonexistent", {})

    def test_preflight_disabled_action(self, sandbox, registry):
        a = registry.find("send_email")
        a.enabled = False
        result = sandbox.preflight("send_email", {})
        assert result.status == STATUS_BLOCKED

    def test_check_rate_delegates(self, sandbox):
        a = sandbox.registry.find("health_check")
        assert sandbox.check_rate(a) is True

    def test_preview_shows_full_info(self, sandbox):
        a = sandbox.registry.find("git_push")
        preview = sandbox.preview(a, {"branch": "main"})
        assert preview["action"] == "git_push"
        assert preview["provider"] == "github"
        assert preview["risk_level"] == "critical"
        assert preview["requires_approval"] is True
        assert "validation_errors" in preview
        assert "would_execute" in preview

    def test_preview_with_validation_errors(self, sandbox):
        a = ActionDefinition.new("test", "mock", ACTION_READ,
                                 input_schema={"required": ["name"], "properties": {"name": {"type": "string"}}})
        preview = sandbox.preview(a, {})
        assert len(preview["validation_errors"]) >= 1
        assert preview["would_execute"] is False

    def test_validate_boolean_type(self, sandbox):
        a = ActionDefinition.new("test", "mock", ACTION_READ,
                                 input_schema={"properties": {"flag": {"type": "boolean"}}})
        assert sandbox.validate(a, {"flag": "not-bool"}) != []
        assert sandbox.validate(a, {"flag": True}) == []

    def test_validate_none_required(self, sandbox):
        a = ActionDefinition.new("test", "mock", ACTION_READ,
                                 input_schema={"required": ["x"], "properties": {"x": {"type": "string"}}})
        errors = sandbox.validate(a, {"x": None})
        assert len(errors) >= 1
