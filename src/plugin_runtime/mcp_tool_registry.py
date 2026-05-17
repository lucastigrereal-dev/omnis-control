"""W152 — MCP Tool Registry (in-memory catalog of registered tools)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .models import _new_id, _now_iso


@dataclass
class McpToolDefinition:
    tool_id: str
    name: str
    plugin_id: str
    description: str
    input_schema: dict = field(default_factory=dict)
    requires_permissions: list[str] = field(default_factory=list)
    registered_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, name: str, plugin_id: str, description: str = "", input_schema: Optional[dict] = None, permissions: Optional[list[str]] = None) -> "McpToolDefinition":
        return cls(
            tool_id=_new_id("tool"),
            name=name,
            plugin_id=plugin_id,
            description=description,
            input_schema=input_schema or {},
            requires_permissions=permissions or [],
        )

    def to_dict(self) -> dict:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "plugin_id": self.plugin_id,
            "description": self.description,
            "input_schema": self.input_schema,
            "requires_permissions": self.requires_permissions,
            "registered_at": self.registered_at,
        }


class McpToolRegistry:
    """In-memory registry of MCP tool definitions."""

    def __init__(self) -> None:
        self._tools: dict[str, McpToolDefinition] = {}

    def register(self, tool: McpToolDefinition) -> None:
        self._tools[tool.tool_id] = tool

    def get_by_id(self, tool_id: str) -> Optional[McpToolDefinition]:
        return self._tools.get(tool_id)

    def find_by_name(self, name: str) -> Optional[McpToolDefinition]:
        for t in self._tools.values():
            if t.name == name:
                return t
        return None

    def list_by_plugin(self, plugin_id: str) -> list[McpToolDefinition]:
        return [t for t in self._tools.values() if t.plugin_id == plugin_id]

    def list_all(self) -> list[McpToolDefinition]:
        return list(self._tools.values())

    def count(self) -> int:
        return len(self._tools)

    def unregister(self, tool_id: str) -> bool:
        if tool_id in self._tools:
            del self._tools[tool_id]
            return True
        return False
