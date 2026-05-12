"""P14 Finance — deterministic services (zero LLM, zero network, zero DB, stdlib only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from src.finance.errors import (
    ApprovalRequiredError,
    BudgetExceededError,
    FinanceError,
    ForecastError,
    InvalidCommissionError,
    InvalidCostError,
    InvalidROIError,
    ValidationError,
)
from src.finance.models import (
    VALID_COST_CATEGORIES,
    VALID_FORECAST_METHODS,
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
    _decimal,
    _now_iso,
    _short_id,
)


# ═══════════════════════════════════════════════════════════════
# ValidationResult
# ═══════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    """Composite result for finance input validation."""
    valid: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.valid and len(self.issues) == 0

    @classmethod
    def success(cls, warnings: list[str] | None = None) -> ValidationResult:
        return cls(valid=True, warnings=warnings or [])

    @classmethod
    def failure(cls, issues: list[str]) -> ValidationResult:
        return cls(valid=False, issues=issues)


# ═══════════════════════════════════════════════════════════════
# Standalone functions
# ═══════════════════════════════════════════════════════════════

def calculate_roi(
    total_revenue_brl: float | Decimal | str,
    total_cost_brl: float | Decimal | str,
    title: str = "ROI Summary",
    reference_period: str = "current_month",
) -> ROISummary:
    """Calculate ROI from revenue and cost totals. Returns ROISummary."""
    return ROISummary.new(
        title=title,
        total_revenue_brl=total_revenue_brl,
        total_cost_brl=total_cost_brl,
        reference_period=reference_period,
    )


def forecast_revenue(
    title: str,
    historical_totals: list[float | Decimal | str],
    method: str = "linear",
    period_months: int = 3,
    confidence_pct: float | Decimal | str = 80.0,
) -> ForecastPlan:
    """Generate a revenue forecast from historical data. Returns ForecastPlan."""
    return ForecastPlan.new(
        title=title,
        method=method,
        historical_totals=historical_totals,
        period_months=period_months,
        confidence_pct=confidence_pct,
    )


def apply_commission_rule(
    rule: CommissionRule,
    revenue_brl: float | Decimal | str,
) -> dict[str, Any]:
    """Apply a commission rule to a revenue amount. Returns dict with result."""
    rev = _decimal(revenue_brl)
    commission = rule.apply(rev)
    return {
        "rule_id": rule.id,
        "rule_name": rule.name,
        "tier_name": rule.tier_name,
        "revenue_brl": str(rev),
        "rate_pct": str(rule.rate_pct),
        "commission_brl": str(commission),
        "approval_required": rule.approval_required,
    }


def build_budget_guard(
    name: str,
    budget_limit_brl: float | Decimal | str,
    reference_month: str,
    category: str = "other",
    spent_brl: float | Decimal | str = 0,
    approval_required: bool = True,
) -> BudgetGuard:
    """Build a budget guard with approval flags. Returns BudgetGuard."""
    return BudgetGuard.new(
        name=name,
        budget_limit_brl=budget_limit_brl,
        reference_month=reference_month,
        category=category,
        spent_brl=spent_brl,
        approval_required=approval_required,
    )


def build_finance_report(
    title: str,
    reference_period: str,
    revenue_records: list[RevenueRecord],
    cost_records: list[CostRecord],
    budget_guards: list[BudgetGuard] | None = None,
    goals: list[dict[str, str]] | None = None,
    roi_summaries: list[ROISummary] | None = None,
    approval_required: bool = False,
) -> FinanceReport:
    """Build a finance report from revenue and cost records. Returns FinanceReport."""
    total_rev = sum((r.amount_brl for r in revenue_records), Decimal("0"))
    total_cost = sum((c.amount_brl for c in cost_records), Decimal("0"))

    alerts: list[str] = []
    for guard in (budget_guards or []):
        if guard.is_over_budget:
            alerts.append(
                f"BUDGET_EXCEEDED: {guard.name} — limit R$ {guard.budget_limit_brl}, "
                f"spent R$ {guard.spent_brl} ({guard.usage_pct}%)"
            )
    if total_cost > total_rev and total_rev > 0:
        alerts.append("CASH_ALERT: total costs exceed total revenue.")

    risk_flags: list[RiskFlag] = []
    for c in cost_records:
        for rf in c.risk_flags:
            if rf not in risk_flags:
                risk_flags.append(rf)

    return FinanceReport.new(
        title=title,
        reference_period=reference_period,
        total_revenue_brl=total_rev,
        total_cost_brl=total_cost,
        budget_guards=budget_guards,
        goals=goals,
        alerts=alerts,
        roi_summaries=roi_summaries,
        risk_flags=risk_flags,
        approval_required=approval_required,
    )


def validate_finance_inputs(
    revenue_records: list[RevenueRecord],
    cost_records: list[CostRecord],
) -> ValidationResult:
    """Validate finance record lists. Returns ValidationResult."""
    issues: list[str] = []
    warnings: list[str] = []

    if not revenue_records and not cost_records:
        warnings.append("No revenue or cost records provided.")

    for i, r in enumerate(revenue_records):
        if r.amount_brl == 0:
            warnings.append(f"Revenue {r.id} has zero amount.")
        if r.category not in VALID_REVENUE_CATEGORIES:
            issues.append(f"Revenue {r.id} has invalid category '{r.category}'.")

    for i, c in enumerate(cost_records):
        if c.amount_brl == 0:
            warnings.append(f"Cost {c.id} has zero amount.")
        if c.category not in VALID_COST_CATEGORIES:
            issues.append(f"Cost {c.id} has invalid category '{c.category}'.")

    if issues:
        return ValidationResult.failure(issues)
    if warnings:
        return ValidationResult.success(warnings)
    return ValidationResult.success()


# ═══════════════════════════════════════════════════════════════
# FinancePlanner
# ═══════════════════════════════════════════════════════════════

class FinancePlanner:
    """Deterministic finance planner — dry-run by default.

    Plans revenue, costs, budget guards, commissions, forecasts,
    and builds finance reports. Zero LLM. Zero network. Zero database.
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._revenue_records: list[RevenueRecord] = []
        self._cost_records: list[CostRecord] = []
        self._commission_rules: list[CommissionRule] = []
        self._budget_guards: list[BudgetGuard] = []
        self._forecast_plans: list[ForecastPlan] = []
        self._roi_summaries: list[ROISummary] = []
        self._finance_reports: list[FinanceReport] = []

    # ── Revenue ───────────────────────────────────────────────

    def record_revenue(
        self,
        source: str,
        description: str,
        amount_brl: float | Decimal | str,
        category: str,
        reference_month: str,
        client: str | None = None,
    ) -> RevenueRecord:
        record = RevenueRecord.new(
            source=source,
            description=description,
            amount_brl=amount_brl,
            category=category,
            reference_month=reference_month,
            client=client,
            dry_run=self.dry_run,
        )
        self._revenue_records.append(record)
        return record

    # ── Cost ──────────────────────────────────────────────────

    def record_cost(
        self,
        description: str,
        amount_brl: float | Decimal | str,
        category: str,
        reference_month: str,
        vendor: str | None = None,
        risk_flags: list[RiskFlag] | None = None,
    ) -> CostRecord:
        record = CostRecord.new(
            description=description,
            amount_brl=amount_brl,
            category=category,
            reference_month=reference_month,
            vendor=vendor,
            risk_flags=risk_flags,
            dry_run=self.dry_run,
        )
        self._cost_records.append(record)
        return record

    # ── Commission ────────────────────────────────────────────

    def define_commission_rule(
        self,
        name: str,
        rate_pct: float | Decimal | str,
        min_revenue_brl: float | Decimal | str = 0,
        max_revenue_brl: float | Decimal | str | None = None,
        tier_name: str = "default",
        approval_required: bool = False,
    ) -> CommissionRule:
        rule = CommissionRule.new(
            name=name,
            rate_pct=rate_pct,
            min_revenue_brl=min_revenue_brl,
            max_revenue_brl=max_revenue_brl,
            tier_name=tier_name,
            approval_required=approval_required,
        )
        self._commission_rules.append(rule)
        return rule

    def compute_commissions(
        self,
        revenue_brl: float | Decimal | str,
    ) -> list[dict[str, Any]]:
        rev = _decimal(revenue_brl)
        results: list[dict[str, Any]] = []
        for rule in self._commission_rules:
            if rule.applies_to(rev):
                results.append(apply_commission_rule(rule, rev))
        return results

    # ── Budget Guard ──────────────────────────────────────────

    def set_budget_guard(
        self,
        name: str,
        budget_limit_brl: float | Decimal | str,
        reference_month: str,
        category: str = "other",
        spent_brl: float | Decimal | str = 0,
        approval_required: bool = True,
    ) -> BudgetGuard:
        guard = BudgetGuard.new(
            name=name,
            budget_limit_brl=budget_limit_brl,
            reference_month=reference_month,
            category=category,
            spent_brl=spent_brl,
            approval_required=approval_required,
        )
        self._budget_guards.append(guard)
        return guard

    def check_budget(self, guard: BudgetGuard) -> None:
        if guard.is_over_budget:
            raise BudgetExceededError(
                f"Budget '{guard.name}' exceeded: R$ {guard.spent_brl} / "
                f"R$ {guard.budget_limit_brl} ({guard.usage_pct}%)"
            )

    # ── Forecast ──────────────────────────────────────────────

    def create_forecast(
        self,
        title: str,
        historical_totals: list[float | Decimal | str],
        method: str = "linear",
        period_months: int = 3,
    ) -> ForecastPlan:
        plan = ForecastPlan.new(
            title=title,
            method=method,
            historical_totals=historical_totals,
            period_months=period_months,
        )
        self._forecast_plans.append(plan)
        return plan

    def forecast_with_sensitivity(
        self,
        title: str,
        historical_totals: list[float | Decimal | str],
        method: str = "linear",
        period_months: int = 3,
    ) -> ForecastPlan:
        plan = ForecastPlan.new(
            title=title,
            method=method,
            historical_totals=historical_totals,
            period_months=period_months,
            confidence_pct=70.0,
            risk_flags=[RiskFlag.FORECAST_SENSITIVE],
            approval_required=True,
        )
        self._forecast_plans.append(plan)
        return plan

    # ── ROI ───────────────────────────────────────────────────

    def compute_roi(
        self,
        title: str = "ROI Summary",
        reference_period: str = "current_month",
    ) -> ROISummary:
        total_rev = sum((r.amount_brl for r in self._revenue_records), Decimal("0"))
        total_cost = sum((c.amount_brl for c in self._cost_records), Decimal("0"))
        summary = ROISummary.new(
            title=title,
            total_revenue_brl=total_rev,
            total_cost_brl=total_cost,
            reference_period=reference_period,
            revenue_records=len(self._revenue_records),
            cost_records=len(self._cost_records),
        )
        self._roi_summaries.append(summary)
        return summary

    # ── Report ────────────────────────────────────────────────

    def build_report(
        self,
        title: str,
        reference_period: str = "current_month",
        goals: list[dict[str, str]] | None = None,
        approval_required: bool = False,
    ) -> FinanceReport:
        report = build_finance_report(
            title=title,
            reference_period=reference_period,
            revenue_records=self._revenue_records,
            cost_records=self._cost_records,
            budget_guards=self._budget_guards,
            goals=goals,
            roi_summaries=self._roi_summaries,
            approval_required=approval_required,
        )
        self._finance_reports.append(report)
        return report

    # ── Validate ──────────────────────────────────────────────

    def validate(self) -> ValidationResult:
        return validate_finance_inputs(self._revenue_records, self._cost_records)

    # ── Inventory ─────────────────────────────────────────────

    def list_revenue(self) -> list[RevenueRecord]:
        return list(self._revenue_records)

    def list_costs(self) -> list[CostRecord]:
        return list(self._cost_records)

    def list_budget_guards(self) -> list[BudgetGuard]:
        return list(self._budget_guards)

    def list_forecasts(self) -> list[ForecastPlan]:
        return list(self._forecast_plans)

    def list_roi_summaries(self) -> list[ROISummary]:
        return list(self._roi_summaries)

    def list_reports(self) -> list[FinanceReport]:
        return list(self._finance_reports)

    @property
    def revenue_count(self) -> int:
        return len(self._revenue_records)

    @property
    def cost_count(self) -> int:
        return len(self._cost_records)

    @property
    def total_revenue(self) -> Decimal:
        return sum((r.amount_brl for r in self._revenue_records), Decimal("0"))

    @property
    def total_cost(self) -> Decimal:
        return sum((c.amount_brl for c in self._cost_records), Decimal("0"))

    @property
    def net_result(self) -> Decimal:
        return self.total_revenue - self.total_cost
