"""P14 Finance Skeleton — deterministic finance package.

Scope:
- Revenue and cost recording (dry-run only)
- Budget guard with approval flags
- Commission rule definition and application
- ROI calculation (deterministic)
- Revenue/cost forecast (linear, moving average, seasonal naive)
- Finance report aggregation with alerts
- Finance input validation

Constraints: zero LLM, zero network, zero Docker, zero database.
No real payment. No real billing. No external API. No CLI integration.
"""

from src.finance.errors import (
    ApprovalRequiredError,
    BudgetExceededError,
    FinanceError,
    ForecastError,
    InvalidCommissionError,
    InvalidCostError,
    InvalidRevenueError,
    InvalidROIError,
    ReportError,
    ValidationError,
)
from src.finance.models import (
    VALID_COST_CATEGORIES,
    VALID_FORECAST_METHODS,
    VALID_REPORT_PERIODS,
    VALID_REVENUE_CATEGORIES,
    ApprovalStatus,
    BudgetGuard,
    CommissionRule,
    CostRecord,
    FinanceReport,
    ForecastPlan,
    RevenueRecord,
    RiskFlag,
    ROISummary,
)
from src.finance.service import (
    FinancePlanner,
    ValidationResult,
    apply_commission_rule,
    build_budget_guard,
    build_finance_report,
    calculate_roi,
    forecast_revenue,
    validate_finance_inputs,
)

__all__ = [
    # Models
    "RevenueRecord",
    "CostRecord",
    "CommissionRule",
    "BudgetGuard",
    "ROISummary",
    "ForecastPlan",
    "FinanceReport",
    # Enums
    "RiskFlag",
    "ApprovalStatus",
    # Constants
    "VALID_REVENUE_CATEGORIES",
    "VALID_COST_CATEGORIES",
    "VALID_FORECAST_METHODS",
    "VALID_REPORT_PERIODS",
    # Service
    "FinancePlanner",
    "ValidationResult",
    # Functions
    "calculate_roi",
    "forecast_revenue",
    "apply_commission_rule",
    "build_budget_guard",
    "build_finance_report",
    "validate_finance_inputs",
    # Errors
    "FinanceError",
    "InvalidRevenueError",
    "InvalidCostError",
    "InvalidCommissionError",
    "BudgetExceededError",
    "ForecastError",
    "InvalidROIError",
    "ReportError",
    "ApprovalRequiredError",
    "ValidationError",
]
