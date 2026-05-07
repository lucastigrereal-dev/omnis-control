"""Testes dos modelos ToolRegistry — P0.8."""
from __future__ import annotations

import pytest

from src.tool_registry.models import (
    ToolRecord,
    ToolStatus,
    ToolRiskLevel,
    ToolCategory,
    validate_tool_id,
)
from src.tool_registry.errors import (
    InvalidToolIdError,
    InvalidStatusError,
    InvalidCategoryError,
    SecretDetectedError,
)


class TestToolRecordValid:
    """ToolRecord valido — campos obrigatorios."""

    def test_valid_minimal_record(self):
        r = ToolRecord(
            tool_id="test_tool",
            name="Test Tool",
            category=ToolCategory.DEVELOPMENT,
            status=ToolStatus.READ_ONLY,
        )
        assert r.tool_id == "test_tool"
        assert r.name == "Test Tool"
        assert r.category == "development"
        assert r.status == "read_only"
        assert r.risk_level == ToolRiskLevel.LOW

    def test_all_optional_fields(self):
        r = ToolRecord(
            tool_id="full_tool",
            name="Full Tool",
            category=ToolCategory.PUBLISHING,
            status=ToolStatus.MANUAL,
            risk_level=ToolRiskLevel.HIGH,
            description="Desc",
            capabilities=["cap1", "cap2"],
            required_credentials=["META_APP_SECRET"],
            available_commands=["cmd1"],
            used_by_modules=["mod1"],
            used_by_skills=["skill1"],
            config_paths=["config/x.yaml"],
            healthcheck="curl :8000",
            limitations=["Sem API"],
            next_action="Configurar OAuth",
            notes="Nota",
        )
        assert len(r.capabilities) == 2
        assert r.required_credentials == ["META_APP_SECRET"]
        assert r.next_action != ""

    def test_auto_timestamps(self):
        r = ToolRecord(tool_id="ts_test", name="TS", category=ToolCategory.LLM)
        assert r.created_at != ""
        assert r.updated_at != ""
        assert "T" in r.created_at


class TestToolIdValidation:
    """Validacao de tool_id — slug seguro."""

    def test_valid_slugs(self):
        for tid in ["test_tool", "my-tool", "abc123", "a_b-c", "docker"]:
            assert validate_tool_id(tid) == tid

    def test_invalid_short_id(self):
        with pytest.raises(InvalidToolIdError):
            validate_tool_id("ab")

    def test_invalid_uppercase(self):
        with pytest.raises(InvalidToolIdError):
            validate_tool_id("TestTool")

    def test_invalid_special_chars(self):
        with pytest.raises(InvalidToolIdError):
            validate_tool_id("test.tool")

    def test_invalid_empty(self):
        with pytest.raises(InvalidToolIdError):
            validate_tool_id("")

    def test_invalid_spaces(self):
        with pytest.raises(InvalidToolIdError):
            validate_tool_id("test tool")


class TestStatusValidation:
    """Validacao de status."""

    def test_invalid_status_fails(self):
        with pytest.raises(InvalidStatusError):
            ToolRecord(tool_id="xt1", name="X", category=ToolCategory.DEVELOPMENT, status="invalid")

    def test_all_valid_statuses(self):
        for st in ToolStatus.ALL:
            r = ToolRecord(tool_id="st_test", name="ST", category=ToolCategory.DEVELOPMENT, status=st)
            assert r.status == st


class TestCategoryValidation:
    """Validacao de categoria."""

    def test_invalid_category_fails(self):
        with pytest.raises(InvalidCategoryError):
            ToolRecord(tool_id="xt1", name="X", category="invalid_cat", status=ToolStatus.MANUAL)


class TestSecretDetection:
    """required_credentials nao aceita valor de secret real."""

    def test_facebook_token_like_blocked(self):
        with pytest.raises(SecretDetectedError):
            ToolRecord(
                tool_id="xt1", name="X", category=ToolCategory.DEVELOPMENT,
                required_credentials=["EAABwzLixnjYBO1234567890abcdefghijklmnop"],
            )

    def test_openai_key_like_blocked(self):
        with pytest.raises(SecretDetectedError):
            ToolRecord(
                tool_id="xt1", name="X", category=ToolCategory.LLM,
                required_credentials=["sk-1234567890abcdefghijklmnopqrstuv"],
            )

    def test_credential_names_allowed(self):
        r = ToolRecord(
            tool_id="xt1", name="X", category=ToolCategory.PUBLISHING,
            required_credentials=["META_APP_SECRET", "INSTAGRAM_ACCESS_TOKEN"],
        )
        assert len(r.required_credentials) == 2


class TestRiskValidation:
    """Validacao de risk_level."""

    def test_invalid_risk_fails(self):
        with pytest.raises(InvalidStatusError):
            ToolRecord(
                tool_id="xt1", name="X", category=ToolCategory.DEVELOPMENT,
                risk_level="catastrophic",
            )
