"""Mission Builder errors."""


class IntentUnknownError(ValueError):
    """Raised when intent cannot be detected from the request."""


class MissionPlanError(ValueError):
    """Raised when plan generation fails."""


class MissionPackageError(IOError):
    """Raised when package creation fails."""
