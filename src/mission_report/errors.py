"""Mission Report errors."""


class MissionNotFoundError(FileNotFoundError):
    """Raised when the mission package directory does not exist."""


class MissionReportError(IOError):
    """Raised when report creation fails."""


class InvalidOutcomeError(ValueError):
    """Raised when outcome is not one of the valid values."""
