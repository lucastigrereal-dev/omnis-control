"""P25 Multi-Model Orchestration — errors."""


class MultiModelError(Exception):
    """Base error for P25 Multi-Model Orchestration."""
    pass


class ProviderUnavailableError(MultiModelError):
    """Provider is not reachable (health check failed)."""
    pass


class RoutingError(MultiModelError):
    """No suitable model found for the given task."""
    pass


class CostLimitError(MultiModelError):
    """Estimated cost exceeds the task's max_cost_usd limit."""
    pass


class AllModelsExhaustedError(MultiModelError):
    """All models in the fallback chain have failed."""
    pass


class AdapterError(MultiModelError):
    """Adapter failed to execute (bug, not provider failure)."""
    pass


class InvalidModelConfigError(MultiModelError):
    """ModelConfig is invalid or missing required fields."""
    pass
