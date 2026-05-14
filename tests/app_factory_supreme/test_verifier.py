"""Tests for P26 BuildVerifier."""
import pytest

from src.app_factory_supreme.verifier import BuildVerifier
from src.app_factory_supreme.models import AppBuild, ModuleBuild


class TestBuildVerifier:
    @pytest.fixture
    def verifier(self):
        return BuildVerifier(dry_run=True)

    @pytest.fixture
    def build(self):
        b = AppBuild.new(title="Test")
        b.modules = [ModuleBuild.new("core"), ModuleBuild.new("auth")]
        return b

    def test_verify_dry_run_sets_tests_pass(self, verifier, build):
        result = verifier.verify(build)
        for m in result.modules:
            assert m.tests_pass is True
            assert m.test_count >= 1
            assert m.test_pass_rate == 1.0

    def test_verify_dry_run_sets_policy_scan_pass(self, verifier, build):
        result = verifier.verify(build)
        for m in result.modules:
            assert m.policy_scan_pass is True

    def test_run_tests_sets_test_results(self, verifier, build):
        result = verifier.run_tests(build)
        assert result.test_results["total"] > 0
        assert result.test_results["failed"] == 0

    def test_scan_security(self, verifier, build):
        result = verifier.scan_security(build)
        assert result.policy_violations == []
