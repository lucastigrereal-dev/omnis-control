"""Tests for P29 ModuleRegistry."""
import pytest

from src.omnis_os.registry import ModuleRegistry
from src.omnis_os.models import ModuleInfo, STATUS_ACTIVE, STATUS_DEGRADED, STATUS_REGISTERED
from src.omnis_os.errors import ModuleNotFoundError


class TestModuleRegistryCRUD:
    def test_register_and_get(self):
        reg = ModuleRegistry()
        m = ModuleInfo.new("api", namespace="omnis_os")
        reg.register(m)
        assert reg.get(m.module_id) is m

    def test_get_missing_raises(self):
        reg = ModuleRegistry()
        with pytest.raises(ModuleNotFoundError):
            reg.get("nonexistent")

    def test_unregister(self):
        reg = ModuleRegistry()
        m = ModuleInfo.new("temp")
        reg.register(m)
        reg.unregister(m.module_id)
        with pytest.raises(ModuleNotFoundError):
            reg.get(m.module_id)

    def test_unregister_missing_noop(self):
        reg = ModuleRegistry()
        reg.unregister("nonexistent")  # no error

    def test_find_by_name(self):
        reg = ModuleRegistry()
        m = ModuleInfo.new("core", namespace="omnis_os")
        reg.register(m)
        assert reg.find("core") is m

    def test_find_by_name_missing_raises(self):
        reg = ModuleRegistry()
        with pytest.raises(ModuleNotFoundError):
            reg.find("ghost")

    def test_find_by_name_optional(self):
        reg = ModuleRegistry()
        assert reg.find_by_name("nope") is None

    def test_find_by_name_optional_found(self):
        reg = ModuleRegistry()
        m = ModuleInfo.new("db")
        reg.register(m)
        assert reg.find_by_name("db") is m


class TestModuleRegistryResolve:
    def test_resolve_by_id(self):
        reg = ModuleRegistry()
        m = ModuleInfo.new("scheduler")
        reg.register(m)
        assert reg.resolve(m.module_id) is m

    def test_resolve_by_name(self):
        reg = ModuleRegistry()
        m = ModuleInfo.new("scheduler")
        reg.register(m)
        assert reg.resolve("scheduler") is m

    def test_resolve_missing_raises(self):
        reg = ModuleRegistry()
        with pytest.raises(ModuleNotFoundError):
            reg.resolve("nobody")


class TestModuleRegistryListing:
    def test_list_all(self):
        reg = ModuleRegistry()
        for name in ["a", "b", "c"]:
            reg.register(ModuleInfo.new(name))
        assert len(reg.list_all()) == 3

    def test_list_active(self):
        reg = ModuleRegistry()
        a = ModuleInfo.new("a")
        a.status = STATUS_ACTIVE
        b = ModuleInfo.new("b")
        reg.register(a)
        reg.register(b)
        assert len(reg.list_active()) == 1

    def test_list_by_namespace(self):
        reg = ModuleRegistry()
        reg.register(ModuleInfo.new("a", namespace="omnis_os"))
        reg.register(ModuleInfo.new("b", namespace="self_improvement"))
        assert len(reg.list_by_namespace("omnis_os")) == 1
        assert len(reg.list_by_namespace("self_improvement")) == 1

    def test_list_legacy(self):
        reg = ModuleRegistry()
        reg.register(ModuleInfo.new("modern"))
        reg.register(ModuleInfo.new("old", is_legacy=True))
        assert len(reg.list_legacy()) == 1


class TestModuleRegistryInfo:
    def test_module_count(self):
        reg = ModuleRegistry()
        assert reg.module_count == 0
        reg.register(ModuleInfo.new("x"))
        assert reg.module_count == 1

    def test_module_names(self):
        reg = ModuleRegistry()
        reg.register(ModuleInfo.new("alpha"))
        reg.register(ModuleInfo.new("beta"))
        assert set(reg.module_names) == {"alpha", "beta"}

    def test_exists(self):
        reg = ModuleRegistry()
        reg.register(ModuleInfo.new("gamma"))
        assert reg.exists("gamma")
        assert not reg.exists("delta")
