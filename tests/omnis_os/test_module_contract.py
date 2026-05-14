"""Tests for P29 OMNIS OS module contract."""
import pytest

from src.omnis_os.module_contract import OmnisModule
from src.omnis_os.models import ModuleHealth, HEALTHY, HEALTH_DEGRADED


class _ConcreteModule(OmnisModule):
    """Minimal concrete implementation for testing."""
    @property
    def name(self) -> str:
        return "test_module"

    @property
    def namespace(self) -> str:
        return "omnis_os"

    @property
    def version(self) -> str:
        return "1.0.0"

    def health_check(self) -> ModuleHealth:
        return ModuleHealth.new(self.name, status=HEALTHY)

    def get_exports(self) -> dict:
        return {"run": lambda: "ok"}


class _ModuleWithDeps(OmnisModule):
    @property
    def name(self) -> str:
        return "dependent"

    @property
    def namespace(self) -> str:
        return "omnis_os"

    @property
    def version(self) -> str:
        return "0.5.0"

    @property
    def dependencies(self) -> list[str]:
        return ["test_module", "core"]

    def health_check(self) -> ModuleHealth:
        return ModuleHealth.new(self.name, status=HEALTHY, warnings=["stale_cache"])

    def get_exports(self) -> dict:
        return {}


class TestOmnisModuleABC:
    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            OmnisModule()

    def test_minimal_concrete(self):
        m = _ConcreteModule()
        assert m.name == "test_module"
        assert m.namespace == "omnis_os"
        assert m.version == "1.0.0"

    def test_default_dependencies(self):
        m = _ConcreteModule()
        assert m.dependencies == []

    def test_custom_dependencies(self):
        m = _ModuleWithDeps()
        assert m.dependencies == ["test_module", "core"]

    def test_health_check_returns_module_health(self):
        m = _ConcreteModule()
        result = m.health_check()
        assert isinstance(result, ModuleHealth)
        assert result.module_name == "test_module"
        assert result.status == HEALTHY

    def test_health_check_with_warnings(self):
        m = _ModuleWithDeps()
        result = m.health_check()
        assert result.warnings == ["stale_cache"]

    def test_get_exports_returns_dict(self):
        m = _ConcreteModule()
        exports = m.get_exports()
        assert isinstance(exports, dict)
        assert "run" in exports

    def test_empty_exports(self):
        m = _ModuleWithDeps()
        assert m.get_exports() == {}


class TestOmnisModuleContractMissingAbstracts:
    """Verify that missing abstract methods prevent instantiation."""

    def test_missing_name_fails(self):
        class Bad(OmnisModule):
            @property
            def namespace(self): return "ns"
            @property
            def version(self): return "1.0"
            def health_check(self): return ModuleHealth.new("x")
            def get_exports(self): return {}
        with pytest.raises(TypeError):
            Bad()

    def test_missing_namespace_fails(self):
        class Bad(OmnisModule):
            @property
            def name(self): return "x"
            @property
            def version(self): return "1.0"
            def health_check(self): return ModuleHealth.new("x")
            def get_exports(self): return {}
        with pytest.raises(TypeError):
            Bad()

    def test_missing_version_fails(self):
        class Bad(OmnisModule):
            @property
            def name(self): return "x"
            @property
            def namespace(self): return "ns"
            def health_check(self): return ModuleHealth.new("x")
            def get_exports(self): return {}
        with pytest.raises(TypeError):
            Bad()

    def test_missing_health_check_fails(self):
        class Bad(OmnisModule):
            @property
            def name(self): return "x"
            @property
            def namespace(self): return "ns"
            @property
            def version(self): return "1.0"
            def get_exports(self): return {}
        with pytest.raises(TypeError):
            Bad()

    def test_missing_get_exports_fails(self):
        class Bad(OmnisModule):
            @property
            def name(self): return "x"
            @property
            def namespace(self): return "ns"
            @property
            def version(self): return "1.0"
            def health_check(self): return ModuleHealth.new("x")
        with pytest.raises(TypeError):
            Bad()


class TestOmnisModuleCompliance:
    def test_full_compliance_passes(self):
        class Compliant(OmnisModule):
            @property
            def name(self): return "compliant"
            @property
            def namespace(self): return "omnis_os"
            @property
            def version(self): return "2.0.0"
            def health_check(self): return ModuleHealth.new("compliant")
            def get_exports(self): return {"fn": lambda x: x}
        m = Compliant()
        assert m.name == "compliant"
        assert m.version == "2.0.0"

    def test_legacy_bridge_marks_unknown(self):
        class LegacyBridge(OmnisModule):
            @property
            def name(self): return "old_legacy"
            @property
            def namespace(self): return "legacy"
            @property
            def version(self): return "0.0.1"
            def health_check(self): return ModuleHealth.new("old_legacy", status=HEALTH_DEGRADED)
            def get_exports(self): return {}
        m = LegacyBridge()
        h = m.health_check()
        assert h.status == HEALTH_DEGRADED
