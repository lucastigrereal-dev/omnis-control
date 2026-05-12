"""P14 Finance — deterministic models (dataclasses, stdlib only, Decimal for money)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any


# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

VALID_REVENUE_CATEGORIES = frozenset({
    "collab", "publi", "consulting", "affiliate",
    "product_sale", "subscription", "licensing", "other",
})

VALID_COST_CATEGORIES = frozenset({
    "ads", "tools", "services", "travel",
    "equipment", "taxes", "salary", "marketing",
    "infra", "other",
})

VALID_FORECAST_METHODS = frozenset({
    "linear", "moving_average", "seasonal_naive", "manual",
})

VALID_REPORT_PERIODS = frozenset({
    "daily", "weekly", "monthly", "quarterly", "yearly",
})


class RiskFlag(Enum):
    PAYMENT = "payment"
    BILLING = "billing"
    BUDGET_EXCEEDED = "budget_exceeded"
    FORECAST_SENSITIVE = "forecast_sensitive"


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_REQUIRED = "not_required"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _short_id(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"


def _decimal_or_none(val: float | Decimal | str | None) -> Decimal | None:
    if val is None:
        return None
    return Decimal(str(val))


def _decimal(val: float | Decimal | str) -> Decimal:
    return Decimal(str(val))


# ═══════════════════════════════════════════════════════════════
# Models
# ═══════════════════════════════════════════════════════════════

@dataclass
class RevenueRecord:
    """A single revenue entry — deterministic, dry-run by default."""

    id: str
    source: str
    description: str
    amount_brl: Decimal
    category: str
    recorded_at: str
    reference_month: str
    client: str | None = None
    dry_run: bool = True
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def new(
        cls,
        source: str,
        description: str,
        amount_brl: float | Decimal | str,
        category: str,
        reference_month: str,
        client: str | None = None,
        dry_run: bool = True,
        metadata: dict[str, str] | None = None,
    ) -> RevenueRecord:
        if category not in VALID_REVENUE_CATEGORIES:
            raise ValueError(
                f"Invalid revenue category '{category}'. Valid: {sorted(VALID_REVENUE_CATEGORIES)}"
            )
        amount = _decimal(amount_brl)
        if amount < 0:
            raise ValueError("Revenue amount cannot be negative.")
        return cls(
            id=_short_id("rev_"),
            source=source,
            description=description,
            amount_brl=amount,
            category=category,
            recorded_at=_now_iso(),
            reference_month=reference_month,
            client=client,
            dry_run=dry_run,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "description": self.description,
            "amount_brl": str(self.amount_brl),
            "category": self.category,
            "recorded_at": self.recorded_at,
            "reference_month": self.reference_month,
            "client": self.client,
            "dry_run": self.dry_run,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RevenueRecord:
        return cls(
            id=data["id"],
            source=data["source"],
            description=data["description"],
            amount_brl=_decimal(data["amount_brl"]),
            category=data["category"],
            recorded_at=data.get("recorded_at", _now_iso()),
            reference_month=data["reference_month"],
            client=data.get("client"),
            dry_run=data.get("dry_run", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CostRecord:
    """A single cost/expense entry — deterministic, dry-run by default."""

    id: str
    description: str
    amount_brl: Decimal
    category: str
    vendor: str | None
    recorded_at: str
    reference_month: str
    risk_flags: list[RiskFlag] = field(default_factory=list)
    dry_run: bool = True
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def new(
        cls,
        description: str,
        amount_brl: float | Decimal | str,
        category: str,
        reference_month: str,
        vendor: str | None = None,
        risk_flags: list[RiskFlag] | None = None,
        dry_run: bool = True,
        metadata: dict[str, str] | None = None,
    ) -> CostRecord:
        if category not in VALID_COST_CATEGORIES:
            raise ValueError(
                f"Invalid cost category '{category}'. Valid: {sorted(VALID_COST_CATEGORIES)}"
            )
        amount = _decimal(amount_brl)
        if amount < 0:
            raise ValueError("Cost amount cannot be negative.")
        return cls(
            id=_short_id("cst_"),
            description=description,
            amount_brl=amount,
            category=category,
            vendor=vendor,
            recorded_at=_now_iso(),
            reference_month=reference_month,
            risk_flags=risk_flags or [],
            dry_run=dry_run,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "amount_brl": str(self.amount_brl),
            "category": self.category,
            "vendor": self.vendor,
            "recorded_at": self.recorded_at,
            "reference_month": self.reference_month,
            "risk_flags": [f.value for f in self.risk_flags],
            "dry_run": self.dry_run,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CostRecord:
        return cls(
            id=data["id"],
            description=data["description"],
            amount_brl=_decimal(data["amount_brl"]),
            category=data["category"],
            vendor=data.get("vendor"),
            recorded_at=data.get("recorded_at", _now_iso()),
            reference_month=data["reference_month"],
            risk_flags=[RiskFlag(f) for f in data.get("risk_flags", [])],
            dry_run=data.get("dry_run", True),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CommissionRule:
    """Commission calculation rule — tiered or flat rate."""

    id: str
    name: str
    rate_pct: Decimal
    min_revenue_brl: Decimal
    max_revenue_brl: Decimal | None
    tier_name: str
    approval_required: bool = False
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        name: str,
        rate_pct: float | Decimal | str,
        min_revenue_brl: float | Decimal | str = 0,
        max_revenue_brl: float | Decimal | str | None = None,
        tier_name: str = "default",
        approval_required: bool = False,
    ) -> CommissionRule:
        rate = _decimal(rate_pct)
        if rate < 0 or rate > 100:
            raise ValueError("Commission rate must be between 0 and 100.")
        return cls(
            id=_short_id("com_"),
            name=name,
            rate_pct=rate,
            min_revenue_brl=_decimal(min_revenue_brl),
            max_revenue_brl=_decimal_or_none(max_revenue_brl),
            tier_name=tier_name,
            approval_required=approval_required,
        )

    @property
    def is_tiered(self) -> bool:
        return self.max_revenue_brl is not None

    def applies_to(self, revenue_brl: Decimal) -> bool:
        if revenue_brl < self.min_revenue_brl:
            return False
        if self.max_revenue_brl is not None and revenue_brl > self.max_revenue_brl:
            return False
        return True

    def apply(self, revenue_brl: Decimal) -> Decimal:
        if not self.applies_to(revenue_brl):
            return Decimal("0")
        return (revenue_brl * self.rate_pct / Decimal("100")).quantize(Decimal("0.01"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "rate_pct": str(self.rate_pct),
            "min_revenue_brl": str(self.min_revenue_brl),
            "max_revenue_brl": str(self.max_revenue_brl) if self.max_revenue_brl else None,
            "tier_name": self.tier_name,
            "approval_required": self.approval_required,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CommissionRule:
        return cls(
            id=data["id"],
            name=data["name"],
            rate_pct=_decimal(data["rate_pct"]),
            min_revenue_brl=_decimal(data.get("min_revenue_brl", "0")),
            max_revenue_brl=_decimal_or_none(data.get("max_revenue_brl")),
            tier_name=data.get("tier_name", "default"),
            approval_required=data.get("approval_required", False),
            created_at=data.get("created_at", _now_iso()),
        )


@dataclass
class BudgetGuard:
    """Budget limit with approval flags for critical financial actions."""

    id: str
    name: str
    budget_limit_brl: Decimal
    spent_brl: Decimal
    reference_month: str
    category: str
    approval_required: bool = True
    risk_flags: list[RiskFlag] = field(default_factory=list)
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        name: str,
        budget_limit_brl: float | Decimal | str,
        reference_month: str,
        category: str = "other",
        spent_brl: float | Decimal | str = 0,
        approval_required: bool = True,
        risk_flags: list[RiskFlag] | None = None,
    ) -> BudgetGuard:
        if category not in VALID_COST_CATEGORIES:
            raise ValueError(
                f"Invalid cost category '{category}'. Valid: {sorted(VALID_COST_CATEGORIES)}"
            )
        limit = _decimal(budget_limit_brl)
        if limit < 0:
            raise ValueError("Budget limit cannot be negative.")
        spent = _decimal(spent_brl)
        if spent < 0:
            raise ValueError("Spent amount cannot be negative.")
        return cls(
            id=_short_id("bgt_"),
            name=name,
            budget_limit_brl=limit,
            spent_brl=spent,
            reference_month=reference_month,
            category=category,
            approval_required=approval_required,
            risk_flags=risk_flags or [],
            approval_status=ApprovalStatus.PENDING if approval_required else ApprovalStatus.NOT_REQUIRED,
        )

    @property
    def remaining_brl(self) -> Decimal:
        return self.budget_limit_brl - self.spent_brl

    @property
    def is_over_budget(self) -> bool:
        return self.spent_brl > self.budget_limit_brl

    @property
    def usage_pct(self) -> Decimal:
        if self.budget_limit_brl == 0:
            return Decimal("0")
        return (self.spent_brl / self.budget_limit_brl * Decimal("100")).quantize(Decimal("0.1"))

    def approve(self) -> None:
        self.approval_status = ApprovalStatus.APPROVED

    def reject(self) -> None:
        self.approval_status = ApprovalStatus.REJECTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "budget_limit_brl": str(self.budget_limit_brl),
            "spent_brl": str(self.spent_brl),
            "remaining_brl": str(self.remaining_brl),
            "usage_pct": str(self.usage_pct),
            "is_over_budget": self.is_over_budget,
            "reference_month": self.reference_month,
            "category": self.category,
            "approval_required": self.approval_required,
            "risk_flags": [f.value for f in self.risk_flags],
            "approval_status": self.approval_status.value,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BudgetGuard:
        return cls(
            id=data["id"],
            name=data["name"],
            budget_limit_brl=_decimal(data["budget_limit_brl"]),
            spent_brl=_decimal(data.get("spent_brl", "0")),
            reference_month=data["reference_month"],
            category=data.get("category", "other"),
            approval_required=data.get("approval_required", True),
            risk_flags=[RiskFlag(f) for f in data.get("risk_flags", [])],
            approval_status=ApprovalStatus(data.get("approval_status", "pending")),
            created_at=data.get("created_at", _now_iso()),
        )


@dataclass
class ForecastPlan:
    """Revenue/cost forecast projection — deterministic, method-based."""

    id: str
    title: str
    method: str
    period_months: int
    historical_totals: list[Decimal]
    projected_totals: list[Decimal]
    confidence_pct: Decimal
    risk_flags: list[RiskFlag] = field(default_factory=list)
    approval_required: bool = False
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        title: str,
        method: str,
        historical_totals: list[float | Decimal | str],
        period_months: int = 3,
        confidence_pct: float | Decimal | str = 80.0,
        risk_flags: list[RiskFlag] | None = None,
        approval_required: bool = False,
    ) -> ForecastPlan:
        if method not in VALID_FORECAST_METHODS:
            raise ValueError(
                f"Invalid forecast method '{method}'. Valid: {sorted(VALID_FORECAST_METHODS)}"
            )
        if period_months < 1:
            raise ValueError("Period must be at least 1 month.")
        hist = [_decimal(v) for v in historical_totals]
        if not hist:
            raise ValueError("Historical data cannot be empty.")
        if any(v < 0 for v in hist):
            raise ValueError("Historical values cannot be negative.")

        conf = _decimal(confidence_pct)
        if conf < 0 or conf > 100:
            raise ValueError("Confidence must be between 0 and 100.")

        projected = _forecast_values(hist, method, period_months)
        return cls(
            id=_short_id("fct_"),
            title=title,
            method=method,
            period_months=period_months,
            historical_totals=hist,
            projected_totals=projected,
            confidence_pct=conf,
            risk_flags=risk_flags or [],
            approval_required=approval_required,
        )

    @property
    def historical_avg(self) -> Decimal:
        if not self.historical_totals:
            return Decimal("0")
        total = sum(self.historical_totals)
        return (total / len(self.historical_totals)).quantize(Decimal("0.01"))

    @property
    def projected_total(self) -> Decimal:
        return sum(self.projected_totals).quantize(Decimal("0.01"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "method": self.method,
            "period_months": self.period_months,
            "historical_totals": [str(v) for v in self.historical_totals],
            "historical_avg": str(self.historical_avg),
            "projected_totals": [str(v) for v in self.projected_totals],
            "projected_total": str(self.projected_total),
            "confidence_pct": str(self.confidence_pct),
            "risk_flags": [f.value for f in self.risk_flags],
            "approval_required": self.approval_required,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ForecastPlan:
        return cls(
            id=data["id"],
            title=data["title"],
            method=data["method"],
            historical_totals=[_decimal(v) for v in data.get("historical_totals", [])],
            period_months=data.get("period_months", 3),
            projected_totals=[_decimal(v) for v in data.get("projected_totals", [])],
            confidence_pct=_decimal(data.get("confidence_pct", "80")),
            risk_flags=[RiskFlag(f) for f in data.get("risk_flags", [])],
            approval_required=data.get("approval_required", False),
            created_at=data.get("created_at", _now_iso()),
        )


@dataclass
class ROISummary:
    """ROI calculation result — total revenue, cost, net margin, and ratio."""

    id: str
    title: str
    total_revenue_brl: Decimal
    total_cost_brl: Decimal
    net_profit_brl: Decimal
    roi_pct: Decimal
    reference_period: str
    revenue_records: int = 0
    cost_records: int = 0
    risk_flags: list[RiskFlag] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        title: str,
        total_revenue_brl: float | Decimal | str,
        total_cost_brl: float | Decimal | str,
        reference_period: str,
        revenue_records: int = 0,
        cost_records: int = 0,
        risk_flags: list[RiskFlag] | None = None,
    ) -> ROISummary:
        rev = _decimal(total_revenue_brl)
        cost = _decimal(total_cost_brl)
        if rev < 0 or cost < 0:
            raise ValueError("Revenue and cost cannot be negative.")

        net = rev - cost
        if cost == 0:
            roi = Decimal("0") if rev == 0 else Decimal("999999")  # infinite ROI marker
        else:
            roi = ((net / cost) * Decimal("100")).quantize(Decimal("0.01"))

        return cls(
            id=_short_id("roi_"),
            title=title,
            total_revenue_brl=rev,
            total_cost_brl=cost,
            net_profit_brl=net,
            roi_pct=roi,
            reference_period=reference_period,
            revenue_records=revenue_records,
            cost_records=cost_records,
            risk_flags=risk_flags or [],
        )

    @property
    def is_profitable(self) -> bool:
        return self.net_profit_brl > 0

    @property
    def profit_margin_pct(self) -> Decimal:
        if self.total_revenue_brl == 0:
            return Decimal("0")
        return (self.net_profit_brl / self.total_revenue_brl * Decimal("100")).quantize(Decimal("0.01"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "total_revenue_brl": str(self.total_revenue_brl),
            "total_cost_brl": str(self.total_cost_brl),
            "net_profit_brl": str(self.net_profit_brl),
            "roi_pct": str(self.roi_pct),
            "profit_margin_pct": str(self.profit_margin_pct),
            "is_profitable": self.is_profitable,
            "reference_period": self.reference_period,
            "revenue_records": self.revenue_records,
            "cost_records": self.cost_records,
            "risk_flags": [f.value for f in self.risk_flags],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ROISummary:
        return cls(
            id=data["id"],
            title=data["title"],
            total_revenue_brl=_decimal(data["total_revenue_brl"]),
            total_cost_brl=_decimal(data["total_cost_brl"]),
            net_profit_brl=_decimal(data.get("net_profit_brl", "0")),
            roi_pct=_decimal(data.get("roi_pct", "0")),
            reference_period=data["reference_period"],
            revenue_records=data.get("revenue_records", 0),
            cost_records=data.get("cost_records", 0),
            risk_flags=[RiskFlag(f) for f in data.get("risk_flags", [])],
            created_at=data.get("created_at", _now_iso()),
        )


@dataclass
class FinanceReport:
    """Aggregated finance summary — revenue, cost, net, goals, alerts."""

    id: str
    title: str
    reference_period: str
    total_revenue_brl: Decimal
    total_cost_brl: Decimal
    net_result_brl: Decimal
    budget_guards: list[BudgetGuard] = field(default_factory=list)
    goals: list[dict[str, str]] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)
    roi_summaries: list[ROISummary] = field(default_factory=list)
    risk_flags: list[RiskFlag] = field(default_factory=list)
    approval_required: bool = False
    approval_status: ApprovalStatus = ApprovalStatus.NOT_REQUIRED
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        title: str,
        reference_period: str,
        total_revenue_brl: float | Decimal | str,
        total_cost_brl: float | Decimal | str,
        budget_guards: list[BudgetGuard] | None = None,
        goals: list[dict[str, str]] | None = None,
        alerts: list[str] | None = None,
        roi_summaries: list[ROISummary] | None = None,
        risk_flags: list[RiskFlag] | None = None,
        approval_required: bool = False,
    ) -> FinanceReport:
        rev = _decimal(total_revenue_brl)
        cost = _decimal(total_cost_brl)
        return cls(
            id=_short_id("fnr_"),
            title=title,
            reference_period=reference_period,
            total_revenue_brl=rev,
            total_cost_brl=cost,
            net_result_brl=(rev - cost).quantize(Decimal("0.01")),
            budget_guards=budget_guards or [],
            goals=goals or [],
            alerts=alerts or [],
            roi_summaries=roi_summaries or [],
            risk_flags=risk_flags or [],
            approval_required=approval_required,
            approval_status=ApprovalStatus.PENDING if approval_required else ApprovalStatus.NOT_REQUIRED,
        )

    @property
    def is_net_positive(self) -> bool:
        return self.net_result_brl > 0

    @property
    def over_budget_count(self) -> int:
        return sum(1 for g in self.budget_guards if g.is_over_budget)

    def approve(self) -> None:
        self.approval_status = ApprovalStatus.APPROVED

    def reject(self) -> None:
        self.approval_status = ApprovalStatus.REJECTED

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "reference_period": self.reference_period,
            "total_revenue_brl": str(self.total_revenue_brl),
            "total_cost_brl": str(self.total_cost_brl),
            "net_result_brl": str(self.net_result_brl),
            "is_net_positive": self.is_net_positive,
            "over_budget_count": self.over_budget_count,
            "budget_guards": [g.to_dict() for g in self.budget_guards],
            "goals": self.goals,
            "alerts": self.alerts,
            "roi_summaries": [r.to_dict() for r in self.roi_summaries],
            "risk_flags": [f.value for f in self.risk_flags],
            "approval_required": self.approval_required,
            "approval_status": self.approval_status.value,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FinanceReport:
        return cls(
            id=data["id"],
            title=data["title"],
            reference_period=data["reference_period"],
            total_revenue_brl=_decimal(data["total_revenue_brl"]),
            total_cost_brl=_decimal(data["total_cost_brl"]),
            net_result_brl=_decimal(data.get("net_result_brl", "0")),
            budget_guards=[BudgetGuard.from_dict(g) for g in data.get("budget_guards", [])],
            goals=data.get("goals", []),
            alerts=data.get("alerts", []),
            roi_summaries=[ROISummary.from_dict(r) for r in data.get("roi_summaries", [])],
            risk_flags=[RiskFlag(f) for f in data.get("risk_flags", [])],
            approval_required=data.get("approval_required", False),
            approval_status=ApprovalStatus(data.get("approval_status", "not_required")),
            created_at=data.get("created_at", _now_iso()),
        )


# ═══════════════════════════════════════════════════════════════
# Forecast helpers
# ═══════════════════════════════════════════════════════════════

def _forecast_values(historical: list[Decimal], method: str, months: int) -> list[Decimal]:
    if method == "manual":
        return [Decimal("0")] * months

    if method == "linear":
        return _forecast_linear(historical, months)

    if method == "moving_average":
        return _forecast_moving_average(historical, months)

    if method == "seasonal_naive":
        return _forecast_seasonal_naive(historical, months)

    return [Decimal("0")] * months


def _forecast_linear(historical: list[Decimal], months: int) -> list[Decimal]:
    n = len(historical)
    if n == 1:
        return [historical[0]] * months

    x_mean = Decimal(str((n - 1) / 2))
    y_mean = sum(historical) / n

    numerator = Decimal("0")
    denominator = Decimal("0")
    for i, y in enumerate(historical):
        x_diff = Decimal(str(i)) - x_mean
        numerator += x_diff * (y - y_mean)
        denominator += x_diff * x_diff

    if denominator == 0:
        slope = Decimal("0")
    else:
        slope = (numerator / denominator).quantize(Decimal("0.0001"))

    result: list[Decimal] = []
    for m in range(1, months + 1):
        val = slope * Decimal(str(n + m - 1)) + (y_mean - slope * x_mean)
        result.append(max(val, Decimal("0")).quantize(Decimal("0.01")))
    return result


def _forecast_moving_average(historical: list[Decimal], months: int) -> list[Decimal]:
    window = min(3, len(historical))
    recent = historical[-window:]
    avg = (sum(recent) / len(recent)).quantize(Decimal("0.01"))
    return [avg] * months


def _forecast_seasonal_naive(historical: list[Decimal], months: int) -> list[Decimal]:
    result: list[Decimal] = []
    n = len(historical)
    for m in range(1, months + 1):
        offset = m % n if n > 0 else 0
        idx = n - offset if offset != 0 else 0
        idx = idx - 1 if offset != 0 else n - 1
        val = historical[idx] if n > 0 else Decimal("0")
        result.append(val)
    return result
