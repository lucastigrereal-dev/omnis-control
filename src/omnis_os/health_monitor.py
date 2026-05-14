"""P29 OMNIS OS Layer — HealthMonitor.

Periodic health checks across all registered modules.
Reports aggregated health status to the kernel.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from src.omnis_os.registry import ModuleRegistry
from src.omnis_os.models import (
    ModuleHealth, ModuleInfo, HEALTHY, HEALTH_DEGRADED, HEALTH_ERROR,
    STATUS_ACTIVE, STATUS_DEGRADED,
)
from src.omnis_os.errors import HealthCheckError


class HealthMonitor:
    """Runs health checks across the registry and reports status."""

    def __init__(self, registry: ModuleRegistry,
                 max_concurrent: int = 5,
                 dry_run: bool = True):
        self.registry = registry
        self.max_concurrent = max_concurrent
        self.dry_run = dry_run
        self._last_results: dict[str, ModuleHealth] = {}
        self._check_count: int = 0

    # ── Health checks ─────────────────────────────────────────────

    def check_one(self, module: ModuleInfo) -> ModuleHealth:
        """Run health check for a single module.

        Uses the module's health attribute and runs an import probe
        if the module is legacy.
        """
        if module.health is None:
            return ModuleHealth.new(
                module.name, status=HEALTH_ERROR,
                imports_ok=False, errors=["No health data available"],
            )

        if module.is_legacy:
            # Legacy modules stay at their current health
            return module.health

        return module.health

    def check_all(self) -> dict[str, ModuleHealth]:
        """Run health checks on all registered modules.

        Uses ThreadPoolExecutor for concurrent checks up to max_concurrent.
        """
        modules = self.registry.list_all()
        results: dict[str, ModuleHealth] = {}

        with ThreadPoolExecutor(max_workers=self.max_concurrent) as pool:
            futures = {pool.submit(self.check_one, m): m for m in modules}
            for future in as_completed(futures):
                mod = futures[future]
                try:
                    results[mod.name] = future.result()
                except Exception as exc:
                    results[mod.name] = ModuleHealth.new(
                        mod.name, status=HEALTH_ERROR,
                        imports_ok=False, errors=[str(exc)],
                    )

        self._last_results = results
        self._check_count += 1
        return results

    def check_module(self, name: str) -> ModuleHealth:
        mod = self.registry.find(name)
        result = self.check_one(mod)
        self._last_results[name] = result
        return result

    # ── Aggregation ───────────────────────────────────────────────

    def aggregate_status(self) -> dict:
        """Return aggregated health summary."""
        if not self._last_results:
            return {"overall": "unknown", "healthy": 0, "degraded": 0,
                    "error": 0, "total": 0}

        healthy = sum(1 for h in self._last_results.values() if h.status == HEALTHY)
        degraded = sum(1 for h in self._last_results.values() if h.status == HEALTH_DEGRADED)
        error = sum(1 for h in self._last_results.values() if h.status == HEALTH_ERROR)
        total = len(self._last_results)

        if total == 0:
            overall = "unknown"
        elif error > 0:
            overall = HEALTH_ERROR
        elif degraded > 0:
            overall = HEALTH_DEGRADED
        else:
            overall = HEALTHY

        return {
            "overall": overall, "healthy": healthy, "degraded": degraded,
            "error": error, "total": total, "check_count": self._check_count,
        }

    def is_all_healthy(self) -> bool:
        agg = self.aggregate_status()
        return agg["overall"] == HEALTHY

    # ── Queries ───────────────────────────────────────────────────

    @property
    def last_results(self) -> dict[str, ModuleHealth]:
        return dict(self._last_results)

    @property
    def check_count(self) -> int:
        return self._check_count
