from src.plugin_runtime.models import MCPDescriptor
from src.plugin_runtime.runtime import PluginRuntime


class TestPluginRuntime:
    def test_discover_safe_plugin(self):
        rt = PluginRuntime(dry_run=True)
        result = rt.discover({"name": "safe-plugin", "capabilities": [{"name": "r", "permissions": ["READ"]}]})
        assert result["ok"] is True
        assert result["plugin_name"] == "safe-plugin"

    def test_discover_forbidden_plugin(self):
        rt = PluginRuntime(dry_run=True)
        result = rt.discover({"name": "evil", "capabilities": [{"name": "s", "permissions": ["SECRETS"]}]})
        assert result["ok"] is False
        assert "permission check failed" in result["error"]

    def test_activate_discovered_plugin(self):
        rt = PluginRuntime(dry_run=True)
        rt.discover({"name": "p1"})
        result = rt.activate("p1")
        assert result["ok"] is True
        assert result["status"] == "ACTIVATED"

    def test_activate_blocked_plugin(self):
        rt = PluginRuntime(dry_run=True)
        rt.gate.block_plugin("evil")
        rt.discover({"name": "evil"})
        result = rt.activate("evil")
        assert result["ok"] is False

    def test_activate_not_found(self):
        rt = PluginRuntime(dry_run=True)
        result = rt.activate("ghost")
        assert result["ok"] is False

    def test_deactivate(self):
        rt = PluginRuntime(dry_run=True)
        rt.discover({"name": "p1"})
        rt.activate("p1")
        result = rt.deactivate("p1")
        assert result["ok"] is True
        assert result["status"] == "DISABLED"

    def test_register_mcp(self):
        rt = PluginRuntime(dry_run=True)
        desc = MCPDescriptor(server_name="memory", command="python", tools=["search"])
        result = rt.register_mcp(desc)
        assert result["ok"] is True
        assert rt.mcp_count == 1

    def test_get_plugin(self):
        rt = PluginRuntime(dry_run=True)
        rt.discover({"name": "p1"})
        assert rt.get_plugin("p1") is not None
        assert rt.get_plugin("ghost") is None

    def test_get_mcp(self):
        rt = PluginRuntime(dry_run=True)
        rt.register_mcp(MCPDescriptor(server_name="m1"))
        assert rt.get_mcp("m1") is not None
        assert rt.get_mcp("m2") is None

    def test_list_plugins(self):
        rt = PluginRuntime(dry_run=True)
        rt.discover({"name": "a"})
        rt.discover({"name": "b"})
        assert len(rt.list_plugins()) == 2

    def test_list_mcps(self):
        rt = PluginRuntime(dry_run=True)
        rt.register_mcp(MCPDescriptor(server_name="a"))
        rt.register_mcp(MCPDescriptor(server_name="b"))
        assert len(rt.list_mcps()) == 2

    def test_events_tracked(self):
        rt = PluginRuntime(dry_run=True)
        rt.discover({"name": "p1"})
        rt.activate("p1")
        assert rt.event_count == 2
