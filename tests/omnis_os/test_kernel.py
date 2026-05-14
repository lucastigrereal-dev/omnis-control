"""Tests for P29 OmnisKernel."""
from src.omnis_os.kernel import OmnisKernel
from src.omnis_os.models import ModuleInfo, KernelConfig, BootstrapResult


class TestKernelInit:
    def test_default_config(self):
        k = OmnisKernel(dry_run=True)
        assert k.config is not None
        assert k.dry_run is True
        assert k.registry is not None
        assert k.event_bus is not None
        assert k.health_monitor is not None

    def test_custom_config(self):
        cfg = KernelConfig(scan_paths=["lib/"], health_check_interval_seconds=120)
        k = OmnisKernel(config=cfg, dry_run=False)
        assert k.config.scan_paths == ["lib/"]
        assert k.dry_run is False

    def test_not_bootstrapped_initially(self):
        k = OmnisKernel(dry_run=True)
        assert not k.is_bootstrapped


class TestKernelBootstrap:
    def test_bootstrap_empty(self):
        k = OmnisKernel(dry_run=True)
        result = k.bootstrap([])
        assert isinstance(result, BootstrapResult)
        assert result.modules_found == 0

    def test_bootstrap_with_modules(self):
        k = OmnisKernel(dry_run=True)
        mods = [ModuleInfo.new("a"), ModuleInfo.new("b")]
        result = k.bootstrap(mods)
        assert result.modules_found == 2
        assert result.modules_activated == 2
        assert result.status == "dry_run"

    def test_bootstrap_detects_legacy(self):
        k = OmnisKernel(dry_run=True)
        mods = [ModuleInfo.new("modern"), ModuleInfo.new("ancient", is_legacy=True)]
        result = k.bootstrap(mods)
        assert "ancient" in result.legacy_modules
        assert "modern" not in result.legacy_modules

    def test_bootstrap_detects_cycles(self):
        k = OmnisKernel(dry_run=True)
        a = ModuleInfo.new("a", dependencies=["b"])
        b = ModuleInfo.new("b", dependencies=["a"])
        result = k.bootstrap([a, b])
        assert len(result.cycles_detected) > 0

    def test_bootstrap_registers_from_wrappers(self):
        from src.omnis_os.legacy_wrapper import LegacyModuleWrapper
        k = OmnisKernel(dry_run=True)
        w = LegacyModuleWrapper("legacy_thing")
        result = k.bootstrap([w])
        assert result.modules_found == 1
        assert k.registry.find_by_name("legacy_thing") is not None

    def test_bootstrap_emits_event(self):
        k = OmnisKernel(dry_run=True)
        k.bootstrap([ModuleInfo.new("x")])
        events = k.event_bus.history(event_type="kernel_bootstrapped")
        assert len(events) == 1

    def test_bootstrap_sets_bootstrapped_on_success(self):
        k = OmnisKernel(dry_run=True)
        k.bootstrap([ModuleInfo.new("x")])
        assert k.is_bootstrapped

    def test_bootstrap_not_bootstrapped_on_cycles(self):
        k = OmnisKernel(dry_run=True)
        a = ModuleInfo.new("a", dependencies=["b"])
        b = ModuleInfo.new("b", dependencies=["a"])
        k.bootstrap([a, b])
        assert not k.is_bootstrapped


class TestKernelShutdown:
    def test_shutdown(self):
        k = OmnisKernel(dry_run=True)
        k.bootstrap([ModuleInfo.new("x")])
        result = k.shutdown()
        assert result["status"] == "shutdown"
        assert not k.is_bootstrapped

    def test_shutdown_emits_event(self):
        k = OmnisKernel(dry_run=True)
        k.bootstrap([ModuleInfo.new("x")])
        k.shutdown()
        events = k.event_bus.history(event_type="kernel_shutdown")
        assert len(events) == 1


class TestKernelStatus:
    def test_status(self):
        k = OmnisKernel(dry_run=True)
        k.bootstrap([ModuleInfo.new("api")])
        s = k.status()
        assert s["bootstrapped"] is True
        assert s["dry_run"] is True
        assert s["modules"] == 1
        assert "health" in s
