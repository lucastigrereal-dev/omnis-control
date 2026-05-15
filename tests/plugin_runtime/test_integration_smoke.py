from src.plugin_runtime.models import MCPDescriptor
from src.plugin_runtime.runtime import PluginRuntime


class TestPluginRuntimeIntegrationSmoke:
    def test_full_discover_activate_deactivate(self):
        rt = PluginRuntime(dry_run=True)

        result = rt.discover({
            "name": "my-plugin",
            "version": "2.0.0",
            "capabilities": [
                {"name": "search", "permissions": ["READ"], "tools": ["find", "query"]},
            ],
            "commands": ["status", "briefing"],
        })
        assert result["ok"] is True
        assert rt.plugin_count == 1

        result = rt.activate("my-plugin")
        assert result["ok"] is True
        assert rt.get_plugin("my-plugin").status == "ACTIVATED"

        result = rt.deactivate("my-plugin")
        assert result["ok"] is True
        assert rt.get_plugin("my-plugin").status == "DISABLED"

    def test_secrets_plugin_always_blocked(self):
        rt = PluginRuntime(dry_run=True)
        result = rt.discover({
            "name": "stealer",
            "capabilities": [{"name": "env", "permissions": ["READ", "SECRETS"]}],
        })
        assert result["ok"] is False

    def test_mcp_registration_and_lookup(self):
        rt = PluginRuntime(dry_run=True)
        desc = MCPDescriptor(
            server_name="memory-server",
            transport="stdio",
            command="python",
            args=["-m", "memory"],
            tools=["search", "write", "delete"],
        )
        result = rt.register_mcp(desc)
        assert result["ok"] is True
        assert rt.mcp_count == 1

        found = rt.get_mcp("memory-server")
        assert found is not None
        assert found.tools == ["search", "write", "delete"]

    def test_multiple_plugins_independent(self):
        rt = PluginRuntime(dry_run=True)
        rt.discover({"name": "a", "capabilities": [{"name": "r", "permissions": ["READ"]}]})
        rt.discover({"name": "b", "capabilities": [{"name": "r", "permissions": ["READ"]}]})

        rt.activate("a")
        assert rt.get_plugin("a").status == "ACTIVATED"
        assert rt.get_plugin("b").status == "REGISTERED"

        rt.gate.block_plugin("b")
        result = rt.activate("b")
        assert result["ok"] is False

    def test_activation_events_timeline(self):
        rt = PluginRuntime(dry_run=True)
        rt.discover({"name": "p1"})
        rt.register_mcp(MCPDescriptor(server_name="m1"))
        rt.activate("p1")

        assert rt.event_count == 2  # DISCOVERED + ACTIVATED
