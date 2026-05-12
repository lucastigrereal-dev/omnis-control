"""P14 Finance — error hierarchy."""


class FinanceError(Exception):
    """Base error for the finance package."""
    pass


class InvalidRevenueError(FinanceError):
    """Revenue record fails validation."""
    pass


class InvalidCostError(FinanceError):
    """Cost record fails validation."""
    pass


class InvalidCommissionError(FinanceError):
    """Commission rule fails validation."""
    pass


class BudgetExceededError(FinanceError):
    """Budget limit exceeded — requires approval."""
    pass


class ForecastError(FinanceError):
    """Forecast plan fails validation."""
    pass


class InvalidROIError(FinanceError):
    """ROI calculation inputs are invalid."""
    pass


class ReportError(FinanceError):
    """Finance report fails validation."""
    pass


class ApprovalRequiredError(FinanceError):
    """Action requires approval before execution."""
    pass


class ValidationError(FinanceError):
    """Finance input validation failed."""
    pass
