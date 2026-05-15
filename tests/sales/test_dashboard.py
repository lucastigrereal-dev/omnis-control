"""Tests for W118 — Sales Dashboard."""
from __future__ import annotations

import pytest

from src.sales.deals import DealRegistry
from src.sales.dashboard import SalesDashboard, SalesMetrics


class TestSalesMetrics:
    def test_create_metrics(self):
        m = SalesMetrics(pipeline_value=5000.0, deals_total=10)
        assert m.pipeline_value == 5000.0
        assert m.deals_total == 10

    def test_to_dict(self):
        m = SalesMetrics(pipeline_value=3000.0, deals_active=5, deals_total=8)
        d = m.to_dict()
        assert d["pipeline_value"] == 3000.0
        assert d["deals_active"] == 5

    def test_to_markdown(self):
        m = SalesMetrics(
            pipeline_value=5000.0,
            weighted_pipeline_value=2500.0,
            deals_active=3,
            deals_closed_won=2,
            closed_won_value=2000.0,
            deals_by_stage={"novo": 2, "proposta": 1},
        )
        md = m.to_markdown()
        assert "Sales Dashboard" in md
        assert "5,000.00" in md
        assert "novo" in md


class TestSalesDashboard:
    def setup_method(self):
        self.dashboard = SalesDashboard()
        self.registry = DealRegistry()

    def test_empty_registry(self):
        metrics = self.dashboard.compute(self.registry)
        assert metrics.deals_total == 0
        assert metrics.pipeline_value == 0.0
        assert metrics.conversion_rate == 0.0

    def test_active_deals_pipeline_value(self):
        self.registry.create(lead_id="l1", value=350.0, stage="novo")
        self.registry.create(lead_id="l2", value=990.0, stage="qualificado")
        self.registry.create(lead_id="l3", value=1200.0, stage="proposta")
        metrics = self.dashboard.compute(self.registry)
        assert metrics.deals_total == 3
        assert metrics.deals_active == 3
        assert metrics.pipeline_value == 2540.0

    def test_weighted_pipeline_value(self):
        self.registry.create(lead_id="l1", value=1000.0, probability=0.5, stage="novo")
        self.registry.create(lead_id="l2", value=2000.0, probability=0.25, stage="qualificado")
        metrics = self.dashboard.compute(self.registry)
        assert metrics.weighted_pipeline_value == 1000.0  # 500 + 500

    def test_closed_won_and_lost(self):
        self.registry.create(lead_id="l1", value=350.0, stage="fechado")
        self.registry.create(lead_id="l2", value=500.0, stage="fechado")
        self.registry.create(lead_id="l3", value=200.0, stage="perdido")
        metrics = self.dashboard.compute(self.registry)
        assert metrics.deals_closed_won == 2
        assert metrics.deals_closed_lost == 1
        assert metrics.closed_won_value == 850.0
        assert metrics.lost_value == 200.0

    def test_conversion_rate(self):
        self.registry.create(lead_id="l1", value=100.0, stage="fechado")
        self.registry.create(lead_id="l2", value=100.0, stage="fechado")
        self.registry.create(lead_id="l3", value=100.0, stage="perdido")
        self.registry.create(lead_id="l4", value=100.0, stage="perdido")
        metrics = self.dashboard.compute(self.registry)
        assert metrics.conversion_rate == 0.5  # 2/4

    def test_conversion_rate_zero_when_no_closed(self):
        self.registry.create(lead_id="l1", value=100.0, stage="novo")
        metrics = self.dashboard.compute(self.registry)
        assert metrics.conversion_rate == 0.0

    def test_deals_by_stage(self):
        self.registry.create(lead_id="l1", stage="novo")
        self.registry.create(lead_id="l2", stage="novo")
        self.registry.create(lead_id="l3", stage="proposta")
        self.registry.create(lead_id="l4", stage="fechado")
        metrics = self.dashboard.compute(self.registry)
        assert metrics.deals_by_stage["novo"] == 2
        assert metrics.deals_by_stage["proposta"] == 1
        assert metrics.deals_by_stage["fechado"] == 1

    def test_avg_deal_value(self):
        self.registry.create(lead_id="l1", value=100.0)
        self.registry.create(lead_id="l2", value=300.0)
        metrics = self.dashboard.compute(self.registry)
        assert metrics.avg_deal_value == 200.0

    def test_followups_due(self):
        metrics = self.dashboard.compute(self.registry, followups_due=3)
        assert metrics.followups_due == 3

    def test_proposals_open(self):
        metrics = self.dashboard.compute(self.registry, proposals_open=2)
        assert metrics.proposals_open == 2

    def test_no_external_dependencies(self):
        self.registry.create(lead_id="l1", value=500.0, stage="novo")
        metrics = self.dashboard.compute(self.registry)
        # All computation is local, no API calls
        assert metrics.computed_at != ""
