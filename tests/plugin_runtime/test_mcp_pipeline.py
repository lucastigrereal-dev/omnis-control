"""Tests for W155 — MCP Plugin E2E Pipeline."""
import pytest
from src.plugin_runtime.mcp_pipeline import McpPluginPipeline, McpPipelineResult


@pytest.fixture
def pipeline():
    return McpPluginPipeline()


def test_run_success(pipeline):
    result = pipeline.run("plugin_01", "read_file", declared_tools=["read_file"])
    assert isinstance(result, McpPipelineResult)
    assert result.success is True


def test_run_dry_run_default(pipeline):
    result = pipeline.run("plugin_01", "read_file")
    assert result.call_result.status == "dry_run"


def test_run_blocked_tool(pipeline):
    result = pipeline.run("plugin_01", "rm_rf")
    assert result.success is False


def test_run_creates_session(pipeline):
    result = pipeline.run("plugin_01", "read_file")
    assert result.session.plugin_id == "plugin_01"
    assert result.session.call_count == 1


def test_run_audit_pass(pipeline):
    result = pipeline.run("plugin_01", "read_file", declared_tools=["read_file"])
    assert result.audit.verdict == "pass"


def test_run_audit_fail_undeclared(pipeline):
    result = pipeline.run("plugin_01", "mystery_tool", declared_tools=["read_file"])
    assert result.audit.verdict == "fail"
    assert result.success is False


def test_run_to_dict(pipeline):
    result = pipeline.run("plugin_01", "read_file")
    d = result.to_dict()
    assert "session" in d
    assert "call_result" in d
    assert "audit" in d


def test_run_multiple_plugins(pipeline):
    r1 = pipeline.run("p1", "read_file", declared_tools=["read_file"])
    r2 = pipeline.run("p2", "list_dir", declared_tools=["list_dir"])
    assert r1.plugin_id == "p1"
    assert r2.plugin_id == "p2"
