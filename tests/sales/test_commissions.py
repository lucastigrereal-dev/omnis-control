"""Tests for W117 — Commission Calculator."""
from __future__ import annotations

import pytest

from src.sales.commissions import (
    CommissionCalculator,
    CommissionRule,
    CommissionResult,
    DEFAULT_RULES,
)


class TestCommissionRule:
    def test_create_rule(self):
        rule = CommissionRule(tier="Starter", base_rate=0.20)
        assert rule.tier == "Starter"
        assert rule.base_rate == 0.20
        assert rule.bonus_rate == 0.0

    def test_calculate_basic(self):
        rule = CommissionRule(tier="Starter", base_rate=0.20)
        assert rule.calculate(350.0) == 70.0  # 20% of 350

    def test_calculate_with_bonus(self):
        rule = CommissionRule(
            tier="Growth",
            base_rate=0.20,
            bonus_rate=0.10,
            threshold=2000.0,
        )
        # deal = 3000, base = 600, bonus on 1000 @ 10% = 100, total = 700
        assert rule.calculate(3000.0) == 700.0

    def test_calculate_with_cap(self):
        rule = CommissionRule(
            tier="Premium",
            base_rate=0.25,
            bonus_rate=0.10,
            threshold=3000.0,
            cap=800.0,
        )
        # deal = 20000, base = 5000, bonus on 17000 @ 10% = 1700, total = 6700 -> capped at 800
        assert rule.calculate(20000.0) == 800.0

    def test_calculate_negative_raises(self):
        rule = CommissionRule(tier="Starter", base_rate=0.20)
        with pytest.raises(ValueError, match="negative"):
            rule.calculate(-100.0)

    def test_calculate_zero(self):
        rule = CommissionRule(tier="Starter", base_rate=0.20)
        assert rule.calculate(0.0) == 0.0

    def test_no_threshold_no_bonus(self):
        rule = CommissionRule(tier="Starter", base_rate=0.20)
        assert rule.calculate(1000.0) == 200.0  # No bonus since threshold=0


class TestCommissionCalculator:
    def setup_method(self):
        self.calc = CommissionCalculator()

    def test_calculate_starter(self):
        result = self.calc.calculate("Starter", 350.0)
        assert result.tier == "Starter"
        assert result.base_commission == 70.0
        assert result.total_commission == 70.0
        assert result.net_value == 280.0

    def test_calculate_growth(self):
        result = self.calc.calculate("Growth", 990.0)
        assert result.tier == "Growth"
        assert result.base_commission == 198.0  # 20% of 990

    def test_calculate_premium(self):
        result = self.calc.calculate("Premium", 1200.0)
        assert result.tier == "Premium"
        assert result.base_commission == 300.0  # 25% of 1200

    def test_calculate_with_bonus(self):
        result = self.calc.calculate("Growth", 3000.0)
        # base: 20% of 3000 = 600, bonus: 10% of (3000-2000) = 100, total = 700 (below 500 cap)
        assert result.base_commission == 600.0
        assert result.bonus_commission == 100.0
        assert result.total_commission == 700.0
        assert result.cap_applied is False

    def test_calculate_with_cap(self):
        result = self.calc.calculate("Premium", 20000.0)
        assert result.total_commission == 800.0  # capped
        assert result.cap_applied is True

    def test_calculate_negative_raises(self):
        with pytest.raises(ValueError, match="negative"):
            self.calc.calculate("Starter", -50.0)

    def test_calculate_unknown_tier_raises(self):
        with pytest.raises(ValueError, match="Unknown tier"):
            self.calc.calculate("Enterprise", 1000.0)

    def test_result_has_explanation(self):
        result = self.calc.calculate("Starter", 350.0)
        assert "Starter" in result.explanation
        assert "350" in result.explanation

    def test_result_to_dict(self):
        result = self.calc.calculate("Growth", 990.0)
        d = result.to_dict()
        assert d["tier"] == "Growth"
        assert d["deal_value"] == 990.0

    def test_calculate_for_deal(self):
        result = self.calc.calculate_for_deal(1200.0, ["Starter", "Premium"])
        assert result.tier == "Premium"
        assert result.base_rate == 0.25

    def test_calculate_for_deal_defaults_to_growth(self):
        result = self.calc.calculate_for_deal(500.0, ["Outro"])
        assert result.tier == "Growth"

    def test_get_rule(self):
        rule = self.calc.get_rule("Starter")
        assert rule is not None
        assert rule.tier == "Starter"

    def test_get_rule_unknown(self):
        assert self.calc.get_rule("Enterprise") is None

    def test_custom_rules(self):
        custom = {
            "VIP": CommissionRule(tier="VIP", base_rate=0.30),
        }
        calc = CommissionCalculator(rules=custom)
        result = calc.calculate("VIP", 1000.0)
        assert result.total_commission == 300.0
