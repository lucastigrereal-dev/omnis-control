"""P24 Live Cockpit Supreme — Data Collector."""
from __future__ import annotations

import logging
from typing import Optional

from src.live_cockpit.alerts import AlertAggregator
from src.live_cockpit.errors import CollectionError, ModuleUnreachableError
from src.live_cockpit.models import CockpitModule, CockpitSnapshot

logger = logging.getLogger(__name__)


class CockpitCollector:
    """Coleta dados de todos os modulos para montar o snapshot."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self.alert_aggregator = AlertAggregator()

    def collect_all(self) -> CockpitSnapshot:
        """Coleta dados de todos os modulos registrados."""
        snapshot = CockpitSnapshot.new()

        collectors = [
            (self.collect_missions, "missions"),
            (self.collect_campaigns, "campaigns"),
            (self.collect_deliveries, "deliveries"),
            (self.collect_publish_queue, "publish_queue"),
            (self.collect_observability, "observability"),
            (self.collect_memory, "memory"),
            (self.collect_capability_gaps, "capability_gaps"),
            (self.collect_autonomous, "autonomous"),
            (self.collect_system_health, "system_health"),
        ]

        for collector_fn, name in collectors:
            try:
                data = collector_fn()
                if data:
                    self._merge(snapshot, data)
            except CollectionError as e:
                snapshot.collection_warnings.append(f"{name}: {e}")
            except Exception as e:
                snapshot.collection_errors.append(f"{name}: {e}")

        modules_data = self.collect_module_health()
        snapshot.modules = modules_data.get("modules", [])
        snapshot.modules_total = len(snapshot.modules)
        snapshot.modules_healthy = sum(1 for m in snapshot.modules if m.is_healthy)

        all_alerts = self.alert_aggregator.collect_alerts(snapshot)
        snapshot.alerts = self.alert_aggregator.prioritize(all_alerts)

        return snapshot

    def _merge(self, snapshot: CockpitSnapshot, data: dict) -> None:
        """Mescla dados de um collector no snapshot."""
        for key, value in data.items():
            if hasattr(snapshot, key):
                setattr(snapshot, key, value)

    # ── Collectors ──────────────────────────────────────────────────────────

    def collect_missions(self) -> dict:
        """Coleta dados de missoes (P20)."""
        try:
            from src.omnis_supreme.models import SupremeStatus
        except ImportError:
            return {
                "active_missions": [],
                "missions_today": 0,
                "missions_completed_today": 0,
                "pending_approvals": 0,
            }
        # Skeleton: retorna dados simulados
        return {
            "active_missions": [],
            "missions_today": 0,
            "missions_completed_today": 0,
            "pending_approvals": 0,
        }

    def collect_campaigns(self) -> dict:
        """Coleta dados de campanhas (P19)."""
        return {"active_campaigns": 0}

    def collect_deliveries(self) -> dict:
        """Coleta dados de deliveries (P17)."""
        return {"pending_deliveries": 0}

    def collect_publish_queue(self) -> dict:
        """Coleta dados da fila de publish (P8)."""
        return {"publish_queue_size": 0}

    def collect_observability(self) -> dict:
        """Coleta dados de observability (P16)."""
        try:
            from src.observability_local import ObservabilitySnapshot
        except ImportError:
            return {
                "tests_passing": 0,
                "tests_failing": 0,
            }
        return {"tests_passing": 0, "tests_failing": 0}

    def collect_memory(self) -> dict:
        """Coleta dados de memoria (P21 + P4)."""
        result = {"memory_sources_available": 0, "recent_learnings": []}
        try:
            from src.memory_intel import MemoryIntelligence
            result["memory_sources_available"] = 1
        except ImportError:
            pass
        return result

    def collect_capability_gaps(self) -> dict:
        """Coleta dados de capability gaps (P22)."""
        return {"open_capability_gaps": 0}

    def collect_autonomous(self) -> dict:
        """Coleta dados de runs autonomas (P23)."""
        return {"autonomous_runs_active": 0, "autonomous_runs_paused": 0}

    def collect_system_health(self) -> dict:
        """Coleta dados de saude do sistema."""
        result = {
            "disk_percent_free": 0.0,
            "containers_healthy": 0,
            "containers_unhealthy": 0,
        }
        try:
            import shutil
            usage = shutil.disk_usage("/")
            result["disk_percent_free"] = round(
                (usage.free / usage.total) * 100, 1
            )
        except Exception:
            result["disk_percent_free"] = -1.0
        return result

    def collect_module_health(self) -> dict:
        """Varre modulos conhecidos e verifica saude."""
        MODULES_TO_CHECK = [
            ("P0", "src.cli"),
            ("P4", "src.memory_pack"),
            ("P8", "src.publisher_argos"),
            ("P13", "src.analytics"),
            ("P16", "src.observability_local"),
            ("P17", "src.delivery_portal"),
            ("P18", "src.governance"),
            ("P19", "src.campaign_manager"),
            ("P20", "src.omnis_supreme"),
            ("P21", "src.memory_intel"),
            ("P22", "src.capability_forge_real"),
            ("P23", "src.autonomous_execution"),
            ("P24", "src.live_cockpit"),
        ]
        modules = []
        for p_num, namespace in MODULES_TO_CHECK:
            m = CockpitModule.new(p_num, namespace)
            try:
                __import__(namespace)
                m.imports_ok = True
                m.status = "healthy"
            except ImportError:
                m.status = "unknown"
                m.alerts.append(f"Module {p_num} ({namespace}) not importable")
            modules.append(m)
        return {"modules": modules}
