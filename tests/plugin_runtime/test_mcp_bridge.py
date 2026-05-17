"""Tests for W151 — MCP Plugin Bridge."""
import pytest
from src.plugin_runtime.mcp_bridge import (
    McpPluginBridge, McpToolCall, McpCallResult,
    MCP_STATUS_OK, MCP_STATUS_DENIED, MCP_STATUS_DRY_RUN,
)
from src.plugin_runtime.models import PluginCapability


@pytest.fixture
def bridge():
    return McpPluginBridge()


@pytest.fixture
def call():
    return McpToolCall.new("read_file", "plugin_abc", {"path": "/docs/readme.md"})


def test_call_new_creates_instance(call):
    assert isinstance(call, McpToolCall)
    assert call.tool_name == "read_file"


def test_call_dry_run_default(call):
    assert call.dry_run is True


def test_call_to_dict(call):
    d = call.to_dict()
    assert d["tool_name"] == "read_file"
    assert d["dry_run"] is True


def test_dry_run_returns_simulated(bridge, call):
    result = bridge.call_tool(call)
    assert result.status == MCP_STATUS_DRY_RUN
    assert result.output["simulated"] is True


def test_blocked_tool_denied(bridge):
    c = McpToolCall.new("rm_rf", "plugin_x")
    result = bridge.call_tool(c)
    assert result.status == MCP_STATUS_DENIED
    assert "blocked" in result.error


def test_blocked_tool_shell_exec(bridge):
    c = McpToolCall.new("shell_exec", "plugin_x", dry_run=False)
    result = bridge.call_tool(c)
    assert result.status == MCP_STATUS_DENIED


def test_non_dry_run_returns_ok(bridge):
    c = McpToolCall.new("read_file", "plugin_x", dry_run=False)
    result = bridge.call_tool(c)
    assert result.status == MCP_STATUS_OK


def test_result_to_dict(bridge, call):
    result = bridge.call_tool(call)
    d = result.to_dict()
    assert "status" in d
    assert "output" in d


def test_register_capability(bridge):
    cap = PluginCapability(name="reader", tools=["read_file", "list_dir"])
    bridge.register_capability(cap)
    assert "read_file" in bridge.list_tools()


def test_list_tools_empty(bridge):
    assert bridge.list_tools() == []


def test_multiple_calls(bridge):
    calls = [McpToolCall.new(f"tool_{i}", "p1") for i in range(5)]
    results = [bridge.call_tool(c) for c in calls]
    assert all(r.status == MCP_STATUS_DRY_RUN for r in results)
