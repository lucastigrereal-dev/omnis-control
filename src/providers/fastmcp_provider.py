"""FastMCPProvider — real MCP protocol via FastMCP.

Requires: pip install fastmcp
Falls back to LocalToolRegistryProvider when not installed.

Exposes OMNIS skills as MCP tools accessible to Claude and other LLMs.
"""
from __future__ import annotations

import os
from typing import Any, Optional

from src.providers.base import ProviderHealth, ProviderStatus
from src.providers.mcp import MCPProvider, ToolDefinition, ToolCallResult, LocalToolRegistryProvider


class FastMCPProvider(MCPProvider):
    """MCPProvider backed by FastMCP — real MCP protocol (stdio or HTTP).

    When available: tools are callable via standard MCP JSON-RPC.
    Falls back to LocalToolRegistryProvider when fastmcp not installed.
    """

    def __init__(
        self,
        server_name: str = "omnis",
        fallback: Optional[MCPProvider] = None,
    ) -> None:
        self._server_name = server_name
        self._fallback = fallback or LocalToolRegistryProvider()
        self._mcp: Any = None
        self._available = False
        self._registered_tools: dict[str, ToolDefinition] = {}
        self._init()

    def _init(self) -> None:
        try:
            import fastmcp  # type: ignore  # noqa: F401
            from fastmcp import FastMCP  # type: ignore
            self._mcp = FastMCP(self._server_name)
            self._available = True
        except ImportError:
            self._available = False

    @property
    def backend(self) -> str:
        return f"fastmcp({self._server_name})" if self._available else "local_registry(fastmcp_unavailable)"

    def health_check(self) -> ProviderHealth:
        if not self._available:
            return ProviderHealth(
                status=ProviderStatus.DEGRADED,
                provider_name=self.name,
                backend=self.backend,
                details={"reason": "fastmcp not installed", "fallback": "local_registry"},
            )
        return ProviderHealth(
            status=ProviderStatus.OK,
            provider_name=self.name,
            backend=self.backend,
            details={"server": self._server_name, "tools": len(self._registered_tools)},
        )

    def register_tool(self, tool: ToolDefinition, handler: Any) -> None:
        """Register a tool with its handler function."""
        self._registered_tools[tool.id] = tool
        self._fallback.register(tool)  # type: ignore[attr-defined]
        if self._available and self._mcp:
            # Wrap handler as FastMCP tool
            self._mcp.tool(name=tool.id, description=tool.description)(handler)

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._registered_tools.values()) or self._fallback.list_tools()

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        return self._registered_tools.get(tool_id) or self._fallback.get_tool(tool_id)

    def call_tool(
        self,
        tool_id: str,
        args: dict[str, Any],
        *,
        dry_run: bool = True,
    ) -> ToolCallResult:
        if not self._available or dry_run:
            return self._fallback.call_tool(tool_id, args, dry_run=dry_run)
        tool = self._registered_tools.get(tool_id)
        if not tool:
            return ToolCallResult(tool_id=tool_id, success=False, error=f"Tool '{tool_id}' not registered")
        return ToolCallResult(
            tool_id=tool_id,
            success=False,
            error="Direct tool call via FastMCP requires running the MCP server (use serve())",
        )

    def serve(self, transport: str = "stdio") -> None:
        """Start the FastMCP server. Blocks."""
        if not self._available:
            raise RuntimeError("fastmcp not installed. Run: pip install fastmcp")
        self._mcp.run(transport=transport)


def build_omnis_mcp_server(registry_provider: Optional[LocalToolRegistryProvider] = None) -> FastMCPProvider:
    """Build a FastMCPProvider pre-loaded with standard OMNIS tools.

    Exposes:
    - omnis_health: run health check
    - omnis_doctor: full doctor report
    - omnis_list_missions: list registered missions
    """
    from src.providers.mcp import ToolDefinition

    provider = FastMCPProvider(server_name="omnis-control")

    # Tool: health check
    health_tool = ToolDefinition(
        id="omnis_health",
        name="omnis_health",
        description="Run OMNIS health check. Returns status of all system components.",
        input_schema={"type": "object", "properties": {}, "required": []},
    )

    def _health_handler() -> dict[str, Any]:
        try:
            from src.omnis_health.server import build_health_report  # type: ignore
            report = build_health_report()
            return report.to_dict() if hasattr(report, "to_dict") else {"status": str(report)}
        except Exception as e:
            return {"error": str(e), "status": "error"}

    provider.register_tool(health_tool, _health_handler)

    # Tool: list missions
    missions_tool = ToolDefinition(
        id="omnis_list_missions",
        name="omnis_list_missions",
        description="List registered OMNIS missions with their status.",
        input_schema={
            "type": "object",
            "properties": {"status": {"type": "string", "description": "Filter by status"}},
            "required": [],
        },
    )

    def _missions_handler(status: Optional[str] = None) -> dict[str, Any]:
        try:
            from src.first_missions.orchestrator import MissionOrchestrator
            orch = MissionOrchestrator(dry_run=True)
            missions = orch.registry.query()
            return {"missions": [m.to_dict() for m in missions], "count": len(missions)}
        except Exception as e:
            return {"error": str(e), "missions": []}

    provider.register_tool(missions_tool, _missions_handler)

    return provider
