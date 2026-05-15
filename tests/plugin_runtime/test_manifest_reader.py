import json
import tempfile
from pathlib import Path

from src.plugin_runtime.manifest_reader import ManifestReader


class TestManifestReader:
    def test_parse_minimal(self):
        reader = ManifestReader()
        data = {"name": "test-plugin", "version": "1.0.0"}
        m = reader.parse(data)
        assert m.plugin_name == "test-plugin"
        assert m.version == "1.0.0"
        assert m.status == "REGISTERED"

    def test_parse_with_capabilities(self):
        reader = ManifestReader()
        data = {
            "name": "my-plugin",
            "capabilities": [{"name": "search", "permissions": ["READ"], "tools": ["find"]}],
        }
        m = reader.parse(data)
        assert len(m.capabilities) == 1
        assert m.capabilities[0].name == "search"
        assert m.capabilities[0].tools == ["find"]

    def test_parse_with_commands(self):
        reader = ManifestReader()
        data = {"name": "p", "commands": ["status", "briefing"]}
        m = reader.parse(data)
        assert m.commands == ["status", "briefing"]

    def test_read_file(self):
        reader = ManifestReader()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"name": "file-plugin", "description": "test"}, f)
            tmp_path = f.name

        try:
            m = reader.read_file(tmp_path)
            assert m is not None
            assert m.plugin_name == "file-plugin"
        finally:
            Path(tmp_path).unlink()

    def test_read_nonexistent(self):
        reader = ManifestReader()
        assert reader.read_file("/nonexistent/path.json") is None

    def test_get_manifest(self):
        reader = ManifestReader()
        reader.parse({"name": "p1"})
        assert reader.get_manifest("p1") is not None
        assert reader.get_manifest("unknown") is None

    def test_loaded_count(self):
        reader = ManifestReader()
        reader.parse({"name": "a"})
        reader.parse({"name": "b"})
        assert reader.loaded_count == 2
