"""E2E tests for P29 OMNIS OS Layer."""
from src.omnis_os.kernel import OmnisKernel
from src.omnis_os.registry import ModuleRegistry
from src.omnis_os.dependency import resolve_order, detect_cycles
from src.omnis_os.event_bus import EventBus
from src.omnis_os.health_monitor import HealthMonitor
from src.omnis_os.models import ModuleInfo, ModuleHealth, OmnisEvent, KernelConfig
from src.omnis_os.legacy_wrapper import LegacyModuleWrapper
from src.omnis_os.errors import ModuleNotFoundError


class TestE2EFullBootstrap:
    """Register → resolve → health check → events → shutdown."""

    def test_full_lifecycle(self):
        kernel = OmnisKernel(dry_run=True)

        # 1. Create module graph
        core = ModuleInfo.new("core", namespace="omnis_os", version="1.0.0")
        scheduler = ModuleInfo.new("scheduler", namespace="omnis_os", version="1.0.0",
                                   dependencies=["core"])
        api = ModuleInfo.new("api", namespace="omnis_os", version="2.0.0",
                            dependencies=["core", "scheduler"])
        legacy = LegacyModuleWrapper("old_reports", namespace="legacy", module_path="src.old_reports")
        legacy.set_version("0.1.0")
        legacy.set_dependencies(["core"])

        # 2. Bootstrap
        result = kernel.bootstrap([core, scheduler, api, legacy])
        assert result.modules_found == 4
        assert result.modules_activated == 4
        assert len(result.legacy_modules) == 1
        assert "old_reports" in result.legacy_modules

        # 3. Verify registry
        assert kernel.registry.module_count == 4
        assert kernel.registry.exists("core")
        assert kernel.registry.exists("api")

        # 4. Resolve dependency order
        all_mods = kernel.registry.list_all()
        order = resolve_order(all_mods)
        assert order.index("core") < order.index("scheduler") < order.index("api")

        # 5. Health check
        kernel.health_monitor.check_all()
        agg = kernel.health_monitor.aggregate_status()
        assert agg["total"] == 4

        # 6. Events
        events = kernel.event_bus.history()
        assert any(e.event_type == "kernel_bootstrapped" for e in events)

        # 7. Shutdown
        result = kernel.shutdown()
        assert result["status"] == "shutdown"
        assert not kernel.is_bootstrapped

    def test_bootstrap_prevents_cycle_activation(self):
        kernel = OmnisKernel(dry_run=True)
        a = ModuleInfo.new("a", dependencies=["b"])
        b = ModuleInfo.new("b", dependencies=["a"])
        result = kernel.bootstrap([a, b])
        assert not kernel.is_bootstrapped
        assert len(result.cycles_detected) > 0


class TestE2ERoundtrips:
    def test_event_roundtrip(self):
        e1 = OmnisEvent.new("test", "kernel", data={"key": "val"})
        e2 = OmnisEvent.from_dict(e1.to_dict())
        assert e2.event_id == e1.event_id
        assert e2.data == e1.data

    def test_config_roundtrip(self):
        c1 = KernelConfig(scan_paths=["a/", "b/"], max_concurrent_health_checks=8)
        c2 = KernelConfig.from_dict(c1.to_dict())
        assert c2.scan_paths == c1.scan_paths
        assert c2.max_concurrent_health_checks == 8


class TestE2EDegradation:
    def test_unknown_module_type(self):
        kernel = OmnisKernel(dry_run=True)
        result = kernel.bootstrap([42])  # int is not a module
        assert len(result.errors) > 0

    def test_missing_dependency_graceful(self):
        kernel = OmnisKernel(dry_run=True)
        orphan = ModuleInfo.new("orphan", dependencies=["nonexistent"])
        result = kernel.bootstrap([orphan])
        # Should not crash, just record errors
        assert result.status in ("dry_run", "error")
