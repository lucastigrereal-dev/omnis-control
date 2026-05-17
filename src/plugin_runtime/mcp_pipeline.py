"""W155 — MCP Plugin E2E Pipeline (session → call → audit)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import PluginCapability, _new_id, _now_iso
from .mcp_bridge import McpPluginBridge, McpToolCall, McpCallResult
from .mcp_session import McpSessionManager, McpSession
from .mcp_tool_registry import McpToolRegistry, McpToolDefinition
from .mcp_permission_auditor import McpPermissionAuditor, AuditReport


@dataclass
class McpPipelineResult:
    run_id: str
    plugin_id: str
    session: McpSession
    call_result: McpCallResult
    audit: AuditReport
    success: bool
    error: str = ""
    ran_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "plugin_id": self.plugin_id,
            "session": self.session.to_dict(),
            "call_result": self.call_result.to_dict(),
            "audit": self.audit.to_dict(),
            "success": self.success,
            "error": self.error,
            "ran_at": self.ran_at,
        }


class McpPluginPipeline:
    """Orchestrates: open session → call tool → record → audit."""

    def __init__(self) -> None:
        self._sessions = McpSessionManager()
        self._bridge = McpPluginBridge()
        self._registry = McpToolRegistry()
        self._auditor = McpPermissionAuditor()

    def run(
        self,
        plugin_id: str,
        tool_name: str,
        arguments: Optional[dict] = None,
        declared_tools: Optional[list[str]] = None,
        dry_run: bool = True,
    ) -> McpPipelineResult:
        run_id = _new_id("mcp_pipe")
        session = self._sessions.open(plugin_id)

        call = McpToolCall.new(tool_name, plugin_id, arguments=arguments, dry_run=dry_run)
        call_result = self._bridge.call_tool(call)

        self._sessions.record_call(session.session_id)
        self._auditor.record(call)

        audit = self._auditor.audit_plugin(plugin_id, declared_tools=declared_tools)
        success = call_result.status != "denied" and audit.verdict != "fail"

        return McpPipelineResult(
            run_id=run_id,
            plugin_id=plugin_id,
            session=session,
            call_result=call_result,
            audit=audit,
            success=success,
        )
