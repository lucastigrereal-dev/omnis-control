"""P29 OMNIS OS Layer — OmnisKernel.

The kernel is the entry point for the OMNIS OS. It bootstraps modules,
runs health checks, resolves dependencies, and manages the event bus.
"""
import time
from typing import Optional

from src.omnis_os.models import (
    KernelConfig, BootstrapResult, OmnisEvent,
    HEALTHY, HEALTH_DEGRADED, HEALTH_ERROR,
    STATUS_ACTIVE, STATUS_DEGRADED,
)
from src.omnis_os.errors import BootstrapError, DependencyCycleError
from src.omnis_os.registry import ModuleRegistry
from src.omnis_os.dependency import resolve_order, detect_cycles, validate_dependencies
from src.omnis_os.event_bus import EventBus
from src.omnis_os.health_monitor import HealthMonitor
from src.utils.dry_run import resolve_dry_run


class OmnisKernel:
    """OMNIS OS Kernel — bootstraps and manages the module ecosystem."""

    def __init__(self, config: Optional[KernelConfig] = None,
                 dry_run: bool = None):
        self.config = config or KernelConfig()
        self.dry_run = resolve_dry_run(dry_run)
        self.registry = ModuleRegistry()
        self.event_bus = EventBus(dry_run=dry_run)
        self.health_monitor = HealthMonitor(
            self.registry,
            max_concurrent=self.config.max_concurrent_health_checks,
            dry_run=dry_run,
        )
        self._bootstrapped = False

    # ── Bootstrap ─────────────────────────────────────────────────

    def bootstrap(self, modules: Optional[list] = None) -> BootstrapResult:
        """Bootstrap the OMNIS OS with a set of modules.

        Args:
            modules: List of modules (ModuleInfo objects or legacy wrappers).
                     If None, uses already-registered modules.

        Returns:
            BootstrapResult with status, counts, and any errors/cycles.
        """
        start = time.monotonic()
        result = BootstrapResult()
        result.status = "bootstrapping"

        if self.dry_run:
            result.status = "dry_run"

        try:
            if modules:
                for m in modules:
                    if hasattr(m, 'to_module_info'):
                        self.registry.register(m.to_module_info())
                    elif hasattr(m, 'module_id'):
                        self.registry.register(m)
                    else:
                        result.errors.append(f"Unknown module type: {type(m).__name__}")

            all_mods = self.registry.list_all()
            result.modules_found = len(all_mods)

            # Detect legacy
            result.legacy_modules = [m.name for m in all_mods if m.is_legacy]

            # Detect cycles
            cycles = detect_cycles(all_mods)
            result.cycles_detected = cycles

            # Validate dependencies
            ok, missing = validate_dependencies(all_mods)
            if not ok:
                result.errors.extend(missing)

            # Try to resolve order
            try:
                resolve_order(all_mods)
            except DependencyCycleError as e:
                result.errors.append(str(e))

            # Activate modules
            for m in all_mods:
                if m.status != STATUS_DEGRADED:
                    m.status = STATUS_ACTIVE
                    result.modules_activated += 1

            # Health check
            self.health_monitor.check_all()

            if not result.errors and not cycles:
                self._bootstrapped = True
                result.status = "ready" if not self.dry_run else "dry_run"

            elif cycles:
                result.status = "degraded"
            else:
                result.status = "error"

        except Exception as exc:
            result.errors.append(str(exc))
            result.status = "error"

        result.duration_ms = int((time.monotonic() - start) * 1000)
        self.event_bus.emit_new("kernel_bootstrapped", "kernel",
                                data=result.to_dict())
        return result

    # ── Shutdown ──────────────────────────────────────────────────

    def shutdown(self) -> dict:
        self.event_bus.emit_new("kernel_shutdown", "kernel")
        self._bootstrapped = False
        return {"status": "shutdown", "dry_run": self.dry_run}

    # ── Status ────────────────────────────────────────────────────

    def status(self) -> dict:
        agg = self.health_monitor.aggregate_status()
        return {
            "bootstrapped": self._bootstrapped,
            "dry_run": self.dry_run,
            "modules": self.registry.module_count,
            "health": agg,
            "events_in_memory": self.event_bus.history_size,
        }

    @property
    def is_bootstrapped(self) -> bool:
        return self._bootstrapped
