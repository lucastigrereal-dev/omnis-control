"""P24 Live Cockpit Supreme — Core models."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── Cockpit Module ────────────────────────────────────────────────────────────


@dataclass
class CockpitModule:
    """Registro de um modulo no cockpit."""
    module_name: str
    namespace: str
    status: str = "unknown"
    test_count: int = 0
    test_pass_rate: float = 0.0
    last_validated: str = ""
    imports_ok: bool = False
    alerts: list[str] = field(default_factory=list)

    @classmethod
    def new(cls, module_name: str, namespace: str) -> "CockpitModule":
        return cls(
            module_name=module_name,
            namespace=namespace,
            last_validated=_now_iso(),
        )

    @property
    def is_healthy(self) -> bool:
        return self.status == "healthy"

    @property
    def is_degraded(self) -> bool:
        return self.status == "degraded"

    @property
    def is_error(self) -> bool:
        return self.status == "error"

    def to_dict(self) -> dict:
        return {
            "module_name": self.module_name,
            "namespace": self.namespace,
            "status": self.status,
            "test_count": self.test_count,
            "test_pass_rate": self.test_pass_rate,
            "last_validated": self.last_validated,
            "imports_ok": self.imports_ok,
            "alerts": self.alerts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CockpitModule":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Cockpit Snapshot ─────────────────────────────────────────────────────────


@dataclass
class CockpitSnapshot:
    """Snapshot completo do ecossistema OMNIS."""
    snapshot_id: str = field(default_factory=lambda: _new_id("ckp"))
    generated_at: str = field(default_factory=_now_iso)

    # Missoes
    active_missions: list[dict] = field(default_factory=list)
    missions_today: int = 0
    missions_completed_today: int = 0
    pending_approvals: int = 0

    # Pipeline
    active_campaigns: int = 0
    pending_deliveries: int = 0
    publish_queue_size: int = 0

    # Saude
    modules_healthy: int = 0
    modules_total: int = 0
    tests_passing: int = 0
    tests_failing: int = 0
    alerts: list[dict] = field(default_factory=list)
    modules: list[CockpitModule] = field(default_factory=list)

    # Autonomo
    autonomous_runs_active: int = 0
    autonomous_runs_paused: int = 0

    # Memoria / Aprendizado
    memory_sources_available: int = 0
    recent_learnings: list[str] = field(default_factory=list)
    open_capability_gaps: int = 0

    # Sistema
    disk_percent_free: float = 0.0
    containers_healthy: int = 0
    containers_unhealthy: int = 0

    # Meta
    collection_errors: list[str] = field(default_factory=list)
    collection_warnings: list[str] = field(default_factory=list)

    @classmethod
    def new(cls) -> "CockpitSnapshot":
        return cls()

    @property
    def is_complete(self) -> bool:
        return len(self.collection_errors) == 0

    @property
    def overall_status(self) -> str:
        if self.collection_errors:
            return "degraded"
        if self.alerts:
            criticals = [a for a in self.alerts if a.get("severity") == "critical"]
            if criticals:
                return "critical"
        if self.modules_total > 0 and self.modules_healthy < self.modules_total:
            return "degraded"
        return "healthy"

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "generated_at": self.generated_at,
            "active_missions": self.active_missions,
            "missions_today": self.missions_today,
            "missions_completed_today": self.missions_completed_today,
            "pending_approvals": self.pending_approvals,
            "active_campaigns": self.active_campaigns,
            "pending_deliveries": self.pending_deliveries,
            "publish_queue_size": self.publish_queue_size,
            "modules_healthy": self.modules_healthy,
            "modules_total": self.modules_total,
            "tests_passing": self.tests_passing,
            "tests_failing": self.tests_failing,
            "alerts": self.alerts,
            "modules": [m.to_dict() for m in self.modules],
            "autonomous_runs_active": self.autonomous_runs_active,
            "autonomous_runs_paused": self.autonomous_runs_paused,
            "memory_sources_available": self.memory_sources_available,
            "recent_learnings": self.recent_learnings,
            "open_capability_gaps": self.open_capability_gaps,
            "disk_percent_free": self.disk_percent_free,
            "containers_healthy": self.containers_healthy,
            "containers_unhealthy": self.containers_unhealthy,
            "collection_errors": self.collection_errors,
            "collection_warnings": self.collection_warnings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CockpitSnapshot":
        s = cls()
        for field_name in cls.__dataclass_fields__:
            if field_name in data:
                setattr(s, field_name, data[field_name])
        s.modules = [CockpitModule.from_dict(m) for m in data.get("modules", [])]
        return s
