import json
from pathlib import Path
from src.plugin_runtime.models import PluginManifest, PluginCapability


class ManifestReader:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._loaded: dict[str, PluginManifest] = {}

    def read_file(self, path: str) -> PluginManifest | None:
        file_path = Path(path)
        if not file_path.exists():
            return None
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return self.parse(data)

    def parse(self, data: dict) -> PluginManifest:
        caps = data.get("capabilities", data.get("tools", []))
        if isinstance(caps, list) and caps and isinstance(caps[0], dict):
            capabilities = [PluginCapability(
                name=c.get("name", ""),
                description=c.get("description", ""),
                permissions=c.get("permissions", []),
                tools=c.get("tools", []),
            ) for c in caps]
        else:
            capabilities = []

        manifest = PluginManifest(
            plugin_name=data.get("name", data.get("plugin_name", "")),
            display_name=data.get("display_name", data.get("title", "")),
            version=data.get("version", "0.1.0"),
            author=data.get("author", ""),
            description=data.get("description", ""),
            capabilities=capabilities,
            commands=data.get("commands", data.get("skills", [])),
            hooks=data.get("hooks", []),
            mcp_servers=data.get("mcp_servers", []),
            status="REGISTERED",
        )
        self._loaded[manifest.plugin_name] = manifest
        return manifest

    def get_manifest(self, plugin_name: str) -> PluginManifest | None:
        return self._loaded.get(plugin_name)

    @property
    def loaded_count(self) -> int:
        return len(self._loaded)
