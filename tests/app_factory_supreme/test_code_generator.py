"""Tests for P26 CodeGenerator."""
import pytest

from src.app_factory_supreme.code_generator import CodeGenerator
from src.app_factory_supreme.models import ModuleBuild


class TestCodeGenerator:
    @pytest.fixture
    def generator(self):
        return CodeGenerator(dry_run=True)

    def test_generate_module_dry_run(self, generator):
        m = ModuleBuild.new("auth")
        result = generator.generate_module(m)
        assert result["status"] == "dry_run"
        assert "auth" in result["module"]

    def test_generate_tests_dry_run(self, generator):
        m = ModuleBuild.new("core")
        content = generator.generate_tests(m)
        assert "DRY-RUN" in content
        assert "def test_placeholder" in content

    def test_scan_policy_returns_empty(self, generator):
        violations = generator.scan_policy("print('hello')")
        assert violations == []

    def test_generate_module_real_mode(self):
        gen = CodeGenerator(dry_run=False)
        m = ModuleBuild.new("web")
        result = gen.generate_module(m)
        assert result["status"] == "generated"
