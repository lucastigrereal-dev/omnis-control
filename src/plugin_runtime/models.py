from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


class PluginStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    REGISTERED = "REGISTERED"
    ACTIVATED = "ACTIVATED"
    DISABLED = "DISABLED"
    ERROR = "ERROR"
    UNINSTALLED = "UNINSTALLED"


class PluginPermission(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    NETWORK = "NETWORK"
    SECRETS = "SECRETS"
    SHELL = "SHELL"


@dataclass
class PluginCapability:
    capability_id: str = field(default_factory=lambda: _new_id("pcap_"))
    name: str = ""
    description: str = ""
    version: str = "0.1.0"
    permissions: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    requires_approval: bool = False
    metadata: dict = field(default_factory=dict)

    def has_permission(self, perm: str) -> bool:
        return perm in self.permissions

    def to_dict(self) -> dict:
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "permissions": self.permissions,
            "tools": self.tools,
            "resources": self.resources,
            "requires_approval": self.requires_approval,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PluginCapability":
        return cls(
            capability_id=data.get("capability_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "0.1.0"),
            permissions=data.get("permissions", []),
            tools=data.get("tools", []),
            resources=data.get("resources", []),
            requires_approval=data.get("requires_approval", False),
            metadata=data.get("metadata", {}),
        )


@dataclass
class PluginManifest:
    manifest_id: str = field(default_factory=lambda: _new_id("pmf_"))
    plugin_name: str = ""
    display_name: str = ""
    version: str = "0.1.0"
    author: str = ""
    description: str = ""
    capabilities: list[PluginCapability] = field(default_factory=list)
    settings: list[str] = field(default_factory=list)
    mcp_servers: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)
    status: str = "DISCOVERED"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "manifest_id": self.manifest_id,
            "plugin_name": self.plugin_name,
            "display_name": self.display_name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "capabilities": [c.to_dict() for c in self.capabilities],
            "settings": self.settings,
            "mcp_servers": self.mcp_servers,
            "commands": self.commands,
            "hooks": self.hooks,
            "status": self.status,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PluginManifest":
        return cls(
            manifest_id=data.get("manifest_id", ""),
            plugin_name=data.get("plugin_name", ""),
            display_name=data.get("display_name", ""),
            version=data.get("version", "0.1.0"),
            author=data.get("author", ""),
            description=data.get("description", ""),
            capabilities=[PluginCapability.from_dict(c) for c in data.get("capabilities", [])],
            settings=data.get("settings", []),
            mcp_servers=data.get("mcp_servers", []),
            commands=data.get("commands", []),
            hooks=data.get("hooks", []),
            status=data.get("status", "DISCOVERED"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class PluginSettings:
    settings_id: str = field(default_factory=lambda: _new_id("ps_"))
    plugin_name: str = ""
    values: dict = field(default_factory=dict)
    secrets_refs: list[str] = field(default_factory=list)
    dry_run: bool = True
    metadata: dict = field(default_factory=dict)

    def get(self, key: str, default: str = "") -> str:
        return self.values.get(key, default)

    def set(self, key: str, value: str) -> None:
        self.values[key] = value

    def to_dict(self) -> dict:
        return {
            "settings_id": self.settings_id,
            "plugin_name": self.plugin_name,
            "values": self.values,
            "secrets_refs": self.secrets_refs,
            "dry_run": self.dry_run,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PluginSettings":
        return cls(
            settings_id=data.get("settings_id", ""),
            plugin_name=data.get("plugin_name", ""),
            values=data.get("values", {}),
            secrets_refs=data.get("secrets_refs", []),
            dry_run=data.get("dry_run", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MCPDescriptor:
    descriptor_id: str = field(default_factory=lambda: _new_id("mcpd_"))
    server_name: str = ""
    transport: str = "stdio"
    command: str = ""
    args: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    enabled: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "descriptor_id": self.descriptor_id,
            "server_name": self.server_name,
            "transport": self.transport,
            "command": self.command,
            "args": self.args,
            "env_vars": self.env_vars,
            "tools": self.tools,
            "resources": self.resources,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MCPDescriptor":
        return cls(
            descriptor_id=data.get("descriptor_id", ""),
            server_name=data.get("server_name", ""),
            transport=data.get("transport", "stdio"),
            command=data.get("command", ""),
            args=data.get("args", []),
            env_vars=data.get("env_vars", {}),
            tools=data.get("tools", []),
            resources=data.get("resources", []),
            enabled=data.get("enabled", False),
            metadata=data.get("metadata", {}),
        )
