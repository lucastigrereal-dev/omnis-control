"""Tests for P26 AppPackager."""
import pytest

from src.app_factory_supreme.packager import AppPackager
from src.app_factory_supreme.models import AppBuild, ModuleBuild


class TestAppPackager:
    @pytest.fixture
    def packager(self):
        return AppPackager(dry_run=True)

    @pytest.fixture
    def build(self):
        b = AppBuild.new(title="Test App")
        m = ModuleBuild.new("core")
        m.tests_pass = True
        m.test_count = 5
        b.modules = [m]
        return b

    def test_package_dry_run_sets_output_dir(self, packager, build):
        result = packager.package(build)
        assert "generated_apps" in result.output_dir

    def test_generate_readme(self, packager, build):
        readme = packager.generate_readme(build)
        assert "Test App" in readme
        assert build.build_id in readme
        assert "core" in readme

    def test_generate_dockerfile(self, packager, build):
        dockerfile = packager.generate_dockerfile(build)
        assert "FROM python" in dockerfile
        assert "WORKDIR /app" in dockerfile
