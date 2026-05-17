"""W154 — MCP Permission Auditor (audits MCP call history vs declared permissions)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import _new_id, _now_iso
from .mcp_bridge import McpToolCall


AUDIT_PASS = "pass"
AUDIT_WARN = "warn"
AUDIT_FAIL = "fail"


@dataclass
class AuditFinding:
    finding_id: str
    severity: str
    message: str
    plugin_id: str
    tool_name: str
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "severity": self.severity,
            "message": self.message,
            "plugin_id": self.plugin_id,
            "tool_name": self.tool_name,
            "created_at": self.created_at,
        }


@dataclass
class AuditReport:
    report_id: str
    plugin_id: str
    verdict: str
    findings: list[AuditFinding] = field(default_factory=list)
    calls_reviewed: int = 0
    audited_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "plugin_id": self.plugin_id,
            "verdict": self.verdict,
            "findings": [f.to_dict() for f in self.findings],
            "calls_reviewed": self.calls_reviewed,
            "audited_at": self.audited_at,
        }


class McpPermissionAuditor:
    """Audits MCP tool call history against declared plugin permissions."""

    HIGH_RISK_TOOLS = {"shell_exec", "rm_rf", "drop_db", "force_push", "write_secret"}
    MEDIUM_RISK_TOOLS = {"write_file", "delete_file", "send_email", "post_to_slack"}

    def __init__(self) -> None:
        self._call_log: list[McpToolCall] = []

    def record(self, call: McpToolCall) -> None:
        self._call_log.append(call)

    def audit_plugin(self, plugin_id: str, declared_tools: Optional[list[str]] = None) -> AuditReport:
        plugin_calls = [c for c in self._call_log if c.plugin_id == plugin_id]
        findings: list[AuditFinding] = []

        for call in plugin_calls:
            if call.tool_name in self.HIGH_RISK_TOOLS:
                findings.append(AuditFinding(
                    finding_id=_new_id("find"),
                    severity="FAIL",
                    message=f"High-risk tool called: '{call.tool_name}'",
                    plugin_id=plugin_id,
                    tool_name=call.tool_name,
                ))
            elif call.tool_name in self.MEDIUM_RISK_TOOLS:
                findings.append(AuditFinding(
                    finding_id=_new_id("find"),
                    severity="WARN",
                    message=f"Medium-risk tool called: '{call.tool_name}'",
                    plugin_id=plugin_id,
                    tool_name=call.tool_name,
                ))

            if declared_tools is not None and call.tool_name not in declared_tools:
                findings.append(AuditFinding(
                    finding_id=_new_id("find"),
                    severity="FAIL",
                    message=f"Undeclared tool called: '{call.tool_name}'",
                    plugin_id=plugin_id,
                    tool_name=call.tool_name,
                ))

        has_fail = any(f.severity == "FAIL" for f in findings)
        has_warn = any(f.severity == "WARN" for f in findings)
        verdict = AUDIT_FAIL if has_fail else (AUDIT_WARN if has_warn else AUDIT_PASS)

        return AuditReport(
            report_id=_new_id("audit"),
            plugin_id=plugin_id,
            verdict=verdict,
            findings=findings,
            calls_reviewed=len(plugin_calls),
        )
