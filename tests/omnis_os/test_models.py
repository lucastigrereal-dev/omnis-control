"""Tests for P29 OMNIS OS models."""
import pytest

from src.omnis_os.models import (
    ModuleHealth, ModuleInfo, OmnisEvent, KernelConfig, BootstrapResult,
    HEALTHY, HEALTH_DEGRADED, HEALTH_ERROR, HEALTH_UNKNOWN,
    STATUS_REGISTERED, STATUS_ACTIVE, STATUS_DEGRADED, STATUS_INACTIVE, STATUS_UNKNOWN,
    MODULE_STATUSES,
)


class TestModuleHealth:
    def test_default_healthy(self):
        h = ModuleHealth("test_module")
        assert h.module_name == "test_module"
        assert h.status == HEALTHY
        assert h.imports_ok is True
        assert h.tests_passing == 0
        assert h.tests_total == 0
        assert h.version == "0.0.0"
        assert h.errors == []
        assert h.warnings == []
        assert h.last_checked

    def test_new_factory(self):
        h = ModuleHealth.new("core", status=HEALTH_DEGRADED, imports_ok=False,
                             tests_passing=5, tests_total=10, version="1.2.3",
                             errors=["e1"], warnings=["w1"])
        assert h.module_name == "core"
        assert h.status == HEALTH_DEGRADED
        assert h.imports_ok is False
        assert h.tests_passing == 5
        assert h.tests_total == 10
        assert h.version == "1.2.3"
        assert h.errors == ["e1"]
        assert h.warnings == ["w1"]

    def test_new_defaults(self):
        h = ModuleHealth.new("test")
        assert h.status == HEALTHY
        assert h.imports_ok is True
        assert h.errors == []
        assert h.warnings == []

    def test_is_healthy(self):
        assert ModuleHealth("a", status=HEALTHY, imports_ok=True).is_healthy
        assert not ModuleHealth("a", status=HEALTH_DEGRADED, imports_ok=True).is_healthy
        assert not ModuleHealth("a", status=HEALTHY, imports_ok=False).is_healthy

    def test_test_pass_rate(self):
        assert ModuleHealth("a", tests_passing=10, tests_total=10).test_pass_rate == 1.0
        assert ModuleHealth("a", tests_passing=5, tests_total=10).test_pass_rate == 0.5
        assert ModuleHealth("a", tests_passing=0, tests_total=0).test_pass_rate == 1.0

    def test_to_dict(self):
        h = ModuleHealth.new("mod", version="2.0.0", errors=["err1"])
        d = h.to_dict()
        assert d["module_name"] == "mod"
        assert d["version"] == "2.0.0"
        assert d["errors"] == ["err1"]
        assert "last_checked" in d

    def test_from_dict(self):
        d = {"module_name": "x", "status": "error", "imports_ok": False,
             "tests_passing": 2, "tests_total": 8, "version": "3.0.0",
             "last_checked": "2026-01-01T00:00:00", "errors": ["bad"],
             "warnings": ["careful"]}
        h = ModuleHealth.from_dict(d)
        assert h.module_name == "x"
        assert h.status == "error"
        assert h.tests_total == 8
        assert h.errors == ["bad"]
        assert h.warnings == ["careful"]

    def test_from_dict_defaults(self):
        h = ModuleHealth.from_dict({})
        assert h.module_name == ""
        assert h.status == HEALTHY

    def test_roundtrip(self):
        h1 = ModuleHealth.new("r", status=HEALTH_ERROR, imports_ok=False,
                              tests_passing=3, tests_total=5, version="0.1.0",
                              errors=["critical"])
        h2 = ModuleHealth.from_dict(h1.to_dict())
        assert h2.module_name == h1.module_name
        assert h2.status == h1.status
        assert h2.tests_passing == h1.tests_passing


class TestModuleInfo:
    def test_new_factory(self):
        m = ModuleInfo.new("scheduler", namespace="omnis_os", version="1.0.0",
                           dependencies=["core"], is_legacy=False)
        assert m.name == "scheduler"
        assert m.namespace == "omnis_os"
        assert m.version == "1.0.0"
        assert m.dependencies == ["core"]
        assert m.is_legacy is False
        assert m.module_id.startswith("om_")
        assert m.status == STATUS_REGISTERED
        assert m.health is not None
        assert m.health.status == HEALTHY
        assert m.registered_at

    def test_new_legacy_module(self):
        m = ModuleInfo.new("old_module", is_legacy=True)
        assert m.is_legacy is True
        assert m.health.status == HEALTH_UNKNOWN

    def test_new_default_dependencies(self):
        m = ModuleInfo.new("solo")
        assert m.dependencies == []

    def test_to_dict(self):
        m = ModuleInfo.new("api", namespace="web", version="2.0.0")
        d = m.to_dict()
        assert d["name"] == "api"
        assert d["namespace"] == "web"
        assert d["is_legacy"] is False
        assert isinstance(d["health"], dict)

    def test_to_dict_none_health(self):
        m = ModuleInfo.new("api")
        m.health = None
        d = m.to_dict()
        assert d["health"] is None

    def test_from_dict(self):
        d = {
            "module_id": "om_abcd1234", "name": "test", "namespace": "ns",
            "version": "1.0.0", "status": STATUS_ACTIVE,
            "dependencies": ["core"], "dependents": ["api"],
            "health": {"module_name": "test", "status": HEALTHY},
            "is_legacy": False, "registered_at": "2026-01-01T00:00:00",
            "last_health_check": "2026-05-01T00:00:00",
        }
        m = ModuleInfo.from_dict(d)
        assert m.module_id == "om_abcd1234"
        assert m.name == "test"
        assert m.status == STATUS_ACTIVE
        assert m.dependencies == ["core"]
        assert m.dependents == ["api"]
        assert m.health.module_name == "test"

    def test_from_dict_defaults(self):
        m = ModuleInfo.from_dict({})
        assert m.module_id == ""
        assert m.name == ""
        assert m.status == STATUS_REGISTERED

    def test_from_dict_no_health(self):
        m = ModuleInfo.from_dict({"name": "bare"})
        assert m.health is None

    def test_roundtrip(self):
        m1 = ModuleInfo.new("rt", namespace="omnis_os", dependencies=["a", "b"])
        m1.status = STATUS_DEGRADED
        m2 = ModuleInfo.from_dict(m1.to_dict())
        assert m2.module_id == m1.module_id
        assert m2.dependencies == ["a", "b"]
        assert m2.status == STATUS_DEGRADED


class TestOmnisEvent:
    def test_new_factory(self):
        e = OmnisEvent.new("module_activated", "kernel", data={"module": "api"})
        assert e.event_id.startswith("ose_")
        assert e.event_type == "module_activated"
        assert e.source_module == "kernel"
        assert e.data == {"module": "api"}
        assert e.timestamp

    def test_new_default_data(self):
        e = OmnisEvent.new("heartbeat", "monitor")
        assert e.data == {}

    def test_to_dict(self):
        e = OmnisEvent.new("test", "src", data={"k": "v"})
        d = e.to_dict()
        assert d["event_id"] == e.event_id
        assert d["data"] == {"k": "v"}

    def test_from_dict(self):
        d = {"event_id": "ose_ff", "event_type": "type_a", "source_module": "mod",
             "data": {"x": 1}, "timestamp": "2026-01-01T00:00:00"}
        e = OmnisEvent.from_dict(d)
        assert e.event_id == "ose_ff"
        assert e.data == {"x": 1}

    def test_from_dict_defaults(self):
        e = OmnisEvent.from_dict({})
        assert e.event_id == ""
        assert e.source_module == ""

    def test_roundtrip(self):
        e1 = OmnisEvent.new("shutdown", "kernel", data={"reason": "restart"})
        e2 = OmnisEvent.from_dict(e1.to_dict())
        assert e2.event_id == e1.event_id
        assert e2.event_type == "shutdown"
        assert e2.data == e1.data


class TestKernelConfig:
    def test_defaults(self):
        c = KernelConfig()
        assert c.scan_paths == ["src/"]
        assert c.health_check_interval_seconds == 60
        assert c.bootstrap_timeout_seconds == 30
        assert c.shutdown_timeout_seconds == 10
        assert c.max_concurrent_health_checks == 5

    def test_custom(self):
        c = KernelConfig(scan_paths=["lib/", "src/"], health_check_interval_seconds=30,
                         max_concurrent_health_checks=10)
        assert c.scan_paths == ["lib/", "src/"]
        assert c.health_check_interval_seconds == 30
        assert c.max_concurrent_health_checks == 10

    def test_to_dict(self):
        c = KernelConfig(scan_paths=["a/"])
        d = c.to_dict()
        assert d["scan_paths"] == ["a/"]
        assert d["bootstrap_timeout_seconds"] == 30

    def test_from_dict(self):
        d = {"scan_paths": ["x/"], "health_check_interval_seconds": 15,
             "bootstrap_timeout_seconds": 60, "shutdown_timeout_seconds": 5,
             "max_concurrent_health_checks": 3}
        c = KernelConfig.from_dict(d)
        assert c.scan_paths == ["x/"]
        assert c.health_check_interval_seconds == 15

    def test_from_dict_defaults(self):
        c = KernelConfig.from_dict({})
        assert c.scan_paths == ["src/"]
        assert c.health_check_interval_seconds == 60

    def test_roundtrip(self):
        c1 = KernelConfig(scan_paths=["p1/", "p2/"], max_concurrent_health_checks=8)
        c2 = KernelConfig.from_dict(c1.to_dict())
        assert c2.scan_paths == c1.scan_paths
        assert c2.max_concurrent_health_checks == 8


class TestBootstrapResult:
    def test_new_factory(self):
        b = BootstrapResult.new(modules_found=5, modules_activated=4,
                                legacy_modules=["old1"], errors=["timeout"],
                                duration_ms=1200)
        assert b.modules_found == 5
        assert b.modules_activated == 4
        assert b.legacy_modules == ["old1"]
        assert b.errors == ["timeout"]
        assert b.duration_ms == 1200

    def test_new_defaults(self):
        b = BootstrapResult.new()
        assert b.modules_found == 0
        assert b.modules_activated == 0
        assert b.legacy_modules == []
        assert b.cycles_detected == []
        assert b.errors == []
        assert b.duration_ms == 0

    def test_to_dict(self):
        b = BootstrapResult.new(modules_found=3, cycles_detected=[["a", "b"]])
        d = b.to_dict()
        assert d["status"] == "dry_run"
        assert d["modules_found"] == 3
        assert d["cycles_detected"] == [["a", "b"]]


class TestModuleStatusConstants:
    def test_all_statuses_defined(self):
        assert len(MODULE_STATUSES) == 5
        assert STATUS_REGISTERED in MODULE_STATUSES
        assert STATUS_ACTIVE in MODULE_STATUSES
        assert STATUS_DEGRADED in MODULE_STATUSES
        assert STATUS_INACTIVE in MODULE_STATUSES
        assert STATUS_UNKNOWN in MODULE_STATUSES
