"""Tests for FastMCPProvider — fallback behavior when not installed."""
import pytest
from src.providers.fastmcp_provider import FastMCPProvider, build_omnis_mcp_server
from src.providers.mcp import ToolDefinition, ToolCallResult
from src.providers.base import ProviderStatus


def make_tool(id: str = "t1") -> ToolDefinition:
    return ToolDefinition(id=id, name=id, description="Test tool")


class TestFastMCPProviderFallback:
    def test_health_degraded_or_ok(self):
        p = FastMCPProvider()
        h = p.health_check()
        assert h.status.value in ("ok", "degraded")

    def test_register_and_list(self):
        p = FastMCPProvider()
        p.register_tool(make_tool("t1"), lambda: {})
        tools = p.list_tools()
        assert any(t.id == "t1" for t in tools)

    def test_get_tool(self):
        p = FastMCPProvider()
        t = make_tool("myid")
        p.register_tool(t, lambda: {})
        assert p.get_tool("myid") is t

    def test_call_tool_dry_run(self):
        p = FastMCPProvider()
        p.register_tool(make_tool("t1"), lambda: {})
        result = p.call_tool("t1", {}, dry_run=True)
        assert isinstance(result, ToolCallResult)
        assert result.dry_run is True

    def test_call_missing_tool(self):
        p = FastMCPProvider()
        result = p.call_tool("missing", {}, dry_run=True)
        assert result.success is False

    def test_backend_indicates_state(self):
        p = FastMCPProvider()
        assert "fastmcp" in p.backend or "local_registry" in p.backend

    def test_name(self):
        assert FastMCPProvider().name == "mcp"

    def test_serve_raises_without_lib(self):
        p = FastMCPProvider()
        if not p._available:
            with pytest.raises(RuntimeError):
                p.serve()


class TestBuildOmnisMCPServer:
    def test_builds_provider(self):
        provider = build_omnis_mcp_server()
        assert isinstance(provider, FastMCPProvider)

    def test_has_health_tool(self):
        provider = build_omnis_mcp_server()
        tool = provider.get_tool("omnis_health")
        assert tool is not None
        assert "health" in tool.description.lower()

    def test_has_missions_tool(self):
        provider = build_omnis_mcp_server()
        tool = provider.get_tool("omnis_list_missions")
        assert tool is not None

    def test_health_tool_dry_run(self):
        provider = build_omnis_mcp_server()
        result = provider.call_tool("omnis_health", {}, dry_run=True)
        assert result.dry_run is True
