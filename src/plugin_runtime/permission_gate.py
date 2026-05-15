from src.plugin_runtime.models import PluginManifest, PluginCapability, PluginPermission


FORBIDDEN_PERMISSIONS = {PluginPermission.SECRETS, PluginPermission.SHELL}
DANGEROUS_PERMISSIONS = {PluginPermission.WRITE, PluginPermission.EXECUTE, PluginPermission.NETWORK}


class PluginPermissionGate:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._allowlist: dict[str, set[str]] = {}
        self._blocked_plugins: set[str] = set()

    def evaluate_manifest(self, manifest: PluginManifest) -> tuple[bool, list[str]]:
        issues: list[str] = []

        for cap in manifest.capabilities:
            for perm_str in cap.permissions:
                try:
                    perm = PluginPermission(perm_str)
                except ValueError:
                    issues.append(f"unknown permission: {perm_str}")
                    continue

                if perm in FORBIDDEN_PERMISSIONS:
                    issues.append(f"forbidden permission: {perm.value} (capability: {cap.name})")

        ok = len(issues) == 0
        return ok, issues

    def can_activate(self, manifest: PluginManifest) -> bool:
        ok, _ = self.evaluate_manifest(manifest)
        if not ok:
            return False
        if manifest.plugin_name in self._blocked_plugins:
            return False
        return True

    def allow_permission(self, plugin_name: str, permission: str) -> None:
        self._allowlist.setdefault(plugin_name, set()).add(permission)

    def has_permission(self, plugin_name: str, permission: str) -> bool:
        allowed = self._allowlist.get(plugin_name, set())
        return permission in allowed

    def block_plugin(self, plugin_name: str) -> None:
        self._blocked_plugins.add(plugin_name)

    def unblock_plugin(self, plugin_name: str) -> bool:
        if plugin_name in self._blocked_plugins:
            self._blocked_plugins.discard(plugin_name)
            return True
        return False

    @property
    def blocked_count(self) -> int:
        return len(self._blocked_plugins)
