"""Tests for P14 Finance models."""

from __future__ import annotations

from decimal import Decimal

import pytest

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


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _make_revenue(**kw) -> RevenueRecord:
    return RevenueRecord.new(
        source=kw.pop("source", "Collab Serhs"),
        description=kw.pop("description", "Publi carrossel + stories"),
        amount_brl=kw.pop("amount_brl", "990.00"),
        category=kw.pop("category", "collab"),
        reference_month=kw.pop("reference_month", "2026-05"),
        **kw,
    )


def _make_cost(**kw) -> CostRecord:
    return CostRecord.new(
        description=kw.pop("description", "Meta Ads — campanha Natal"),
        amount_brl=kw.pop("amount_brl", "150.00"),
        category=kw.pop("category", "ads"),
        reference_month=kw.pop("reference_month", "2026-05"),
        **kw,
    )


def _make_commission(**kw) -> CommissionRule:
    return CommissionRule.new(
        name=kw.pop("name", "Growth Tier 1"),
        rate_pct=kw.pop("rate_pct", "10.0"),
        **kw,
    )


def _make_budget_guard(**kw) -> BudgetGuard:
    return BudgetGuard.new(
        name=kw.pop("name", "Ads Budget Maio"),
        budget_limit_brl=kw.pop("budget_limit_brl", "500.00"),
        reference_month=kw.pop("reference_month", "2026-05"),
        **kw,
    )


def _make_forecast(**kw) -> ForecastPlan:
    return ForecastPlan.new(
        title=kw.pop("title", "Revenue Q2 2026"),
        method=kw.pop("method", "linear"),
        historical_totals=kw.pop("historical_totals", ["800", "850", "900"]),
        **kw,
    )


def _make_roi(**kw) -> ROISummary:
    return ROISummary.new(
        title=kw.pop("title", "ROI Collab Maio"),
        total_revenue_brl=kw.pop("total_revenue_brl", "990.00"),
        total_cost_brl=kw.pop("total_cost_brl", "150.00"),
        reference_period=kw.pop("reference_period", "2026-05"),
        **kw,
    )


def _make_report(**kw) -> FinanceReport:
    return FinanceReport.new(
        title=kw.pop("title", "Resumo Financeiro Maio"),
        reference_period=kw.pop("reference_period", "2026-05"),
        total_revenue_brl=kw.pop("total_revenue_brl", "2500.00"),
        total_cost_brl=kw.pop("total_cost_brl", "800.00"),
        **kw,
    )


# ═══════════════════════════════════════════════════════════════
# RevenueRecord
# ═══════════════════════════════════════════════════════════════

class TestRevenueRecord:
    def test_new_creates_with_id_prefix(self):
        r = _make_revenue()
        assert r.id.startswith("rev_")
        assert len(r.id) == 12

    def test_new_creates_unique_ids(self):
        a = _make_revenue()
        b = _make_revenue()
        assert a.id != b.id

    def test_new_has_iso_timestamp(self):
        r = _make_revenue()
        assert "T" in r.recorded_at
        assert r.recorded_at.endswith("Z")

    def test_dry_run_true_by_default(self):
        r = _make_revenue()
        assert r.dry_run is True

    def test_can_set_dry_run_false(self):
        r = _make_revenue(dry_run=False)
        assert r.dry_run is False

    def test_amount_is_decimal(self):
        r = _make_revenue(amount_brl="990.50")
        assert isinstance(r.amount_brl, Decimal)
        assert r.amount_brl == Decimal("990.50")

    def test_rejects_invalid_category(self):
        with pytest.raises(ValueError, match="Invalid revenue category"):
            _make_revenue(category="rockets")

    def test_rejects_negative_amount(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            _make_revenue(amount_brl="-50.00")

    def test_accepts_all_valid_categories(self):
        for cat in VALID_REVENUE_CATEGORIES:
            r = _make_revenue(category=cat)
            assert r.category == cat

    def test_client_defaults_to_none(self):
        r = _make_revenue()
        assert r.client is None

    def test_metadata_defaults_to_empty(self):
        r = _make_revenue()
        assert r.metadata == {}

    def test_to_dict_from_dict_round_trip(self):
        r = _make_revenue(client="Hotel Serhs", metadata={"contract": "C001"})
        d = r.to_dict()
        restored = RevenueRecord.from_dict(d)
        assert restored.id == r.id
        assert restored.source == r.source
        assert restored.amount_brl == r.amount_brl
        assert restored.client == "Hotel Serhs"
        assert restored.metadata == {"contract": "C001"}

    def test_from_dict_defaults(self):
        d = {
            "id": "rev_test1234", "source": "S", "description": "D",
            "amount_brl": "100.00", "category": "collab",
            "reference_month": "2026-05",
        }
        r = RevenueRecord.from_dict(d)
        assert r.dry_run is True
        assert r.client is None
        assert r.metadata == {}


# ═══════════════════════════════════════════════════════════════
# CostRecord
# ═══════════════════════════════════════════════════════════════

class TestCostRecord:
    def test_new_creates_with_id_prefix(self):
        c = _make_cost()
        assert c.id.startswith("cst_")
        assert len(c.id) == 12

    def test_new_creates_unique_ids(self):
        a = _make_cost()
        b = _make_cost()
        assert a.id != b.id

    def test_dry_run_true_by_default(self):
        c = _make_cost()
        assert c.dry_run is True

    def test_amount_is_decimal(self):
        c = _make_cost(amount_brl="350.75")
        assert isinstance(c.amount_brl, Decimal)
        assert c.amount_brl == Decimal("350.75")

    def test_rejects_invalid_category(self):
        with pytest.raises(ValueError, match="Invalid cost category"):
            _make_cost(category="nuclear_warhead")

    def test_rejects_negative_amount(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            _make_cost(amount_brl="-10.00")

    def test_risk_flags_defaults_to_empty(self):
        c = _make_cost()
        assert c.risk_flags == []

    def test_can_set_risk_flags(self):
        c = _make_cost(risk_flags=[RiskFlag.PAYMENT])
        assert c.risk_flags == [RiskFlag.PAYMENT]

    def test_vendor_defaults_to_none(self):
        c = _make_cost()
        assert c.vendor is None

    def test_accepts_all_valid_categories(self):
        for cat in VALID_COST_CATEGORIES:
            c = _make_cost(category=cat)
            assert c.category == cat

    def test_to_dict_from_dict_round_trip(self):
        c = _make_cost(
            vendor="Meta Platforms",
            risk_flags=[RiskFlag.BILLING, RiskFlag.PAYMENT],
            metadata={"campaign_id": "C123"},
        )
        d = c.to_dict()
        restored = CostRecord.from_dict(d)
        assert restored.id == c.id
        assert restored.vendor == "Meta Platforms"
        assert restored.risk_flags == [RiskFlag.BILLING, RiskFlag.PAYMENT]
        assert restored.metadata == {"campaign_id": "C123"}

    def test_from_dict_defaults(self):
        d = {
            "id": "cst_test1234", "description": "D",
            "amount_brl": "50.00", "category": "ads",
            "reference_month": "2026-05",
        }
        c = CostRecord.from_dict(d)
        assert c.vendor is None
        assert c.risk_flags == []
        assert c.dry_run is True


# ═══════════════════════════════════════════════════════════════
# CommissionRule
# ═══════════════════════════════════════════════════════════════

class TestCommissionRule:
    def test_new_creates_with_id_prefix(self):
        cr = _make_commission()
        assert cr.id.startswith("com_")

    def test_new_creates_unique_ids(self):
        a = _make_commission()
        b = _make_commission()
        assert a.id != b.id

    def test_rate_is_decimal(self):
        cr = _make_commission(rate_pct="15.5")
        assert isinstance(cr.rate_pct, Decimal)
        assert cr.rate_pct == Decimal("15.5")

    def test_rejects_rate_below_zero(self):
        with pytest.raises(ValueError, match="between 0 and 100"):
            _make_commission(rate_pct="-1")

    def test_rejects_rate_above_100(self):
        with pytest.raises(ValueError, match="between 0 and 100"):
            _make_commission(rate_pct="150")

    def test_is_tiered_false_without_max(self):
        cr = _make_commission()
        assert cr.is_tiered is False

    def test_is_tiered_true_with_max(self):
        cr = _make_commission(max_revenue_brl="5000")
        assert cr.is_tiered is True

    def test_applies_to_within_range(self):
        cr = _make_commission(min_revenue_brl="100", max_revenue_brl="5000")
        assert cr.applies_to(Decimal("1000")) is True

    def test_applies_to_below_min(self):
        cr = _make_commission(min_revenue_brl="100")
        assert cr.applies_to(Decimal("50")) is False

    def test_applies_to_above_max(self):
        cr = _make_commission(max_revenue_brl="5000")
        assert cr.applies_to(Decimal("10000")) is False

    def test_apply_returns_correct_commission(self):
        cr = _make_commission(rate_pct="10")
        result = cr.apply(Decimal("1000"))
        assert result == Decimal("100.00")

    def test_apply_returns_zero_when_not_applicable(self):
        cr = _make_commission(min_revenue_brl="100")
        result = cr.apply(Decimal("50"))
        assert result == Decimal("0")

    def test_approval_required_defaults_to_false(self):
        cr = _make_commission()
        assert cr.approval_required is False

    def test_to_dict_from_dict_round_trip(self):
        cr = _make_commission(
            rate_pct="12.5", min_revenue_brl="200",
            max_revenue_brl="10000", tier_name="premium",
            approval_required=True,
        )
        d = cr.to_dict()
        restored = CommissionRule.from_dict(d)
        assert restored.id == cr.id
        assert restored.rate_pct == Decimal("12.5")
        assert restored.tier_name == "premium"
        assert restored.approval_required is True


# ═══════════════════════════════════════════════════════════════
# BudgetGuard
# ═══════════════════════════════════════════════════════════════

class TestBudgetGuard:
    def test_new_creates_with_id_prefix(self):
        bg = _make_budget_guard()
        assert bg.id.startswith("bgt_")

    def test_new_creates_unique_ids(self):
        a = _make_budget_guard()
        b = _make_budget_guard()
        assert a.id != b.id

    def test_remaining_brl_calculated(self):
        bg = _make_budget_guard(budget_limit_brl="500", spent_brl="150")
        assert bg.remaining_brl == Decimal("350")

    def test_is_over_budget_false_when_under(self):
        bg = _make_budget_guard(budget_limit_brl="500", spent_brl="400")
        assert bg.is_over_budget is False

    def test_is_over_budget_true_when_exceeded(self):
        bg = _make_budget_guard(budget_limit_brl="500", spent_brl="600")
        assert bg.is_over_budget is True

    def test_usage_pct_calculated(self):
        bg = _make_budget_guard(budget_limit_brl="1000", spent_brl="250")
        assert bg.usage_pct == Decimal("25.0")

    def test_usage_pct_zero_for_zero_limit(self):
        bg = _make_budget_guard(budget_limit_brl="0", spent_brl="0")
        assert bg.usage_pct == Decimal("0")

    def test_approval_status_pending_by_default(self):
        bg = _make_budget_guard()
        assert bg.approval_status == ApprovalStatus.PENDING

    def test_approve_updates_status(self):
        bg = _make_budget_guard()
        bg.approve()
        assert bg.approval_status == ApprovalStatus.APPROVED

    def test_reject_updates_status(self):
        bg = _make_budget_guard()
        bg.reject()
        assert bg.approval_status == ApprovalStatus.REJECTED

    def test_no_approval_not_required(self):
        bg = _make_budget_guard(approval_required=False)
        assert bg.approval_status == ApprovalStatus.NOT_REQUIRED

    def test_rejects_invalid_category(self):
        with pytest.raises(ValueError, match="Invalid cost category"):
            _make_budget_guard(category="black_hole")

    def test_rejects_negative_limit(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            _make_budget_guard(budget_limit_brl="-100")

    def test_rejects_negative_spent(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            _make_budget_guard(spent_brl="-50")

    def test_to_dict_from_dict_round_trip(self):
        bg = _make_budget_guard(
            budget_limit_brl="2000", spent_brl="800",
            risk_flags=[RiskFlag.BUDGET_EXCEEDED],
        )
        d = bg.to_dict()
        restored = BudgetGuard.from_dict(d)
        assert restored.id == bg.id
        assert restored.budget_limit_brl == Decimal("2000")
        assert restored.spent_brl == Decimal("800")
        assert restored.risk_flags == [RiskFlag.BUDGET_EXCEEDED]


# ═══════════════════════════════════════════════════════════════
# ForecastPlan
# ═══════════════════════════════════════════════════════════════

class TestForecastPlan:
    def test_new_creates_with_id_prefix(self):
        fp = _make_forecast()
        assert fp.id.startswith("fct_")

    def test_new_creates_unique_ids(self):
        a = _make_forecast()
        b = _make_forecast()
        assert a.id != b.id

    def test_historical_totals_are_decimals(self):
        fp = _make_forecast(historical_totals=["100", "200", "300"])
        assert all(isinstance(v, Decimal) for v in fp.historical_totals)

    def test_projected_totals_not_empty(self):
        fp = _make_forecast(period_months=6)
        assert len(fp.projected_totals) == 6

    def test_historical_avg_calculated(self):
        fp = _make_forecast(historical_totals=["100", "200", "300"])
        assert fp.historical_avg == Decimal("200.00")

    def test_projected_total_sum(self):
        fp = _make_forecast(historical_totals=["100", "100", "100"], method="moving_average")
        assert fp.projected_total == Decimal("300.00")  # 100 * 3 months

    def test_linear_forecast_trending_up(self):
        fp = _make_forecast(
            historical_totals=["100", "200", "300", "400", "500"],
            period_months=2,
        )
        assert fp.projected_totals[1] > fp.projected_totals[0]

    def test_moving_average_forecast_flat(self):
        fp = _make_forecast(
            historical_totals=["100", "200", "300"],
            method="moving_average", period_months=4,
        )
        assert fp.projected_totals[0] == fp.projected_totals[3]

    def test_seasonal_naive_forecast(self):
        fp = _make_forecast(
            historical_totals=["10", "20", "30"],
            method="seasonal_naive", period_months=3,
        )
        assert len(fp.projected_totals) == 3

    def test_manual_forecast_returns_zeros(self):
        fp = _make_forecast(historical_totals=["100"], method="manual", period_months=2)
        assert fp.projected_totals == [Decimal("0"), Decimal("0")]

    def test_rejects_invalid_method(self):
        with pytest.raises(ValueError, match="Invalid forecast method"):
            _make_forecast(method="crystal_ball")

    def test_rejects_empty_historical(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            _make_forecast(historical_totals=[])

    def test_rejects_negative_historical(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            _make_forecast(historical_totals=["100", "-50"])

    def test_rejects_zero_period(self):
        with pytest.raises(ValueError, match="at least 1 month"):
            _make_forecast(period_months=0)

    def test_rejects_invalid_confidence(self):
        with pytest.raises(ValueError, match="between 0 and 100"):
            _make_forecast(confidence_pct="150")

    def test_risk_flags_default_empty(self):
        fp = _make_forecast()
        assert fp.risk_flags == []

    def test_to_dict_from_dict_round_trip(self):
        fp = _make_forecast(
            historical_totals=["500", "600", "700"],
            method="linear", period_months=4,
            confidence_pct="85",
            risk_flags=[RiskFlag.FORECAST_SENSITIVE],
            approval_required=True,
        )
        d = fp.to_dict()
        restored = ForecastPlan.from_dict(d)
        assert restored.id == fp.id
        assert restored.method == "linear"
        assert restored.confidence_pct == Decimal("85")
        assert restored.risk_flags == [RiskFlag.FORECAST_SENSITIVE]
        assert restored.approval_required is True


# ═══════════════════════════════════════════════════════════════
# ROISummary
# ═══════════════════════════════════════════════════════════════

class TestROISummary:
    def test_new_creates_with_id_prefix(self):
        r = _make_roi()
        assert r.id.startswith("roi_")

    def test_new_creates_unique_ids(self):
        a = _make_roi()
        b = _make_roi()
        assert a.id != b.id

    def test_net_profit_calculated(self):
        r = _make_roi(total_revenue_brl="1000", total_cost_brl="300")
        assert r.net_profit_brl == Decimal("700")

    def test_roi_pct_calculated(self):
        r = _make_roi(total_revenue_brl="1000", total_cost_brl="500")
        assert r.roi_pct == Decimal("100.00")  # (500/500) * 100

    def test_roi_zero_cost_zero_revenue(self):
        r = _make_roi(total_revenue_brl="0", total_cost_brl="0")
        assert r.roi_pct == Decimal("0")

    def test_infinite_roi_marker(self):
        r = _make_roi(total_revenue_brl="100", total_cost_brl="0")
        assert r.roi_pct == Decimal("999999")

    def test_negative_net_when_loss(self):
        r = _make_roi(total_revenue_brl="100", total_cost_brl="500")
        assert r.net_profit_brl == Decimal("-400")

    def test_is_profitable_true(self):
        r = _make_roi(total_revenue_brl="1000", total_cost_brl="300")
        assert r.is_profitable is True

    def test_is_profitable_false(self):
        r = _make_roi(total_revenue_brl="100", total_cost_brl="500")
        assert r.is_profitable is False

    def test_profit_margin_pct(self):
        r = _make_roi(total_revenue_brl="1000", total_cost_brl="700")
        assert r.profit_margin_pct == Decimal("30.00")  # 300/1000 * 100

    def test_profit_margin_zero_revenue(self):
        r = _make_roi(total_revenue_brl="0", total_cost_brl="50")
        assert r.profit_margin_pct == Decimal("0")

    def test_rejects_negative_revenue(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            _make_roi(total_revenue_brl="-50")

    def test_rejects_negative_cost(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            _make_roi(total_cost_brl="-50")

    def test_to_dict_from_dict_round_trip(self):
        r = _make_roi(
            total_revenue_brl="5000", total_cost_brl="2000",
            reference_period="2026-Q2",
            revenue_records=5, cost_records=3,
            risk_flags=[RiskFlag.FORECAST_SENSITIVE],
        )
        d = r.to_dict()
        restored = ROISummary.from_dict(d)
        assert restored.id == r.id
        assert restored.total_revenue_brl == Decimal("5000")
        assert restored.reference_period == "2026-Q2"
        assert restored.revenue_records == 5
        assert restored.cost_records == 3


# ═══════════════════════════════════════════════════════════════
# FinanceReport
# ═══════════════════════════════════════════════════════════════

class TestFinanceReport:
    def test_new_creates_with_id_prefix(self):
        fr = _make_report()
        assert fr.id.startswith("fnr_")

    def test_new_creates_unique_ids(self):
        a = _make_report()
        b = _make_report()
        assert a.id != b.id

    def test_net_result_calculated(self):
        fr = _make_report(total_revenue_brl="5000", total_cost_brl="2000")
        assert fr.net_result_brl == Decimal("3000.00")

    def test_is_net_positive_true(self):
        fr = _make_report(total_revenue_brl="5000", total_cost_brl="2000")
        assert fr.is_net_positive is True

    def test_is_net_positive_false(self):
        fr = _make_report(total_revenue_brl="500", total_cost_brl="2000")
        assert fr.is_net_positive is False

    def test_over_budget_count(self):
        bg1 = BudgetGuard.new("A", "100", "2026-05", spent_brl="150")
        bg2 = BudgetGuard.new("B", "200", "2026-05", spent_brl="50")
        fr = _make_report(budget_guards=[bg1, bg2])
        assert fr.over_budget_count == 1

    def test_alerts_empty_by_default(self):
        fr = _make_report()
        assert fr.alerts == []

    def test_goals_empty_by_default(self):
        fr = _make_report()
        assert fr.goals == []

    def test_approval_status_not_required_by_default(self):
        fr = _make_report()
        assert fr.approval_status == ApprovalStatus.NOT_REQUIRED

    def test_approval_status_pending_when_required(self):
        fr = _make_report(approval_required=True)
        assert fr.approval_status == ApprovalStatus.PENDING

    def test_approve_updates_status(self):
        fr = _make_report(approval_required=True)
        fr.approve()
        assert fr.approval_status == ApprovalStatus.APPROVED

    def test_reject_updates_status(self):
        fr = _make_report(approval_required=True)
        fr.reject()
        assert fr.approval_status == ApprovalStatus.REJECTED

    def test_to_dict_from_dict_round_trip(self):
        bg = BudgetGuard.new("Test", "500", "2026-05")
        roi = ROISummary.new("ROI", "1000", "200", "2026-05")
        fr = _make_report(
            total_revenue_brl="10000", total_cost_brl="4000",
            budget_guards=[bg],
            goals=[{"name": "Meta Receita", "target": "15000", "actual": "10000"}],
            alerts=["CASH_ALERT: costs > revenue"],
            roi_summaries=[roi],
            risk_flags=[RiskFlag.BUDGET_EXCEEDED],
            approval_required=True,
        )
        d = fr.to_dict()
        restored = FinanceReport.from_dict(d)
        assert restored.id == fr.id
        assert restored.title == fr.title
        assert restored.total_revenue_brl == Decimal("10000")
        assert len(restored.budget_guards) == 1
        assert len(restored.roi_summaries) == 1
        assert len(restored.goals) == 1
        assert len(restored.alerts) == 1
        assert restored.approval_required is True


# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

class TestConstants:
    def test_valid_revenue_categories_cardinality(self):
        assert len(VALID_REVENUE_CATEGORIES) == 8

    def test_valid_cost_categories_cardinality(self):
        assert len(VALID_COST_CATEGORIES) == 10

    def test_valid_forecast_methods_cardinality(self):
        assert len(VALID_FORECAST_METHODS) == 4

    def test_valid_report_periods_cardinality(self):
        assert len(VALID_REPORT_PERIODS) == 5


# ═══════════════════════════════════════════════════════════════
# RiskFlag Enum
# ═══════════════════════════════════════════════════════════════

class TestRiskFlag:
    def test_risk_flag_values(self):
        assert RiskFlag.PAYMENT.value == "payment"
        assert RiskFlag.BILLING.value == "billing"
        assert RiskFlag.BUDGET_EXCEEDED.value == "budget_exceeded"
        assert RiskFlag.FORECAST_SENSITIVE.value == "forecast_sensitive"

    def test_risk_flag_from_value(self):
        assert RiskFlag("payment") == RiskFlag.PAYMENT
        assert RiskFlag("forecast_sensitive") == RiskFlag.FORECAST_SENSITIVE


# ═══════════════════════════════════════════════════════════════
# ApprovalStatus Enum
# ═══════════════════════════════════════════════════════════════

class TestApprovalStatus:
    def test_approval_status_values(self):
        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"
        assert ApprovalStatus.NOT_REQUIRED.value == "not_required"
