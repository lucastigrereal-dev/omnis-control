"""MCPProvider — Model Context Protocol abstraction for OMNIS.

Backends:
1. LocalToolRegistryProvider — built-in, reads from tool_registry JSONL (no deps)
2. FastMCPProvider           — stdio MCP server via FastMCP (optional)
3. RemoteMCPProvider         — HTTP MCP endpoint (optional)

OMNIS core only imports MCPProvider and ToolDefinition.
"""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

from src.providers.base import Provider, ProviderHealth, ProviderStatus


@dataclass
class ToolDefinition:
    """Standard MCP tool definition."""
    id: str
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCallResult:
    """Result of calling a tool via MCP."""
    tool_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    dry_run: bool = False


class MCPProvider(Provider):
    """Abstract MCP provider. Use registry.get('mcp') to get instance."""

    @property
    def name(self) -> str:
        return "mcp"

    @abstractmethod
    def list_tools(self) -> list[ToolDefinition]:
        """List all available tools."""

    @abstractmethod
    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        """Get a tool by id. Returns None if not found."""

    @abstractmethod
    def call_tool(
        self,
        tool_id: str,
        args: dict[str, Any],
        *,
        dry_run: bool = True,
    ) -> ToolCallResult:
        """Call a tool. dry_run=True simulates without executing."""


# ── Built-in fallback: LocalToolRegistryProvider ───────────────────────────

class LocalToolRegistryProvider(MCPProvider):
    """Reads tools from the existing tool_registry module.

    Bridges the existing JSONL-based tool_registry into the MCP provider pattern.
    Does NOT implement actual MCP protocol — use FastMCPProvider for real MCP.
    """

    def __init__(self, tools: Optional[list[ToolDefinition]] = None) -> None:
        self._tools: dict[str, ToolDefinition] = {t.id: t for t in (tools or [])}

    @property
    def backend(self) -> str:
        return "local_tool_registry"

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            status=ProviderStatus.OK,
            provider_name=self.name,
            backend=self.backend,
            details={"tools_count": len(self._tools)},
        )

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.id] = tool

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        return self._tools.get(tool_id)

    def call_tool(
        self,
        tool_id: str,
        args: dict[str, Any],
        *,
        dry_run: bool = True,
    ) -> ToolCallResult:
        tool = self._tools.get(tool_id)
        if not tool:
            return ToolCallResult(
                tool_id=tool_id,
                success=False,
                error=f"Tool '{tool_id}' not found in local registry",
            )
        if dry_run:
            return ToolCallResult(
                tool_id=tool_id,
                success=True,
                output={"dry_run": True, "tool": tool.name, "args": args},
                dry_run=True,
            )
        return ToolCallResult(
            tool_id=tool_id,
            success=False,
            error="LocalToolRegistryProvider does not execute tools — use FastMCPProvider",
        )
