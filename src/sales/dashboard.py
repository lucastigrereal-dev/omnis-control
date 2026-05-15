"""W118 — Sales Dashboard metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.sales.deals import DealRegistry
from src.sales.pipeline import PipelineStage


@dataclass
class SalesMetrics:
    """Aggregated sales metrics — computed from local data only."""

    pipeline_value: float = 0.0
    weighted_pipeline_value: float = 0.0
    deals_total: int = 0
    deals_active: int = 0
    deals_closed_won: int = 0
    deals_closed_lost: int = 0
    conversion_rate: float = 0.0  # won / (won + lost)
    avg_deal_value: float = 0.0
    avg_cycle_days: float = 0.0  # placeholder — requires deal history
    followups_due: int = 0
    proposals_open: int = 0
    closed_won_value: float = 0.0
    lost_value: float = 0.0
    deals_by_stage: dict[str, int] = field(default_factory=dict)
    computed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "pipeline_value": self.pipeline_value,
            "weighted_pipeline_value": self.weighted_pipeline_value,
            "deals_total": self.deals_total,
            "deals_active": self.deals_active,
            "deals_closed_won": self.deals_closed_won,
            "deals_closed_lost": self.deals_closed_lost,
            "conversion_rate": self.conversion_rate,
            "avg_deal_value": self.avg_deal_value,
            "avg_cycle_days": self.avg_cycle_days,
            "followups_due": self.followups_due,
            "proposals_open": self.proposals_open,
            "closed_won_value": self.closed_won_value,
            "lost_value": self.lost_value,
            "deals_by_stage": self.deals_by_stage,
            "computed_at": self.computed_at,
        }

    def to_markdown(self) -> str:
        def brl(v: float) -> str:
            return f"R$ {v:,.2f}"

        return "\n".join([
            "# Sales Dashboard",
            "",
            "## Resumo",
            f"**Pipeline Total:** {brl(self.pipeline_value)}",
            f"**Pipeline Ponderado:** {brl(self.weighted_pipeline_value)}",
            f"**Deals Ativos:** {self.deals_active}",
            f"**Ganhos:** {self.deals_closed_won} ({brl(self.closed_won_value)})",
            f"**Perdidos:** {self.deals_closed_lost} ({brl(self.lost_value)})",
            f"**Taxa de Conversão:** {self.conversion_rate:.1%}",
            f"**Ticket Médio:** {brl(self.avg_deal_value)}",
            "",
            "## Pipeline por Stage",
            *[f"- **{s}:** {c}" for s, c in sorted(self.deals_by_stage.items())],
            "",
            f"**Computed:** {self.computed_at[:19]}",
        ])


class SalesDashboard:
    """Computes sales metrics from registries — local-only, zero external calls."""

    def compute(
        self,
        deals: DealRegistry,
        followups_due: int = 0,
        proposals_open: int = 0,
    ) -> SalesMetrics:
        all_deals = deals.list_all()
        active = [d for d in all_deals if d.stage not in {
            PipelineStage.FECHADO.value,
            PipelineStage.PERDIDO.value,
            PipelineStage.ARQUIVADO.value,
        }]
        won = [d for d in all_deals if d.stage == PipelineStage.FECHADO.value]
        lost = [d for d in all_deals if d.stage == PipelineStage.PERDIDO.value]

        total_won_lost = len(won) + len(lost)
        conversion = len(won) / total_won_lost if total_won_lost > 0 else 0.0

        total_value = sum(d.value for d in all_deals)
        avg_value = total_value / len(all_deals) if all_deals else 0.0

        stage_counts: dict[str, int] = {}
        for d in all_deals:
            stage_counts[d.stage] = stage_counts.get(d.stage, 0) + 1

        return SalesMetrics(
            pipeline_value=sum(d.value for d in active),
            weighted_pipeline_value=sum(d.weighted_value for d in active),
            deals_total=len(all_deals),
            deals_active=len(active),
            deals_closed_won=len(won),
            deals_closed_lost=len(lost),
            conversion_rate=conversion,
            avg_deal_value=round(avg_value, 2),
            followups_due=followups_due,
            proposals_open=proposals_open,
            closed_won_value=sum(d.value for d in won),
            lost_value=sum(d.value for d in lost),
            deals_by_stage=stage_counts,
        )
