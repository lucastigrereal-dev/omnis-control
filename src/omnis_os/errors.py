"""P29 OMNIS OS Layer — error hierarchy."""


class OsError(Exception):
    """Base error for P29 OMNIS OS."""
    pass


class ModuleNotFoundError(OsError):
    """Module not found in registry."""
    pass


class DependencyCycleError(OsError):
    """Circular dependency detected."""
    pass


class BootstrapError(OsError):
    """Error during system bootstrap."""
    pass


class HealthCheckError(OsError):
    """Error during health check execution."""
    pass


class EventBusError(OsError):
    """Error in event bus operations."""
    pass


class KernelError(OsError):
    """Error in kernel operations."""
    pass
