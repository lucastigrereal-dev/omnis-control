"""Tests for P14 Finance service layer."""

from __future__ import annotations

from decimal import Decimal

import pytest

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


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _revenue(**kw) -> RevenueRecord:
    return RevenueRecord.new(
        source=kw.pop("source", "Collab Test"),
        description=kw.pop("description", "Test revenue"),
        amount_brl=kw.pop("amount_brl", "500.00"),
        category=kw.pop("category", "collab"),
        reference_month=kw.pop("reference_month", "2026-05"),
        **kw,
    )


def _cost(**kw) -> CostRecord:
    return CostRecord.new(
        description=kw.pop("description", "Test cost"),
        amount_brl=kw.pop("amount_brl", "100.00"),
        category=kw.pop("category", "ads"),
        reference_month=kw.pop("reference_month", "2026-05"),
        **kw,
    )


# ═══════════════════════════════════════════════════════════════
# ValidationResult
# ═══════════════════════════════════════════════════════════════

class TestValidationResult:
    def test_success_ok(self):
        vr = ValidationResult.success()
        assert vr.valid is True
        assert vr.ok is True

    def test_success_with_warnings(self):
        vr = ValidationResult.success(warnings=["low data"])
        assert vr.ok is True
        assert vr.warnings == ["low data"]

    def test_failure_not_ok(self):
        vr = ValidationResult.failure(["bad data"])
        assert vr.valid is False
        assert vr.ok is False

    def test_failure_stores_issues(self):
        vr = ValidationResult.failure(["issue1", "issue2"])
        assert vr.issues == ["issue1", "issue2"]


# ═══════════════════════════════════════════════════════════════
# Standalone Functions
# ═══════════════════════════════════════════════════════════════

class TestCalculateROI:
    def test_returns_roi_summary(self):
        roi = calculate_roi("1000", "400")
        assert isinstance(roi, ROISummary)
        assert roi.id.startswith("roi_")

    def test_net_profit_correct(self):
        roi = calculate_roi("1000", "300", title="Test", reference_period="2026-05")
        assert roi.net_profit_brl == Decimal("700")
        assert roi.title == "Test"
        assert roi.reference_period == "2026-05"

    def test_roi_pct_correct(self):
        roi = calculate_roi("1000", "500")
        assert roi.roi_pct == Decimal("100.00")


class TestForecastRevenue:
    def test_returns_forecast_plan(self):
        fp = forecast_revenue("Q2 Forecast", ["100", "200", "300"])
        assert isinstance(fp, ForecastPlan)
        assert fp.id.startswith("fct_")
        assert fp.title == "Q2 Forecast"

    def test_default_method_is_linear(self):
        fp = forecast_revenue("Test", ["100", "200", "300"])
        assert fp.method == "linear"

    def test_default_period_is_3(self):
        fp = forecast_revenue("Test", ["100", "200", "300"])
        assert fp.period_months == 3


class TestApplyCommissionRule:
    def test_returns_dict_with_result(self):
        rule = CommissionRule.new("Standard", "10.0")
        result = apply_commission_rule(rule, "1000")
        assert result["rule_name"] == "Standard"
        assert result["commission_brl"] == "100.00"
        assert result["rate_pct"] == "10.0"

    def test_approval_required_reflected(self):
        rule = CommissionRule.new("Approved Tier", "15", approval_required=True)
        result = apply_commission_rule(rule, "2000")
        assert result["approval_required"] is True


class TestBuildBudgetGuard:
    def test_returns_budget_guard(self):
        bg = build_budget_guard("Ads Q2", "2000", "2026-Q2")
        assert isinstance(bg, BudgetGuard)
        assert bg.id.startswith("bgt_")
        assert bg.name == "Ads Q2"
        assert bg.budget_limit_brl == Decimal("2000")

    def test_approval_required_default_true(self):
        bg = build_budget_guard("Test", "1000", "2026-05")
        assert bg.approval_required is True


class TestBuildFinanceReport:
    def test_returns_finance_report(self):
        revenues = [_revenue(amount_brl="500"), _revenue(amount_brl="300")]
        costs = [_cost(amount_brl="100")]
        fr = build_finance_report("Report", "2026-05", revenues, costs)
        assert isinstance(fr, FinanceReport)
        assert fr.total_revenue_brl == Decimal("800")
        assert fr.total_cost_brl == Decimal("100")
        assert fr.net_result_brl == Decimal("700.00")

    def test_alerts_on_over_budget(self):
        revenues = [_revenue(amount_brl="1000")]
        costs = [_cost(amount_brl="100")]
        bg = BudgetGuard.new("Ads Limit", "50", "2026-05", spent_brl="80")
        fr = build_finance_report("R", "2026-05", revenues, costs, budget_guards=[bg])
        assert len(fr.alerts) >= 1
        assert any("BUDGET_EXCEEDED" in a for a in fr.alerts)

    def test_cash_alert_when_costs_exceed_revenue(self):
        revenues = [_revenue(amount_brl="100")]
        costs = [_cost(amount_brl="500")]
        fr = build_finance_report("R", "2026-05", revenues, costs)
        assert any("CASH_ALERT" in a for a in fr.alerts)

    def test_risk_flags_from_cost_records(self):
        revenues = [_revenue(amount_brl="1000")]
        costs = [_cost(amount_brl="100", risk_flags=[RiskFlag.PAYMENT, RiskFlag.BILLING])]
        fr = build_finance_report("R", "2026-05", revenues, costs)
        assert RiskFlag.PAYMENT in fr.risk_flags
        assert RiskFlag.BILLING in fr.risk_flags

    def test_includes_roi_summaries(self):
        revenues = [_revenue(amount_brl="500")]
        costs = [_cost(amount_brl="100")]
        roi = ROISummary.new("ROI", "500", "100", "2026-05")
        fr = build_finance_report("R", "2026-05", revenues, costs, roi_summaries=[roi])
        assert len(fr.roi_summaries) == 1


class TestValidateFinanceInputs:
    def test_empty_records_warns(self):
        vr = validate_finance_inputs([], [])
        assert vr.ok is True
        assert len(vr.warnings) >= 1

    def test_zero_amount_warns(self):
        revenues = [_revenue(amount_brl="0")]
        vr = validate_finance_inputs(revenues, [])
        assert vr.ok is True
        assert any("zero" in w.lower() for w in vr.warnings)

    def test_valid_records_pass(self):
        revenues = [_revenue(amount_brl="500")]
        costs = [_cost(amount_brl="100")]
        vr = validate_finance_inputs(revenues, costs)
        assert vr.ok is True
        assert vr.issues == []


# ═══════════════════════════════════════════════════════════════
# FinancePlanner
# ═══════════════════════════════════════════════════════════════

class TestFinancePlanner:
    def test_default_dry_run_true(self):
        planner = FinancePlanner()
        assert planner.dry_run is True

    def test_can_set_dry_run_false(self):
        planner = FinancePlanner(dry_run=False)
        assert planner.dry_run is False

    # ── Revenue ──────────────────────────────────────────────

    def test_record_revenue_returns_revenue_record(self):
        planner = FinancePlanner()
        r = planner.record_revenue("Collab X", "Publi carrossel", "990", "collab", "2026-05")
        assert isinstance(r, RevenueRecord)
        assert r.source == "Collab X"
        assert r.id.startswith("rev_")

    def test_record_revenue_tracks_in_inventory(self):
        planner = FinancePlanner()
        planner.record_revenue("A", "a", "100", "collab", "2026-05")
        planner.record_revenue("B", "b", "200", "publi", "2026-05")
        assert planner.revenue_count == 2
        assert len(planner.list_revenue()) == 2

    # ── Cost ─────────────────────────────────────────────────

    def test_record_cost_returns_cost_record(self):
        planner = FinancePlanner()
        c = planner.record_cost("Meta Ads", "150", "ads", "2026-05")
        assert isinstance(c, CostRecord)
        assert c.description == "Meta Ads"
        assert c.id.startswith("cst_")

    def test_record_cost_with_risk_flags(self):
        planner = FinancePlanner()
        c = planner.record_cost("Invoice", "500", "services", "2026-05", risk_flags=[RiskFlag.PAYMENT])
        assert c.risk_flags == [RiskFlag.PAYMENT]

    def test_record_cost_tracks_in_inventory(self):
        planner = FinancePlanner()
        planner.record_cost("A", "100", "ads", "2026-05")
        planner.record_cost("B", "200", "tools", "2026-05")
        assert planner.cost_count == 2

    # ── Commission ───────────────────────────────────────────

    def test_define_commission_rule_returns_rule(self):
        planner = FinancePlanner()
        rule = planner.define_commission_rule("Sales Comm", "10.0")
        assert isinstance(rule, CommissionRule)
        assert rule.name == "Sales Comm"

    def test_compute_commissions_applies_matching_rules(self):
        planner = FinancePlanner()
        planner.define_commission_rule("T1", "5.0", min_revenue_brl="0", max_revenue_brl="1000")
        planner.define_commission_rule("T2", "10.0", min_revenue_brl="1001", max_revenue_brl="5000")
        results = planner.compute_commissions("2000")
        assert len(results) == 1
        assert results[0]["rule_name"] == "T2"
        assert results[0]["commission_brl"] == "200.00"

    # ── Budget Guard ─────────────────────────────────────────

    def test_set_budget_guard_returns_guard(self):
        planner = FinancePlanner()
        guard = planner.set_budget_guard("Ads", "1000", "2026-05")
        assert isinstance(guard, BudgetGuard)
        assert guard.approval_required is True

    def test_check_budget_raises_when_exceeded(self):
        planner = FinancePlanner()
        guard = planner.set_budget_guard("Ads", "500", "2026-05", spent_brl="600")
        with pytest.raises(BudgetExceededError, match="exceeded"):
            planner.check_budget(guard)

    def test_check_budget_ok_when_under(self):
        planner = FinancePlanner()
        guard = planner.set_budget_guard("Ads", "500", "2026-05", spent_brl="300")
        planner.check_budget(guard)  # Should not raise

    # ── Forecast ─────────────────────────────────────────────

    def test_create_forecast_returns_plan(self):
        planner = FinancePlanner()
        fp = planner.create_forecast("Q3 Forecast", ["100", "200", "300", "400"])
        assert isinstance(fp, ForecastPlan)
        assert fp.title == "Q3 Forecast"
        assert fp.confidence_pct == Decimal("80")  # default

    def test_forecast_with_sensitivity_has_risk_flags(self):
        planner = FinancePlanner()
        fp = planner.forecast_with_sensitivity("Sensitive Q3", ["100", "200", "300"])
        assert RiskFlag.FORECAST_SENSITIVE in fp.risk_flags
        assert fp.approval_required is True
        assert fp.confidence_pct == Decimal("70")

    # ── ROI ──────────────────────────────────────────────────

    def test_compute_roi_from_records(self):
        planner = FinancePlanner()
        planner.record_revenue("A", "a", "1000", "collab", "2026-05")
        planner.record_revenue("B", "b", "500", "publi", "2026-05")
        planner.record_cost("C1", "200", "ads", "2026-05")
        roi = planner.compute_roi("ROI Maio", "2026-05")
        assert roi.total_revenue_brl == Decimal("1500")
        assert roi.total_cost_brl == Decimal("200")
        assert roi.net_profit_brl == Decimal("1300")
        assert roi.revenue_records == 2
        assert roi.cost_records == 1

    # ── Report ───────────────────────────────────────────────

    def test_build_report_returns_finance_report(self):
        planner = FinancePlanner()
        planner.record_revenue("A", "a", "500", "collab", "2026-05")
        planner.record_cost("B", "100", "ads", "2026-05")
        report = planner.build_report("Resumo", "2026-05")
        assert isinstance(report, FinanceReport)
        assert report.title == "Resumo"
        assert report.total_revenue_brl == Decimal("500")
        assert report.total_cost_brl == Decimal("100")

    def test_build_report_with_goals(self):
        planner = FinancePlanner()
        planner.record_revenue("A", "a", "1000", "collab", "2026-05")
        goals = [{"name": "Meta Mensal", "target": "10000", "actual": "1000"}]
        report = planner.build_report("Resumo", "2026-05", goals=goals, approval_required=True)
        assert len(report.goals) == 1
        assert report.approval_required is True
        assert report.approval_status == ApprovalStatus.PENDING

    # ── Validate ─────────────────────────────────────────────

    def test_validate_delegates(self):
        planner = FinancePlanner()
        vr = planner.validate()
        assert isinstance(vr, ValidationResult)
        assert vr.ok is True  # warns on empty, but still ok

    # ── Properties ───────────────────────────────────────────

    def test_total_revenue_property(self):
        planner = FinancePlanner()
        planner.record_revenue("A", "a", "100.50", "collab", "2026-05")
        planner.record_revenue("B", "b", "200.25", "publi", "2026-05")
        assert planner.total_revenue == Decimal("300.75")

    def test_total_cost_property(self):
        planner = FinancePlanner()
        planner.record_cost("A", "50.00", "ads", "2026-05")
        planner.record_cost("B", "75.50", "tools", "2026-05")
        assert planner.total_cost == Decimal("125.50")

    def test_net_result_property(self):
        planner = FinancePlanner()
        planner.record_revenue("A", "a", "1000", "collab", "2026-05")
        planner.record_cost("B", "300", "ads", "2026-05")
        assert planner.net_result == Decimal("700")

    # ── Inventory lists ──────────────────────────────────────

    def test_list_revenue_returns_copy(self):
        planner = FinancePlanner()
        planner.record_revenue("X", "x", "100", "collab", "2026-05")
        copy1 = planner.list_revenue()
        copy1.clear()
        assert planner.revenue_count == 1

    def test_list_costs_returns_copy(self):
        planner = FinancePlanner()
        planner.record_cost("X", "100", "ads", "2026-05")
        copy1 = planner.list_costs()
        copy1.clear()
        assert planner.cost_count == 1

    def test_list_forecasts(self):
        planner = FinancePlanner()
        planner.create_forecast("F1", ["100", "200"])
        planner.create_forecast("F2", ["300", "400"])
        assert len(planner.list_forecasts()) == 2

    def test_list_roi_summaries(self):
        planner = FinancePlanner()
        planner.record_revenue("A", "a", "500", "collab", "2026-05")
        planner.compute_roi()
        assert len(planner.list_roi_summaries()) == 1

    def test_list_reports(self):
        planner = FinancePlanner()
        planner.record_revenue("A", "a", "500", "collab", "2026-05")
        planner.build_report("R1")
        planner.build_report("R2")
        assert len(planner.list_reports()) == 2

    def test_list_budget_guards(self):
        planner = FinancePlanner()
        planner.set_budget_guard("G1", "1000", "2026-05")
        planner.set_budget_guard("G2", "2000", "2026-05")
        assert len(planner.list_budget_guards()) == 2


# ═══════════════════════════════════════════════════════════════
# End-to-End Scenario
# ═══════════════════════════════════════════════════════════════

class TestEndToEnd:
    def test_full_monthly_workflow(self):
        planner = FinancePlanner()

        # Record revenue
        planner.record_revenue("Collab Hotel Serhs", "Publi carrossel", "990", "collab", "2026-05", client="Hotel Serhs")
        planner.record_revenue("Collab Restaurante", "Publi stories", "350", "collab", "2026-05", client="Restaurante X")
        planner.record_revenue("Consulting", "Mentoria Instagram", "500", "consulting", "2026-05")

        # Record costs
        planner.record_cost("Meta Ads", "300", "ads", "2026-05", vendor="Meta", risk_flags=[RiskFlag.BILLING])
        planner.record_cost("Canva Pro", "55", "tools", "2026-05", vendor="Canva")
        planner.record_cost("Freelancer video", "200", "services", "2026-05", risk_flags=[RiskFlag.PAYMENT])

        # Budget guard
        guard = planner.set_budget_guard("Marketing Budget", "1000", "2026-05", category="ads")
        assert guard.remaining_brl == Decimal("1000")

        # Validate
        vr = planner.validate()
        assert vr.ok is True

        # ROI
        roi = planner.compute_roi("ROI Maio 2026", "2026-05")
        assert roi.is_profitable is True
        assert roi.roi_pct > 0

        # Forecast
        forecast = planner.create_forecast("Revenue Forecast Jun-Ago", ["800", "900", "1840"])
        assert len(forecast.projected_totals) == 3

        # Report
        report = planner.build_report("Resumo Financeiro Maio 2026", "2026-05", approval_required=True)
        assert report.total_revenue_brl == Decimal("1840")
        assert report.total_cost_brl == Decimal("555")
        assert report.net_result_brl == Decimal("1285.00")
        assert report.is_net_positive is True
        assert planner.revenue_count == 3
        assert planner.cost_count == 3

        # Approve
        report.approve()
        assert report.approval_status == ApprovalStatus.APPROVED
