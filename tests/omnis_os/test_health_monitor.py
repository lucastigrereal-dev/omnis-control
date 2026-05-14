"""Tests for P29 HealthMonitor."""
from src.omnis_os.health_monitor import HealthMonitor
from src.omnis_os.registry import ModuleRegistry
from src.omnis_os.models import (
    ModuleInfo, ModuleHealth,
    HEALTHY, HEALTH_DEGRADED, HEALTH_ERROR,
)


class TestHealthMonitorCheckOne:
    def test_check_healthy(self):
        reg = ModuleRegistry()
        m = ModuleInfo.new("core")
        reg.register(m)
        monitor = HealthMonitor(reg, dry_run=True)
        result = monitor.check_one(m)
        assert result.status == HEALTHY

    def test_check_no_health(self):
        reg = ModuleRegistry()
        m = ModuleInfo.new("bare")
        m.health = None
        reg.register(m)
        monitor = HealthMonitor(reg, dry_run=True)
        result = monitor.check_one(m)
        assert result.status == HEALTH_ERROR

    def test_check_legacy(self):
        reg = ModuleRegistry()
        m = ModuleInfo.new("old", is_legacy=True)
        reg.register(m)
        monitor = HealthMonitor(reg, dry_run=True)
        result = monitor.check_one(m)
        assert result.module_name == "old"


class TestHealthMonitorCheckAll:
    def test_check_all(self):
        reg = ModuleRegistry()
        for name in ["a", "b", "c"]:
            reg.register(ModuleInfo.new(name))
        monitor = HealthMonitor(reg, dry_run=True)
        results = monitor.check_all()
        assert len(results) == 3
        assert all(isinstance(v, ModuleHealth) for v in results.values())

    def test_check_module_by_name(self):
        reg = ModuleRegistry()
        reg.register(ModuleInfo.new("api"))
        monitor = HealthMonitor(reg, dry_run=True)
        result = monitor.check_module("api")
        assert isinstance(result, ModuleHealth)
        assert result.module_name == "api"

    def test_check_all_with_error_module(self):
        reg = ModuleRegistry()
        bad = ModuleInfo.new("bad")
        bad.health = None
        reg.register(bad)
        reg.register(ModuleInfo.new("good"))
        monitor = HealthMonitor(reg, dry_run=True)
        results = monitor.check_all()
        assert results["bad"].status == HEALTH_ERROR
        assert results["good"].status == HEALTHY


class TestHealthMonitorAggregation:
    def test_aggregate_empty(self):
        reg = ModuleRegistry()
        monitor = HealthMonitor(reg, dry_run=True)
        agg = monitor.aggregate_status()
        assert agg["overall"] == "unknown"
        assert agg["total"] == 0

    def test_aggregate_all_healthy(self):
        reg = ModuleRegistry()
        reg.register(ModuleInfo.new("a"))
        reg.register(ModuleInfo.new("b"))
        monitor = HealthMonitor(reg, dry_run=True)
        monitor.check_all()
        agg = monitor.aggregate_status()
        assert agg["overall"] == HEALTHY
        assert agg["healthy"] == 2

    def test_aggregate_with_degraded(self):
        reg = ModuleRegistry()
        a = ModuleInfo.new("a")
        a.health.status = HEALTHY
        b = ModuleInfo.new("b")
        b.health.status = HEALTH_DEGRADED
        reg.register(a)
        reg.register(b)
        monitor = HealthMonitor(reg, dry_run=True)
        monitor.check_all()
        agg = monitor.aggregate_status()
        assert agg["overall"] == HEALTH_DEGRADED
        assert agg["degraded"] == 1

    def test_aggregate_with_error(self):
        reg = ModuleRegistry()
        a = ModuleInfo.new("a")
        a.health.status = HEALTH_ERROR
        reg.register(a)
        monitor = HealthMonitor(reg, dry_run=True)
        monitor.check_all()
        agg = monitor.aggregate_status()
        assert agg["overall"] == HEALTH_ERROR

    def test_is_all_healthy(self):
        reg = ModuleRegistry()
        reg.register(ModuleInfo.new("ok"))
        monitor = HealthMonitor(reg, dry_run=True)
        monitor.check_all()
        assert monitor.is_all_healthy()

    def test_check_count(self):
        reg = ModuleRegistry()
        reg.register(ModuleInfo.new("x"))
        monitor = HealthMonitor(reg, dry_run=True)
        assert monitor.check_count == 0
        monitor.check_all()
        assert monitor.check_count == 1
        monitor.check_all()
        assert monitor.check_count == 2

    def test_last_results_property(self):
        reg = ModuleRegistry()
        reg.register(ModuleInfo.new("mod"))
        monitor = HealthMonitor(reg, dry_run=True)
        monitor.check_all()
        assert "mod" in monitor.last_results
