from src.plugin_runtime.models import PluginManifest, PluginCapability
from src.plugin_runtime.permission_gate import PluginPermissionGate


class TestPluginPermissionGate:
    def test_evaluate_safe_manifest(self):
        gate = PluginPermissionGate()
        manifest = PluginManifest(
            plugin_name="safe",
            capabilities=[PluginCapability(name="readonly", permissions=["READ"])],
        )
        ok, issues = gate.evaluate_manifest(manifest)
        assert ok is True
        assert len(issues) == 0

    def test_evaluate_forbidden_secrets(self):
        gate = PluginPermissionGate()
        manifest = PluginManifest(
            plugin_name="dangerous",
            capabilities=[PluginCapability(name="access", permissions=["SECRETS"])],
        )
        ok, issues = gate.evaluate_manifest(manifest)
        assert ok is False
        assert any("forbidden" in i for i in issues)

    def test_evaluate_forbidden_shell(self):
        gate = PluginPermissionGate()
        manifest = PluginManifest(
            plugin_name="shell-plugin",
            capabilities=[PluginCapability(name="exec", permissions=["SHELL"])],
        )
        ok, _ = gate.evaluate_manifest(manifest)
        assert ok is False

    def test_evaluate_unknown_permission(self):
        gate = PluginPermissionGate()
        manifest = PluginManifest(
            plugin_name="unknown",
            capabilities=[PluginCapability(name="x", permissions=["INVALID"])],
        )
        ok, issues = gate.evaluate_manifest(manifest)
        assert ok is False
        assert any("unknown" in i for i in issues)

    def test_can_activate_safe(self):
        gate = PluginPermissionGate()
        manifest = PluginManifest(plugin_name="safe")
        assert gate.can_activate(manifest) is True

    def test_can_activate_blocked(self):
        gate = PluginPermissionGate()
        gate.block_plugin("evil")
        manifest = PluginManifest(plugin_name="evil")
        assert gate.can_activate(manifest) is False

    def test_allow_permission(self):
        gate = PluginPermissionGate()
        gate.allow_permission("p1", "WRITE")
        assert gate.has_permission("p1", "WRITE") is True
        assert gate.has_permission("p1", "EXECUTE") is False

    def test_unblock_plugin(self):
        gate = PluginPermissionGate()
        gate.block_plugin("p1")
        assert gate.unblock_plugin("p1") is True
        assert gate.unblock_plugin("nonexistent") is False
        assert gate.blocked_count == 0
