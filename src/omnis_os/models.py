"""P29 OMNIS OS Layer — core models."""
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


# ── Module statuses ───────────────────────────────────────────────
STATUS_REGISTERED = "registered"
STATUS_ACTIVE = "active"
STATUS_DEGRADED = "degraded"
STATUS_INACTIVE = "inactive"
STATUS_UNKNOWN = "unknown"
MODULE_STATUSES = [STATUS_REGISTERED, STATUS_ACTIVE, STATUS_DEGRADED, STATUS_INACTIVE, STATUS_UNKNOWN]

# ── Health statuses ───────────────────────────────────────────────
HEALTHY = "healthy"
HEALTH_DEGRADED = "degraded"
HEALTH_ERROR = "error"
HEALTH_UNKNOWN = "unknown"


# ── ModuleHealth ──────────────────────────────────────────────────

@dataclass
class ModuleHealth:
    module_name: str
    status: str = HEALTHY
    imports_ok: bool = True
    tests_passing: int = 0
    tests_total: int = 0
    version: str = "0.0.0"
    last_checked: str = field(default_factory=_now_iso)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def new(cls, module_name: str, status: str = HEALTHY,
            imports_ok: bool = True, tests_passing: int = 0,
            tests_total: int = 0, version: str = "0.0.0",
            errors: Optional[list[str]] = None,
            warnings: Optional[list[str]] = None) -> "ModuleHealth":
        return cls(
            module_name=module_name, status=status, imports_ok=imports_ok,
            tests_passing=tests_passing, tests_total=tests_total,
            version=version, errors=errors or [], warnings=warnings or [],
        )

    def to_dict(self) -> dict:
        return {
            "module_name": self.module_name, "status": self.status,
            "imports_ok": self.imports_ok, "tests_passing": self.tests_passing,
            "tests_total": self.tests_total, "version": self.version,
            "last_checked": self.last_checked, "errors": self.errors,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ModuleHealth":
        return cls(
            module_name=d.get("module_name", ""), status=d.get("status", HEALTHY),
            imports_ok=d.get("imports_ok", True), tests_passing=d.get("tests_passing", 0),
            tests_total=d.get("tests_total", 0), version=d.get("version", "0.0.0"),
            last_checked=d.get("last_checked", ""), errors=d.get("errors", []),
            warnings=d.get("warnings", []),
        )

    @property
    def is_healthy(self) -> bool:
        return self.status == HEALTHY and self.imports_ok

    @property
    def test_pass_rate(self) -> float:
        if self.tests_total == 0:
            return 1.0
        return self.tests_passing / self.tests_total


# ── ModuleInfo ────────────────────────────────────────────────────

@dataclass
class ModuleInfo:
    module_id: str
    name: str
    namespace: str = ""
    version: str = "0.0.0"
    status: str = STATUS_REGISTERED
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    health: Optional[ModuleHealth] = None
    is_legacy: bool = False
    registered_at: str = field(default_factory=_now_iso)
    last_health_check: str = ""

    @classmethod
    def new(cls, name: str, namespace: str = "", version: str = "0.0.0",
            dependencies: Optional[list[str]] = None,
            is_legacy: bool = False) -> "ModuleInfo":
        return cls(
            module_id=_short_id("om"), name=name, namespace=namespace,
            version=version, dependencies=dependencies or [],
            is_legacy=is_legacy,
            health=ModuleHealth.new(name, status=HEALTH_UNKNOWN if is_legacy else HEALTHY),
        )

    def to_dict(self) -> dict:
        return {
            "module_id": self.module_id, "name": self.name,
            "namespace": self.namespace, "version": self.version,
            "status": self.status, "dependencies": self.dependencies,
            "dependents": self.dependents,
            "health": self.health.to_dict() if self.health else None,
            "is_legacy": self.is_legacy, "registered_at": self.registered_at,
            "last_health_check": self.last_health_check,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ModuleInfo":
        health_data = d.get("health")
        health = ModuleHealth.from_dict(health_data) if isinstance(health_data, dict) else None
        return cls(
            module_id=d.get("module_id", ""), name=d.get("name", ""),
            namespace=d.get("namespace", ""), version=d.get("version", "0.0.0"),
            status=d.get("status", STATUS_REGISTERED),
            dependencies=d.get("dependencies", []),
            dependents=d.get("dependents", []),
            health=health, is_legacy=d.get("is_legacy", False),
            registered_at=d.get("registered_at", ""),
            last_health_check=d.get("last_health_check", ""),
        )


# ── OmnisEvent ────────────────────────────────────────────────────

@dataclass
class OmnisEvent:
    event_id: str
    event_type: str
    source_module: str
    data: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, event_type: str, source_module: str,
            data: Optional[dict] = None) -> "OmnisEvent":
        return cls(
            event_id=_short_id("ose"), event_type=event_type,
            source_module=source_module, data=data or {},
        )

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id, "event_type": self.event_type,
            "source_module": self.source_module, "data": self.data,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OmnisEvent":
        return cls(
            event_id=d.get("event_id", ""), event_type=d.get("event_type", ""),
            source_module=d.get("source_module", ""), data=d.get("data", {}),
            timestamp=d.get("timestamp", ""),
        )


# ── KernelConfig ──────────────────────────────────────────────────

@dataclass
class KernelConfig:
    scan_paths: list[str] = field(default_factory=lambda: ["src/"])
    health_check_interval_seconds: int = 60
    bootstrap_timeout_seconds: int = 30
    shutdown_timeout_seconds: int = 10
    max_concurrent_health_checks: int = 5

    def to_dict(self) -> dict:
        return {
            "scan_paths": self.scan_paths,
            "health_check_interval_seconds": self.health_check_interval_seconds,
            "bootstrap_timeout_seconds": self.bootstrap_timeout_seconds,
            "shutdown_timeout_seconds": self.shutdown_timeout_seconds,
            "max_concurrent_health_checks": self.max_concurrent_health_checks,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "KernelConfig":
        return cls(
            scan_paths=d.get("scan_paths", ["src/"]),
            health_check_interval_seconds=d.get("health_check_interval_seconds", 60),
            bootstrap_timeout_seconds=d.get("bootstrap_timeout_seconds", 30),
            shutdown_timeout_seconds=d.get("shutdown_timeout_seconds", 10),
            max_concurrent_health_checks=d.get("max_concurrent_health_checks", 5),
        )


# ── BootstrapResult ───────────────────────────────────────────────

@dataclass
class BootstrapResult:
    status: str = "dry_run"
    modules_found: int = 0
    modules_activated: int = 0
    legacy_modules: list[str] = field(default_factory=list)
    cycles_detected: list[list[str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    duration_ms: int = 0

    @classmethod
    def new(cls, modules_found: int = 0, modules_activated: int = 0,
            legacy_modules: Optional[list[str]] = None,
            cycles_detected: Optional[list[list[str]]] = None,
            errors: Optional[list[str]] = None,
            duration_ms: int = 0) -> "BootstrapResult":
        return cls(
            modules_found=modules_found, modules_activated=modules_activated,
            legacy_modules=legacy_modules or [],
            cycles_detected=cycles_detected or [],
            errors=errors or [], duration_ms=duration_ms,
        )

    def to_dict(self) -> dict:
        return {
            "status": self.status, "modules_found": self.modules_found,
            "modules_activated": self.modules_activated,
            "legacy_modules": self.legacy_modules,
            "cycles_detected": self.cycles_detected, "errors": self.errors,
            "duration_ms": self.duration_ms,
        }
