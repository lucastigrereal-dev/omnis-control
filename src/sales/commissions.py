"""W117 — Commission Calculator for Sales/CRM."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class CommissionRule:
    """A single commission rule for a tier."""

    tier: str  # Starter, Growth, Premium
    base_rate: float  # e.g. 0.20 = 20%
    bonus_rate: float = 0.0  # extra % above threshold
    threshold: float = 0.0  # value above which bonus applies
    cap: float = 0.0  # max commission (0 = no cap)

    def calculate(self, deal_value: float) -> float:
        if deal_value < 0:
            raise ValueError("Deal value cannot be negative")
        base = deal_value * self.base_rate
        bonus = 0.0
        if self.threshold > 0 and deal_value > self.threshold:
            bonus = (deal_value - self.threshold) * self.bonus_rate
        total = base + bonus
        if self.cap > 0 and total > self.cap:
            total = self.cap
        return round(total, 2)


# Default commission tiers based on OMNIS pricing
DEFAULT_RULES: dict[str, CommissionRule] = {
    "Starter": CommissionRule(
        tier="Starter",
        base_rate=0.20,
        bonus_rate=0.05,
        threshold=500.0,
        cap=200.0,
    ),
    "Growth": CommissionRule(
        tier="Growth",
        base_rate=0.20,
        bonus_rate=0.10,
        threshold=2000.0,
        cap=0.0,
    ),
    "Premium": CommissionRule(
        tier="Premium",
        base_rate=0.25,
        bonus_rate=0.10,
        threshold=3000.0,
        cap=800.0,
    ),
}


@dataclass
class CommissionResult:
    """Output of commission calculation."""

    tier: str
    deal_value: float
    base_rate: float
    base_commission: float
    bonus_rate: float = 0.0
    bonus_commission: float = 0.0
    cap_applied: bool = False
    total_commission: float = 0.0
    net_value: float = 0.0  # deal_value - total_commission
    explanation: str = ""
    calculated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "deal_value": self.deal_value,
            "base_rate": self.base_rate,
            "base_commission": self.base_commission,
            "bonus_rate": self.bonus_rate,
            "bonus_commission": self.bonus_commission,
            "cap_applied": self.cap_applied,
            "total_commission": self.total_commission,
            "net_value": self.net_value,
            "explanation": self.explanation,
            "calculated_at": self.calculated_at,
        }


class CommissionCalculator:
    """Calculates commissions per tier rules — purely local, zero external calls."""

    def __init__(self, rules: dict[str, CommissionRule] | None = None):
        self._rules = rules or DEFAULT_RULES

    def calculate(self, tier: str, deal_value: float) -> CommissionResult:
        if deal_value < 0:
            raise ValueError("Deal value cannot be negative")

        rule = self._rules.get(tier)
        if not rule:
            raise ValueError(f"Unknown tier: {tier}. Valid: {list(self._rules.keys())}")

        total = rule.calculate(deal_value)
        base_commission = round(deal_value * rule.base_rate, 2)
        bonus_commission = 0.0
        cap_applied = False

        if rule.threshold > 0 and deal_value > rule.threshold:
            bonus_commission = round((deal_value - rule.threshold) * rule.bonus_rate, 2)

        if rule.cap > 0 and total >= rule.cap:
            cap_applied = True

        explanation_parts = [f"{tier}: {deal_value:,.2f} × {rule.base_rate:.0%} = R$ {base_commission:,.2f}"]
        if bonus_commission > 0:
            explanation_parts.append(
                f"Bônus sobre excedente de R$ {rule.threshold:,.2f}: + R$ {bonus_commission:,.2f}"
            )
        if cap_applied:
            explanation_parts.append(f"Cap aplicado em R$ {rule.cap:,.2f}")

        return CommissionResult(
            tier=tier,
            deal_value=deal_value,
            base_rate=rule.base_rate,
            base_commission=base_commission,
            bonus_rate=rule.bonus_rate,
            bonus_commission=bonus_commission,
            cap_applied=cap_applied,
            total_commission=total,
            net_value=round(deal_value - total, 2),
            explanation="; ".join(explanation_parts),
        )

    def calculate_for_deal(self, deal_value: float, products: list[str]) -> CommissionResult:
        # Use highest tier in products, or Growth as default
        tier_order = {"Premium": 3, "Growth": 2, "Starter": 1}
        best = "Growth"
        best_rank = 0
        for p in products:
            rank = tier_order.get(p, 0)
            if rank > best_rank:
                best = p
                best_rank = rank
        return self.calculate(tier=best, deal_value=deal_value)

    def get_rule(self, tier: str) -> CommissionRule | None:
        return self._rules.get(tier)
