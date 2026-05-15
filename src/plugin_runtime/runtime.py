from src.plugin_runtime.models import (
    PluginManifest, PluginCapability, PluginSettings, MCPDescriptor, PluginStatus,
)
from src.plugin_runtime.manifest_reader import ManifestReader
from src.plugin_runtime.permission_gate import PluginPermissionGate


class PluginRuntime:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.reader = ManifestReader(dry_run=dry_run)
        self.gate = PluginPermissionGate(dry_run=dry_run)
        self._plugins: dict[str, PluginManifest] = {}
        self._settings: dict[str, PluginSettings] = {}
        self._mcps: dict[str, MCPDescriptor] = {}
        self._events: list[dict] = []

    def discover(self, manifest_data: dict) -> dict:
        try:
            manifest = self.reader.parse(manifest_data)
        except Exception as e:
            return {"ok": False, "error": f"parse error: {e}"}

        ok, issues = self.gate.evaluate_manifest(manifest)
        if not ok:
            return {"ok": False, "error": "permission check failed", "issues": issues}

        self._plugins[manifest.plugin_name] = manifest
        self._events.append({"event": "PLUGIN_DISCOVERED", "plugin": manifest.plugin_name})
        return {"ok": True, "plugin_name": manifest.plugin_name, "status": "DISCOVERED"}

    def register_mcp(self, descriptor: MCPDescriptor) -> dict:
        self._mcps[descriptor.server_name] = descriptor
        return {"ok": True, "server_name": descriptor.server_name}

    def activate(self, plugin_name: str) -> dict:
        manifest = self._plugins.get(plugin_name)
        if manifest is None:
            return {"ok": False, "error": "plugin not found"}

        if not self.gate.can_activate(manifest):
            return {"ok": False, "error": "plugin blocked by permission gate"}

        manifest.status = "ACTIVATED"
        self._events.append({"event": "PLUGIN_ACTIVATED", "plugin": plugin_name})
        return {"ok": True, "plugin_name": plugin_name, "status": "ACTIVATED"}

    def deactivate(self, plugin_name: str) -> dict:
        manifest = self._plugins.get(plugin_name)
        if manifest is None:
            return {"ok": False, "error": "plugin not found"}
        manifest.status = "DISABLED"
        return {"ok": True, "plugin_name": plugin_name, "status": "DISABLED"}

    def get_plugin(self, plugin_name: str) -> PluginManifest | None:
        return self._plugins.get(plugin_name)

    def get_mcp(self, server_name: str) -> MCPDescriptor | None:
        return self._mcps.get(server_name)

    def list_plugins(self) -> list[dict]:
        return [m.to_dict() for m in self._plugins.values()]

    def list_mcps(self) -> list[dict]:
        return [m.to_dict() for m in self._mcps.values()]

    @property
    def plugin_count(self) -> int:
        return len(self._plugins)

    @property
    def mcp_count(self) -> int:
        return len(self._mcps)

    @property
    def event_count(self) -> int:
        return len(self._events)
