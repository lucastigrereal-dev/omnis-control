"""Tests for P29 LegacyModule wrapper."""
from src.omnis_os.legacy_wrapper import LegacyModuleWrapper
from src.omnis_os.models import ModuleInfo, ModuleHealth


class TestLegacyWrapperBasics:
    def test_name_contract(self):
        w = LegacyModuleWrapper("old_mod")
        assert w.name == "old_mod"

    def test_namespace_inferred(self):
        w = LegacyModuleWrapper("old_mod", module_path="src.legacy.old_mod")
        assert w.namespace == "src"

    def test_namespace_explicit(self):
        w = LegacyModuleWrapper("old_mod", namespace="custom_ns")
        assert w.namespace == "custom_ns"

    def test_namespace_fallback(self):
        w = LegacyModuleWrapper("bare")
        assert w.namespace == "legacy"

    def test_default_version(self):
        w = LegacyModuleWrapper("x")
        assert w.version == "0.0.0"

    def test_default_dependencies(self):
        w = LegacyModuleWrapper("x")
        assert w.dependencies == []

    def test_set_version(self):
        w = LegacyModuleWrapper("x")
        w.set_version("2.1.0")
        assert w.version == "2.1.0"

    def test_set_dependencies(self):
        w = LegacyModuleWrapper("x")
        w.set_dependencies(["a", "b"])
        assert w.dependencies == ["a", "b"]


class TestLegacyWrapperHealthCheck:
    def test_health_check_returns_module_health(self):
        w = LegacyModuleWrapper("legacy_mod")
        h = w.health_check()
        assert isinstance(h, ModuleHealth)

    def test_health_check_imports_ok(self):
        w = LegacyModuleWrapper("src.omnis_os.models", module_path="src.omnis_os.models")
        h = w.health_check()
        assert h.imports_ok is True

    def test_health_check_warning_for_legacy(self):
        w = LegacyModuleWrapper("legacy_mod")
        h = w.health_check()
        assert any("Legacy" in warn for warn in h.warnings)


class TestLegacyWrapperExports:
    def test_get_exports_is_dict(self):
        w = LegacyModuleWrapper("x")
        assert isinstance(w.get_exports(), dict)

    def test_get_exports_legacy_flag(self):
        w = LegacyModuleWrapper("x")
        assert w.get_exports().get("_legacy") is True


class TestLegacyWrapperToModuleInfo:
    def test_to_module_info(self):
        w = LegacyModuleWrapper("oldie", namespace="ns", module_path="src.oldie")
        w.set_version("1.5")
        mi = w.to_module_info()
        assert isinstance(mi, ModuleInfo)
        assert mi.name == "oldie"
        assert mi.namespace == "ns"
        assert mi.is_legacy is True
        assert mi.health is not None

    def test_to_module_info_defaults(self):
        w = LegacyModuleWrapper("bare")
        mi = w.to_module_info()
        assert mi.name == "bare"
        assert mi.is_legacy is True
