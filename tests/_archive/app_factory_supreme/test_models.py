"""Tests for P26 App Factory Supreme — models."""
import pytest

from src.app_factory_supreme.models import (
    BUILD_COMPLETE,
    BUILD_FAILED,
    BUILD_PLANNED,
    BUILD_ROLLED_BACK,
    AppBuild,
    ModuleBuild,
)


class TestModuleBuild:
    def test_new_creates_module(self):
        m = ModuleBuild.new("auth")
        assert m.module_name == "auth"
        assert m.status == BUILD_PLANNED
        assert m.files_generated == []
        assert m.errors == []

    def test_is_success_when_complete_no_errors(self):
        m = ModuleBuild.new("web")
        m.status = BUILD_COMPLETE
        m.errors = []
        assert m.is_success is True

    def test_is_success_false_with_errors(self):
        m = ModuleBuild.new("web")
        m.status = BUILD_COMPLETE
        m.errors = ["something went wrong"]
        assert m.is_success is False

    def test_to_dict_and_from_dict_roundtrip(self):
        m = ModuleBuild.new("api")
        m.files_generated = ["api/__init__.py"]
        m.test_count = 5
        m.test_pass_rate = 1.0
        d = m.to_dict()
        m2 = ModuleBuild.from_dict(d)
        assert m2.module_name == m.module_name
        assert m2.test_count == m.test_count

    def test_default_values(self):
        m = ModuleBuild.new("core")
        assert m.test_pass_rate == 0.0
        assert m.policy_scan_pass is False
        assert m.policy_violations == 0


class TestAppBuild:
    def test_new_creates_build(self):
        b = AppBuild.new(title="Test App")
        assert b.build_id.startswith("apb_")
        assert b.title == "Test App"
        assert b.status == BUILD_PLANNED
        assert b.modules == []

    def test_new_defaults(self):
        b = AppBuild.new()
        assert b.idea_id == ""
        assert b.blueprint_approved is False
        assert b.security_approved is False

    def test_is_complete(self):
        b = AppBuild.new()
        b.status = BUILD_COMPLETE
        assert b.is_complete is True

    def test_is_terminal(self):
        b = AppBuild.new()
        b.status = BUILD_FAILED
        assert b.is_terminal is True

    def test_is_terminal_false_when_planned(self):
        b = AppBuild.new()
        assert b.is_terminal is False

    def test_module_count(self):
        b = AppBuild.new()
        b.modules = [ModuleBuild.new("a"), ModuleBuild.new("b"), ModuleBuild.new("c")]
        assert b.module_count == 3

    def test_modules_passing(self):
        b = AppBuild.new()
        m1 = ModuleBuild.new("a"); m1.tests_pass = True
        m2 = ModuleBuild.new("b"); m2.tests_pass = False
        m3 = ModuleBuild.new("c"); m3.tests_pass = True
        b.modules = [m1, m2, m3]
        assert b.modules_passing == 2

    def test_overall_pass_rate(self):
        b = AppBuild.new()
        m1 = ModuleBuild.new("a"); m1.tests_pass = True
        m2 = ModuleBuild.new("b"); m2.tests_pass = False
        b.modules = [m1, m2]
        assert b.overall_pass_rate == 0.5

    def test_overall_pass_rate_empty_modules(self):
        b = AppBuild.new()
        assert b.overall_pass_rate == 0.0

    def test_to_dict_and_from_dict_roundtrip(self):
        b = AppBuild.new(idea_id="idea_123", title="Test")
        m = ModuleBuild.new("core")
        m.tests_pass = True
        b.modules = [m]
        b.blueprint_approved = True

        d = b.to_dict()
        b2 = AppBuild.from_dict(d)
        assert b2.build_id == b.build_id
        assert b2.title == b.title
        assert b2.blueprint_approved is True
        assert len(b2.modules) == 1

    def test_from_dict_with_empty_modules(self):
        d = {"build_id": "apb_test", "title": "Minimal"}
        b = AppBuild.from_dict(d)
        assert b.title == "Minimal"
        assert b.modules == []

    def test_rollback_status_tracked(self):
        b = AppBuild.new()
        b.status = BUILD_ROLLED_BACK
        assert b.is_terminal is True
