"""Tests for W113 — Deal model + DealRegistry."""
from __future__ import annotations

import pytest
import tempfile

from src.sales.deals import Deal, DealRegistry


class TestDeal:
    def test_create_deal_minimal(self):
        deal = Deal(deal_id="d1", lead_id="l1")
        assert deal.deal_id == "d1"
        assert deal.lead_id == "l1"
        assert deal.value == 0.0
        assert deal.currency == "BRL"
        assert deal.stage == "novo"
        assert deal.dry_run is True

    def test_create_deal_full(self):
        deal = Deal(
            deal_id="d2",
            lead_id="l2",
            title="Pacote Premium — Resort Costa Verde",
            value=1200.0,
            probability=0.6,
            expected_close_date="2026-06-15",
            owner="lucas",
            products=["Growth", "Premium"],
        )
        assert deal.value == 1200.0
        assert deal.probability == 0.6
        assert deal.owner == "lucas"
        assert "Growth" in deal.products

    def test_weighted_value(self):
        deal = Deal(deal_id="d3", lead_id="l3", value=1000.0, probability=0.5)
        assert deal.weighted_value == 500.0

    def test_weighted_value_zero_probability(self):
        deal = Deal(deal_id="d4", lead_id="l4", value=1000.0, probability=0.0)
        assert deal.weighted_value == 0.0

    def test_to_dict_roundtrip(self):
        deal = Deal(
            deal_id="d5",
            lead_id="l5",
            title="Collab Hotel Teste",
            value=350.0,
            products=["Starter"],
            stage="proposta",
        )
        d = deal.to_dict()
        restored = Deal.from_dict(d)
        assert restored.deal_id == "d5"
        assert restored.lead_id == "l5"
        assert restored.value == 350.0
        assert restored.stage == "proposta"

    def test_to_markdown(self):
        deal = Deal(deal_id="d6", lead_id="l6", title="Publi Natal", value=990.0)
        md = deal.to_markdown()
        assert "Publi Natal" in md
        assert "d6" in md
        assert "990.00" in md

    def test_default_stage_novo(self):
        deal = Deal(deal_id="d7", lead_id="l7")
        assert deal.stage == "novo"

    def test_dry_run_default(self):
        deal = Deal(deal_id="d8", lead_id="l8")
        assert deal.dry_run is True


class TestDealRegistry:
    def test_create_deal(self):
        registry = DealRegistry()
        deal = registry.create(lead_id="l1", title="Deal Test")
        assert registry.count == 1
        assert deal.lead_id == "l1"

    def test_create_deal_negative_value_raises(self):
        registry = DealRegistry()
        with pytest.raises(ValueError, match="value cannot be negative"):
            registry.create(lead_id="l1", title="Bad Deal", value=-100.0)

    def test_update_deal_negative_value_raises(self):
        registry = DealRegistry()
        deal = registry.create(lead_id="l1", value=500.0)
        with pytest.raises(ValueError, match="value cannot be negative"):
            registry.update(deal.deal_id, value=-50.0)

    def test_list_by_lead(self):
        registry = DealRegistry()
        registry.create(lead_id="l1", title="Deal A")
        registry.create(lead_id="l1", title="Deal B")
        registry.create(lead_id="l2", title="Deal C")
        assert len(registry.list_by_lead("l1")) == 2
        assert len(registry.list_by_lead("l2")) == 1

    def test_list_by_stage(self):
        registry = DealRegistry()
        registry.create(lead_id="l1", title="A", stage="novo")
        registry.create(lead_id="l2", title="B", stage="proposta")
        assert len(registry.list_by_stage("novo")) == 1
        assert len(registry.list_by_stage("proposta")) == 1

    def test_update_deal(self):
        registry = DealRegistry()
        deal = registry.create(lead_id="l1", title="Old Title", value=500.0)
        updated = registry.update(deal.deal_id, title="New Title", value=800.0)
        assert updated is not None
        assert updated.title == "New Title"
        assert updated.value == 800.0

    def test_update_nonexistent(self):
        registry = DealRegistry()
        assert registry.update("nonexistent", title="X") is None

    def test_delete_deal(self):
        registry = DealRegistry()
        deal = registry.create(lead_id="l1")
        assert registry.count == 1
        registry.delete(deal.deal_id)
        assert registry.count == 0

    def test_delete_nonexistent(self):
        registry = DealRegistry()
        assert registry.delete("nonexistent") is False

    def test_total_pipeline_value(self):
        registry = DealRegistry()
        registry.create(lead_id="l1", value=350.0)
        registry.create(lead_id="l2", value=990.0)
        registry.create(lead_id="l3", value=1200.0)
        assert registry.total_pipeline_value() == 2540.0

    def test_total_weighted_value(self):
        registry = DealRegistry()
        registry.create(lead_id="l1", value=1000.0, probability=0.5)
        registry.create(lead_id="l2", value=2000.0, probability=0.25)
        assert registry.total_weighted_value() == 1000.0  # 500 + 500

    def test_file_backed_save_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg1 = DealRegistry(storage_dir=tmp)
            reg1.create(lead_id="l1", title="File Deal 1", value=500.0)
            reg1.create(lead_id="l2", title="File Deal 2", value=800.0)

            reg2 = DealRegistry.load(tmp)
            assert reg2.count == 2
            values = {d.value for d in reg2.list_all()}
            assert 500.0 in values
            assert 800.0 in values

    def test_to_jsonl(self):
        registry = DealRegistry()
        registry.create(lead_id="l1", title="JSONL Deal")
        jsonl = registry.to_jsonl()
        assert "JSONL Deal" in jsonl

    def test_no_external_calls(self):
        registry = DealRegistry()
        deal = registry.create(lead_id="l1", title="Safe Deal")
        assert deal.dry_run is True
