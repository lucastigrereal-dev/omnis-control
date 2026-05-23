"""Tests for App Generator."""

import pytest

from src.app_factory_exec.models import AppSpec, AppType
from src.app_factory_exec.generator import AppGenerator


@pytest.fixture
def generator():
    return AppGenerator()


@pytest.fixture
def api_spec():
    return AppSpec(
        app_name="test_api",
        app_type=AppType.API_BACKEND,
        description="Test API backend",
        entities=["User", "Task"],
    )


@pytest.fixture
def cli_spec():
    return AppSpec(
        app_name="test_cli",
        app_type=AppType.CLI_TOOL,
        description="Test CLI tool",
        entities=["Report"],
    )


def _find_file(files, path):
    for f in files:
        if f.relative_path == path:
            return f
    return None


class TestAppGeneratorAPI:
    def test_generates_all_expected_files(self, generator, api_spec):
        files = generator.generate(api_spec)
        paths = {f.relative_path for f in files}
        assert "main.py" in paths
        assert "models.py" in paths
        assert "database.py" in paths
        assert "seed_data.py" in paths
        assert "requirements.txt" in paths
        assert "README.md" in paths
        assert "tests/test_app.py" in paths

    def test_main_py_has_entities(self, generator, api_spec):
        files = generator.generate(api_spec)
        main_file = _find_file(files, "main.py")
        assert main_file is not None
        assert "User" in main_file.content or "user" in main_file.content.lower()
        assert "Task" in main_file.content or "task" in main_file.content.lower()

    def test_main_py_has_fastapi_app(self, generator, api_spec):
        files = generator.generate(api_spec)
        main_file = _find_file(files, "main.py")
        assert "FastAPI" in main_file.content

    def test_models_py_has_tables(self, generator, api_spec):
        files = generator.generate(api_spec)
        models_file = _find_file(files, "models.py")
        assert models_file is not None
        assert "__tablename__" in models_file.content

    def test_database_py_has_sqlite(self, generator, api_spec):
        files = generator.generate(api_spec)
        db_file = _find_file(files, "database.py")
        assert db_file is not None
        assert "sqlite" in db_file.content.lower()

    def test_readme_has_instructions(self, generator, api_spec):
        files = generator.generate(api_spec)
        readme = _find_file(files, "README.md")
        assert readme is not None
        assert "Instalacao" in readme.content or "Install" in readme.content
        assert "pip install" in readme.content.lower()

    def test_tests_have_health_check(self, generator, api_spec):
        files = generator.generate(api_spec)
        test_file = _find_file(files, "tests/test_app.py")
        assert test_file is not None
        assert "test_health" in test_file.content

    def test_seed_data_has_inserts(self, generator, api_spec):
        files = generator.generate(api_spec)
        seed_file = _find_file(files, "seed_data.py")
        assert seed_file is not None
        assert "db.insert" in seed_file.content


class TestAppGeneratorCLI:
    def test_cli_has_typer(self, generator, cli_spec):
        files = generator.generate(cli_spec)
        cli_file = _find_file(files, "cli.py")
        assert cli_file is not None
        assert "typer" in cli_file.content.lower()


class TestAppGeneratorFullstack:
    def test_includes_frontend(self, generator):
        spec = AppSpec(
            app_name="fullstack_app",
            app_type=AppType.FULLSTACK,
            description="Fullstack app",
            entities=["Product"],
        )
        files = generator.generate(spec)
        paths = {f.relative_path for f in files}
        assert "frontend/index.html" in paths
        assert "frontend/app.js" in paths
        assert "main.py" in paths  # Backend still generated
