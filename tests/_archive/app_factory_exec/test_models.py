"""Tests for App Factory Executable models."""

from src.app_factory_exec.models import AppSpec, AppType, GeneratedFile


class TestAppType:
    def test_types(self):
        assert AppType.API_BACKEND == "api_backend"
        assert AppType.FULLSTACK == "fullstack"
        assert AppType.CLI_TOOL == "cli_tool"


class TestAppSpec:
    def test_minimal(self):
        spec = AppSpec(
            app_name="my_api",
            app_type=AppType.API_BACKEND,
            description="Minimal API",
        )
        assert spec.app_name == "my_api"
        assert spec.port == 8000
        assert spec.database == "sqlite"

    def test_with_entities(self):
        spec = AppSpec(
            app_name="crm",
            app_type=AppType.FULLSTACK,
            description="CRM App",
            entities=["User", "Lead", "Deal"],
            endpoints=["/users", "/leads", "/deals"],
        )
        assert len(spec.entities) == 3
        assert len(spec.endpoints) == 3

    def test_to_dict_roundtrip(self):
        spec = AppSpec(
            app_name="test_app",
            app_type=AppType.CLI_TOOL,
            description="Test CLI",
            entities=["Task"],
            port=5000,
        )
        d = spec.to_dict()
        restored = AppSpec.from_dict(d)
        assert restored.app_name == "test_app"
        assert restored.app_type == AppType.CLI_TOOL
        assert restored.port == 5000


class TestGeneratedFile:
    def test_construction(self):
        gf = GeneratedFile(relative_path="main.py", content="print('hello')", is_executable=True)
        assert gf.relative_path == "main.py"
        assert gf.is_executable

    def test_to_dict(self):
        gf = GeneratedFile(relative_path="README.md", content="# Hello")
        d = gf.to_dict()
        assert d["relative_path"] == "README.md"
