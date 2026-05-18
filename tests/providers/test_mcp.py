"""Tests for MCPProvider — LocalToolRegistryProvider."""
import pytest
from src.providers.mcp import LocalToolRegistryProvider, ToolDefinition, ToolCallResult


def make_tool(id: str = "t1", name: str = "Tool 1") -> ToolDefinition:
    return ToolDefinition(id=id, name=name, description="A test tool")


class TestLocalToolRegistryProvider:
    def test_health_ok(self):
        assert LocalToolRegistryProvider().health_check().ok

    def test_register_and_list(self):
        p = LocalToolRegistryProvider()
        p.register(make_tool("t1"))
        tools = p.list_tools()
        assert len(tools) == 1
        assert tools[0].id == "t1"

    def test_get_existing(self):
        p = LocalToolRegistryProvider()
        t = make_tool("myid")
        p.register(t)
        assert p.get_tool("myid") is t

    def test_get_missing(self):
        p = LocalToolRegistryProvider()
        assert p.get_tool("missing") is None

    def test_call_dry_run(self):
        p = LocalToolRegistryProvider()
        p.register(make_tool("t1"))
        result = p.call_tool("t1", {"arg": 1}, dry_run=True)
        assert isinstance(result, ToolCallResult)
        assert result.success
        assert result.dry_run is True

    def test_call_missing_tool(self):
        p = LocalToolRegistryProvider()
        result = p.call_tool("missing", {}, dry_run=True)
        assert result.success is False
        assert result.error is not None

    def test_call_real_returns_error(self):
        p = LocalToolRegistryProvider()
        p.register(make_tool("t1"))
        result = p.call_tool("t1", {}, dry_run=False)
        assert result.success is False

    def test_init_with_tools(self):
        tools = [make_tool("a"), make_tool("b")]
        p = LocalToolRegistryProvider(tools=tools)
        assert len(p.list_tools()) == 2

    def test_backend(self):
        assert LocalToolRegistryProvider().backend == "local_tool_registry"

    def test_name(self):
        assert LocalToolRegistryProvider().name == "mcp"
