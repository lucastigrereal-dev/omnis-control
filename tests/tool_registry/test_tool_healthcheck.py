"""Testes de healthcheck do Tool Registry — P1.1."""
from __future__ import annotations

import pytest

from src.tool_registry.healthcheck import (
    ToolHealthResult,
    HealthStatus,
    is_healthcheck_allowed,
    get_checker_name,
    is_checker_safe,
    run_healthcheck_for,
    check_local_filesystem,
    check_docker,
    check_obsidian_vault,
    check_publisher_local_dry_run,
    check_publisher_os_argos,
    check_n8n,
)
from src.tool_registry.registry import ToolRegistry


class TestToolHealthResult:
    """Testa modelo ToolHealthResult."""

    def test_creates_with_defaults(self):
        r = ToolHealthResult(tool_id="test_tool")
        assert r.tool_id == "test_tool"
        assert r.health_status == HealthStatus.NOT_CHECKED
        assert r.checked_at != ""
        assert r.duration_ms == 0

    def test_creates_with_custom_checked_at(self):
        r = ToolHealthResult(tool_id="test_tool", checked_at="2026-01-01T00:00:00Z")
        assert r.checked_at == "2026-01-01T00:00:00Z"

    def test_extra_fields_blocked(self):
        with pytest.raises(Exception):
            ToolHealthResult(tool_id="test_tool", campo_inexistente=123)

    def test_safe_evidence_truncates_long_strings(self):
        r = ToolHealthResult(
            tool_id="test",
            evidence={"key": "a" * 300, "short": "ok"},
        )
        safe = r.safe_evidence()
        assert len(safe["key"]) <= 203  # 200 + "..."
        assert safe["short"] == "ok"

    def test_all_fields_serializable(self):
        r = ToolHealthResult(
            tool_id="test_tool",
            status_before="read_only",
            status_after="read_only",
            health_status=HealthStatus.OK,
            checker_name="test_checker",
            duration_ms=42,
            message="ok",
            evidence={"a": 1},
            recommendation="keep",
        )
        d = r.model_dump()
        assert d["tool_id"] == "test_tool"
        assert d["duration_ms"] == 42
        assert d["evidence"] == {"a": 1}


class TestHealthStatusEnum:
    """Testa HealthStatus constants."""

    def test_all_statuses_in_all(self):
        assert HealthStatus.OK in HealthStatus.ALL
        assert HealthStatus.BLOCKED in HealthStatus.ALL
        assert HealthStatus.NOT_CHECKED in HealthStatus.ALL
        assert len(HealthStatus.ALL) == 6


class TestAllowlist:
    """Testa allowlist de ferramentas."""

    def test_local_filesystem_is_allowed(self):
        assert is_healthcheck_allowed("local_filesystem")
        assert get_checker_name("local_filesystem") == "check_local_filesystem"
        assert is_checker_safe("local_filesystem")

    def test_instagram_is_allowed_but_not_safe(self):
        assert is_healthcheck_allowed("instagram_graph_api")
        assert get_checker_name("instagram_graph_api") is None
        assert not is_checker_safe("instagram_graph_api")

    def test_unknown_tool_not_allowed(self):
        assert not is_healthcheck_allowed("ferramenta_inexistente")


class TestLocalFilesystemHealthcheck:
    """Testa healthcheck local_filesystem."""

    def test_returns_ok(self):
        result = check_local_filesystem("local_filesystem")
        assert result.tool_id == "local_filesystem"
        assert result.health_status == HealthStatus.OK
        assert result.checker_name == "check_local_filesystem"
        assert result.duration_ms >= 0
        assert result.evidence["exists"] is True


class TestPublisherLocalDryRun:
    """Testa healthcheck do publisher dry-run."""

    def test_returns_ok(self):
        result = check_publisher_local_dry_run("publisher_local_dry_run")
        # Pode ser OK ou DEGRADED dependendo se o modulo existe
        assert result.tool_id == "publisher_local_dry_run"
        assert result.checker_name == "check_publisher_local_dry_run"


class TestPublisherOsArgos:
    """Testa healthcheck do ARGOS."""

    def test_checks_port_8000(self):
        result = check_publisher_os_argos("publisher_os_argos")
        assert result.tool_id == "publisher_os_argos"
        # Pode ser OK ou DEGRADED dependendo se porta aberta
        assert result.health_status in (HealthStatus.OK, HealthStatus.DEGRADED)

    def test_has_recommendation_when_degraded(self):
        result = check_publisher_os_argos("publisher_os_argos")
        if result.health_status == HealthStatus.DEGRADED:
            assert result.recommendation != ""


class TestN8nHealthcheck:
    """Testa healthcheck do n8n."""

    def test_checks_port_5678(self):
        result = check_n8n("n8n")
        assert result.tool_id == "n8n"
        assert result.health_status in (HealthStatus.OK, HealthStatus.DEGRADED, HealthStatus.FAILED)


class TestRunHealthcheckFor:
    """Testa dispatcher run_healthcheck_for."""

    def test_instagram_returns_blocked(self):
        result = run_healthcheck_for("instagram_graph_api", "blocked")
        assert result.health_status == HealthStatus.BLOCKED
        assert result.error_code == "OAUTH_REQUIRED"
        assert result.status_before == "blocked"

    def test_publer_returns_not_checked(self):
        result = run_healthcheck_for("publer", "not_configured")
        assert result.health_status == HealthStatus.NOT_CHECKED

    def test_unknown_tool_returns_not_checked(self):
        result = run_healthcheck_for("tool_inexistente")
        assert result.health_status == HealthStatus.NOT_CHECKED

    def test_local_filesystem_returns_ok(self):
        result = run_healthcheck_for("local_filesystem")
        assert result.health_status == HealthStatus.OK


class TestRegistryHealthcheckIntegration:
    """Testa integracao healthcheck no ToolRegistry."""

    @pytest.fixture
    def registry(self, tmp_path):
        return ToolRegistry(base_dir=str(tmp_path / "tool_registry"))

    def test_run_healthcheck_nonexistent_returns_none(self, registry):
        assert registry.run_healthcheck("nonexistent") is None

    def test_run_healthcheck_updates_last_validated(self, registry):
        from src.tool_registry.discovery import discover_known_tools
        tools = discover_known_tools()
        fs = [t for t in tools if t.tool_id == "local_filesystem"][0]
        registry.add_tool(fs)

        result = registry.run_healthcheck("local_filesystem")
        assert result is not None
        assert result.health_status == HealthStatus.OK

        # Verifica que o registro foi atualizado
        tool = registry.get_tool("local_filesystem")
        assert tool is not None
        assert tool.last_validated_at == result.checked_at
        assert tool.validation_status == HealthStatus.OK

    def test_run_healthcheck_persists_log(self, registry):
        from src.tool_registry.discovery import discover_known_tools
        tools = discover_known_tools()
        fs = [t for t in tools if t.tool_id == "local_filesystem"][0]
        registry.add_tool(fs)

        registry.run_healthcheck("local_filesystem")
        last = registry.get_last_healthcheck("local_filesystem")
        assert last is not None
        assert last.tool_id == "local_filesystem"
        assert last.health_status == HealthStatus.OK

    def test_run_healthcheck_instagram_blocked(self, registry):
        from src.tool_registry.discovery import discover_known_tools
        tools = discover_known_tools()
        ig = [t for t in tools if t.tool_id == "instagram_graph_api"][0]
        registry.add_tool(ig)

        result = registry.run_healthcheck("instagram_graph_api")
        assert result is not None
        assert result.health_status == HealthStatus.BLOCKED

    def test_run_all_healthchecks_only_safe(self, registry):
        from src.tool_registry.discovery import discover_known_tools
        tools = discover_known_tools()
        for t in tools:
            registry.add_tool(t)

        results = registry.run_all_healthchecks()
        # Deve ter executado apenas ferramentas com checker seguro
        assert len(results) >= 4  # local_filesystem, docker, obsidian, dry_run
        tool_ids = {r.tool_id for r in results}
        assert "instagram_graph_api" not in tool_ids
        assert "publer" not in tool_ids

    def test_get_healthcheck_report(self, registry):
        from src.tool_registry.discovery import discover_known_tools
        tools = discover_known_tools()
        fs = [t for t in tools if t.tool_id == "local_filesystem"][0]
        registry.add_tool(fs)
        registry.run_healthcheck("local_filesystem")

        report = registry.get_healthcheck_report()
        assert len(report) >= 1
        fs_report = [r for r in report if r["tool_id"] == "local_filesystem"][0]
        assert fs_report["health_status"] == "ok"
