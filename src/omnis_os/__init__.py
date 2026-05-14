"""P29 OMNIS OS Layer — unified operating system for all OMNIS modules."""
from src.omnis_os.models import (
    ModuleHealth, ModuleInfo, OmnisEvent, KernelConfig, BootstrapResult,
    STATUS_REGISTERED, STATUS_ACTIVE, STATUS_DEGRADED, STATUS_INACTIVE, STATUS_UNKNOWN,
    MODULE_STATUSES, HEALTHY, HEALTH_DEGRADED, HEALTH_ERROR, HEALTH_UNKNOWN,
)
from src.omnis_os.errors import (
    OsError, ModuleNotFoundError, DependencyCycleError, BootstrapError,
    HealthCheckError, EventBusError, KernelError,
)
from src.omnis_os.module_contract import OmnisModule
from src.omnis_os.registry import ModuleRegistry
from src.omnis_os.legacy_wrapper import LegacyModuleWrapper
from src.omnis_os.dependency import resolve_order, detect_cycles, validate_dependencies
from src.omnis_os.event_bus import EventBus
from src.omnis_os.health_monitor import HealthMonitor
from src.omnis_os.kernel import OmnisKernel

__all__ = [
    # Models
    "ModuleHealth", "ModuleInfo", "OmnisEvent", "KernelConfig", "BootstrapResult",
    # Status constants
    "STATUS_REGISTERED", "STATUS_ACTIVE", "STATUS_DEGRADED", "STATUS_INACTIVE", "STATUS_UNKNOWN",
    "MODULE_STATUSES",
    # Health constants
    "HEALTHY", "HEALTH_DEGRADED", "HEALTH_ERROR", "HEALTH_UNKNOWN",
    # Errors
    "OsError", "ModuleNotFoundError", "DependencyCycleError", "BootstrapError",
    "HealthCheckError", "EventBusError", "KernelError",
    # Core
    "OmnisModule", "ModuleRegistry", "LegacyModuleWrapper",
    "resolve_order", "detect_cycles", "validate_dependencies",
    "EventBus", "HealthMonitor", "OmnisKernel",
]
