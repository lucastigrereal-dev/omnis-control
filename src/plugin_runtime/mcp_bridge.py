"""W151 — MCP Plugin Bridge (dry-run, mock-first)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import _new_id, _now_iso, PluginCapability


MCP_TOOL_CALL = "tool_call"
MCP_RESOURCE_READ = "resource_read"
MCP_PROMPT = "prompt"

MCP_STATUS_OK = "ok"
MCP_STATUS_DENIED = "denied"
MCP_STATUS_DRY_RUN = "dry_run"
MCP_STATUS_ERROR = "error"


@dataclass
class McpToolCall:
    call_id: str
    tool_name: str
    plugin_id: str
    arguments: dict = field(default_factory=dict)
    dry_run: bool = True
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, tool_name: str, plugin_id: str, arguments: Optional[dict] = None, dry_run: bool = True) -> "McpToolCall":
        return cls(
            call_id=_new_id("mcp_call"),
            tool_name=tool_name,
            plugin_id=plugin_id,
            arguments=arguments or {},
            dry_run=dry_run,
        )

    def to_dict(self) -> dict:
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "plugin_id": self.plugin_id,
            "arguments": self.arguments,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }


@dataclass
class McpCallResult:
    result_id: str
    call_id: str
    status: str
    output: dict = field(default_factory=dict)
    error: str = ""
    completed_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "call_id": self.call_id,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "completed_at": self.completed_at,
        }


class McpPluginBridge:
    """Routes tool calls from OMNIS to MCP-registered plugins (mock-first)."""

    BLOCKED_TOOLS = {"shell_exec", "rm_rf", "force_push", "drop_db"}

    def __init__(self) -> None:
        self._registered: dict[str, PluginCapability] = {}

    def register_capability(self, capability: PluginCapability) -> None:
        self._registered[capability.capability_id] = capability

    def call_tool(self, call: McpToolCall) -> McpCallResult:
        if call.tool_name in self.BLOCKED_TOOLS:
            return McpCallResult(
                result_id=_new_id("mcp_res"),
                call_id=call.call_id,
                status=MCP_STATUS_DENIED,
                error=f"Tool '{call.tool_name}' is blocked by OMNIS safety policy",
            )

        if call.dry_run:
            return McpCallResult(
                result_id=_new_id("mcp_res"),
                call_id=call.call_id,
                status=MCP_STATUS_DRY_RUN,
                output={"simulated": True, "tool": call.tool_name, "args": call.arguments},
            )

        return McpCallResult(
            result_id=_new_id("mcp_res"),
            call_id=call.call_id,
            status=MCP_STATUS_OK,
            output={"tool": call.tool_name, "result": "mock_ok"},
        )

    def list_tools(self) -> list[str]:
        tools: list[str] = []
        for cap in self._registered.values():
            tools.extend(cap.tools)
        return tools
