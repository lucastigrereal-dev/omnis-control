from src.plugin_runtime.models import (
    PluginCapability,
    PluginManifest,
    PluginSettings,
    MCPDescriptor,
    PluginPermission,
)


class TestPluginCapability:
    def test_defaults(self):
        c = PluginCapability()
        assert c.capability_id.startswith("pcap_")
        assert c.version == "0.1.0"

    def test_has_permission(self):
        c = PluginCapability(permissions=["READ", "WRITE"])
        assert c.has_permission("READ") is True
        assert c.has_permission("EXECUTE") is False

    def test_tools_and_resources(self):
        c = PluginCapability(tools=["search", "index"], resources=["memory://docs"])
        assert len(c.tools) == 2
        assert "memory://docs" in c.resources

    def test_requires_approval(self):
        c = PluginCapability(requires_approval=True)
        assert c.requires_approval is True

    def test_roundtrip(self):
        c = PluginCapability(name="search", permissions=["READ"], tools=["find"])
        d = c.to_dict()
        c2 = PluginCapability.from_dict(d)
        assert c2.name == "search"
        assert c2.tools == ["find"]
        assert c2.permissions == ["READ"]


class TestPluginManifest:
    def test_defaults(self):
        m = PluginManifest()
        assert m.manifest_id.startswith("pmf_")
        assert m.status == "DISCOVERED"

    def test_plugin_with_capability(self):
        cap = PluginCapability(name="search", permissions=["READ"])
        m = PluginManifest(plugin_name="my-plugin", capabilities=[cap])
        assert len(m.capabilities) == 1
        assert m.capabilities[0].name == "search"

    def test_commands_and_hooks(self):
        m = PluginManifest(commands=["status", "briefing"], hooks=["pre-commit"])
        assert len(m.commands) == 2
        assert "pre-commit" in m.hooks

    def test_roundtrip(self):
        cap = PluginCapability(name="search", permissions=["READ"])
        m = PluginManifest(
            plugin_name="test-plugin", version="2.0.0",
            capabilities=[cap], commands=["cmd1"],
            status="REGISTERED",
        )
        d = m.to_dict()
        m2 = PluginManifest.from_dict(d)
        assert m2.plugin_name == "test-plugin"
        assert m2.version == "2.0.0"
        assert len(m2.capabilities) == 1
        assert m2.status == "REGISTERED"


class TestPluginSettings:
    def test_defaults(self):
        s = PluginSettings()
        assert s.settings_id.startswith("ps_")
        assert s.dry_run is True

    def test_get_set(self):
        s = PluginSettings(values={"key": "val"})
        assert s.get("key") == "val"
        assert s.get("missing", "default") == "default"
        s.set("new_key", "new_val")
        assert s.get("new_key") == "new_val"

    def test_secrets_refs(self):
        s = PluginSettings(secrets_refs=["GITHUB_TOKEN", "NOTION_KEY"])
        assert len(s.secrets_refs) == 2

    def test_roundtrip(self):
        s = PluginSettings(plugin_name="p1", values={"a": "b"}, secrets_refs=["TOK"], dry_run=False)
        d = s.to_dict()
        s2 = PluginSettings.from_dict(d)
        assert s2.plugin_name == "p1"
        assert s2.get("a") == "b"
        assert s2.dry_run is False


class TestMCPDescriptor:
    def test_defaults(self):
        d = MCPDescriptor()
        assert d.descriptor_id.startswith("mcpd_")
        assert d.enabled is False
        assert d.transport == "stdio"

    def test_server_config(self):
        d = MCPDescriptor(
            server_name="memory-server", command="python", args=["-m", "memory_server"],
            tools=["search", "write"], enabled=True,
        )
        assert d.command == "python"
        assert len(d.args) == 2
        assert d.enabled is True

    def test_env_vars(self):
        d = MCPDescriptor(env_vars={"DB_HOST": "localhost", "DB_PORT": "5432"})
        assert d.env_vars["DB_HOST"] == "localhost"

    def test_roundtrip(self):
        d = MCPDescriptor(
            server_name="s", transport="sse", command="npx",
            args=["-y", "server"], tools=["t1"], enabled=True,
        )
        data = d.to_dict()
        d2 = MCPDescriptor.from_dict(data)
        assert d2.server_name == "s"
        assert d2.transport == "sse"
        assert d2.tools == ["t1"]
        assert d2.enabled is True
