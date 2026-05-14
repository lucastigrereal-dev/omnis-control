"""P28 Self-Improvement Loop — error hierarchy."""


class ImprovementError(Exception):
    """Base error for P28 self-improvement."""
    pass


class AnalysisError(ImprovementError):
    """Error during feedback analysis."""
    pass


class ProposalError(ImprovementError):
    """Error during proposal generation."""
    pass


class ExecutionError(ImprovementError):
    """Error during improvement execution."""
    pass


class MeasurementError(ImprovementError):
    """Error during impact measurement."""
    pass


class InsufficientDataError(AnalysisError):
    """Not enough feedback data to analyze."""
    pass


class RollbackError(ImprovementError):
    """Error during rollback of a change."""
    pass
