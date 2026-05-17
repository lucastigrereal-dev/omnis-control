"""Tests for W152 — MCP Tool Registry."""
import pytest
from src.plugin_runtime.mcp_tool_registry import McpToolRegistry, McpToolDefinition


@pytest.fixture
def registry():
    return McpToolRegistry()


@pytest.fixture
def tool():
    return McpToolDefinition.new("read_file", "plugin_01", "Read file content")


def test_register_and_count(registry, tool):
    registry.register(tool)
    assert registry.count() == 1


def test_get_by_id(registry, tool):
    registry.register(tool)
    found = registry.get_by_id(tool.tool_id)
    assert found is tool


def test_get_missing_returns_none(registry):
    assert registry.get_by_id("bad") is None


def test_find_by_name(registry, tool):
    registry.register(tool)
    found = registry.find_by_name("read_file")
    assert found is not None


def test_find_by_name_missing(registry):
    assert registry.find_by_name("nonexistent") is None


def test_list_by_plugin(registry):
    t1 = McpToolDefinition.new("tool1", "plugin_01")
    t2 = McpToolDefinition.new("tool2", "plugin_01")
    t3 = McpToolDefinition.new("tool3", "plugin_02")
    for t in [t1, t2, t3]:
        registry.register(t)
    results = registry.list_by_plugin("plugin_01")
    assert len(results) == 2


def test_list_all(registry, tool):
    registry.register(tool)
    assert len(registry.list_all()) == 1


def test_unregister(registry, tool):
    registry.register(tool)
    removed = registry.unregister(tool.tool_id)
    assert removed is True
    assert registry.count() == 0


def test_unregister_missing(registry):
    assert registry.unregister("bad") is False


def test_to_dict(tool):
    d = tool.to_dict()
    assert d["name"] == "read_file"
    assert "tool_id" in d
