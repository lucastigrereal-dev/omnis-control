"""Tests for W154 — MCP Permission Auditor."""
import pytest
from src.plugin_runtime.mcp_permission_auditor import McpPermissionAuditor, AUDIT_PASS, AUDIT_WARN, AUDIT_FAIL
from src.plugin_runtime.mcp_bridge import McpToolCall


@pytest.fixture
def auditor():
    return McpPermissionAuditor()


def test_audit_clean_plugin(auditor):
    call = McpToolCall.new("read_file", "plugin_01")
    auditor.record(call)
    report = auditor.audit_plugin("plugin_01", declared_tools=["read_file"])
    assert report.verdict == AUDIT_PASS


def test_audit_high_risk_tool_fails(auditor):
    call = McpToolCall.new("rm_rf", "plugin_01")
    auditor.record(call)
    report = auditor.audit_plugin("plugin_01")
    assert report.verdict == AUDIT_FAIL


def test_audit_medium_risk_warns(auditor):
    call = McpToolCall.new("write_file", "plugin_01")
    auditor.record(call)
    report = auditor.audit_plugin("plugin_01")
    assert report.verdict == AUDIT_WARN


def test_audit_undeclared_tool_fails(auditor):
    call = McpToolCall.new("mystery_tool", "plugin_01")
    auditor.record(call)
    report = auditor.audit_plugin("plugin_01", declared_tools=["read_file"])
    assert report.verdict == AUDIT_FAIL
    assert any("Undeclared" in f.message for f in report.findings)


def test_audit_empty_plugin(auditor):
    report = auditor.audit_plugin("unknown_plugin")
    assert report.verdict == AUDIT_PASS
    assert report.calls_reviewed == 0


def test_audit_calls_reviewed_count(auditor):
    for _ in range(3):
        auditor.record(McpToolCall.new("read_file", "p1"))
    report = auditor.audit_plugin("p1", declared_tools=["read_file"])
    assert report.calls_reviewed == 3


def test_audit_isolates_plugins(auditor):
    auditor.record(McpToolCall.new("rm_rf", "p1"))
    auditor.record(McpToolCall.new("read_file", "p2"))
    r1 = auditor.audit_plugin("p1")
    r2 = auditor.audit_plugin("p2")
    assert r1.verdict == AUDIT_FAIL
    assert r2.verdict == AUDIT_PASS


def test_to_dict(auditor):
    call = McpToolCall.new("read_file", "p1")
    auditor.record(call)
    report = auditor.audit_plugin("p1", declared_tools=["read_file"])
    d = report.to_dict()
    assert "verdict" in d
    assert "findings" in d
