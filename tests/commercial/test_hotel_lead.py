"""Tests for W121 — HotelLead model + HotelLeadRegistry."""
from __future__ import annotations

import pytest
import tempfile
from pathlib import Path

from src.sales.leads import Lead, LeadRegistry
from src.commercial.hotel_lead import HotelLead, HotelLeadRegistry


class TestHotelLead:
    def _make_base_lead(self) -> Lead:
        return Lead(
            lead_id="l1",
            name="Hotel Sol RN",
            company="Sol Resorts Ltda",
            contact_channel="instagram",
            source="indicacao",
            segment="hotel",
            interest="pacote",
            tags=["resort", "praia"],
            score=85,
        )

    def test_create_hotel_lead_valid(self):
        base = self._make_base_lead()
        hl = HotelLead(
            hotel_lead_id="h1",
            base_lead=base,
            hotel_name="Hotel Sol RN Resort",
            city="Natal",
            state="RN",
            region="nordeste",
            hotel_tier="Premium",
            niche="resort",
            fit_score=85,
            priority_tier="hot",
        )
        assert hl.hotel_lead_id == "h1"
        assert hl.hotel_name == "Hotel Sol RN Resort"
        assert hl.city == "Natal"
        assert hl.state == "RN"
        assert hl.dry_run is True

    def test_proxy_properties_from_base_lead(self):
        base = self._make_base_lead()
        hl = HotelLead(hotel_lead_id="h2", base_lead=base, city="Natal")
        assert hl.lead_id == "l1"
        assert hl.name == "Hotel Sol RN"
        assert hl.company == "Sol Resorts Ltda"
        assert hl.contact_channel == "instagram"
        assert hl.source == "indicacao"
        assert hl.interest == "pacote"

    def test_invalid_hotel_tier_raises(self):
        base = self._make_base_lead()
        with pytest.raises(ValueError, match="Invalid hotel_tier"):
            HotelLead(hotel_lead_id="h3", base_lead=base, hotel_tier="Enterprise")

    def test_invalid_niche_raises(self):
        base = self._make_base_lead()
        with pytest.raises(ValueError, match="Invalid niche"):
            HotelLead(hotel_lead_id="h4", base_lead=base, niche="hospital")

    def test_invalid_priority_raises(self):
        base = self._make_base_lead()
        with pytest.raises(ValueError, match="Invalid priority_tier"):
            HotelLead(hotel_lead_id="h5", base_lead=base, priority_tier="urgent")

    def test_is_pursuable(self):
        base = self._make_base_lead()
        hot = HotelLead(hotel_lead_id="h6", base_lead=base, priority_tier="hot")
        warm = HotelLead(hotel_lead_id="h7", base_lead=base, priority_tier="warm")
        cold = HotelLead(hotel_lead_id="h8", base_lead=base, priority_tier="cold")
        disq = HotelLead(hotel_lead_id="h9", base_lead=base, priority_tier="disqualified")
        assert hot.is_pursuable is True
        assert warm.is_pursuable is True
        assert cold.is_pursuable is False
        assert disq.is_pursuable is False

    def test_is_premium_candidate(self):
        base = self._make_base_lead()
        yes = HotelLead(hotel_lead_id="h10", base_lead=base, hotel_tier="Premium", fit_score=90)
        no_tier = HotelLead(hotel_lead_id="h11", base_lead=base, hotel_tier="Growth", fit_score=90)
        no_score = HotelLead(hotel_lead_id="h12", base_lead=base, hotel_tier="Premium", fit_score=70)
        assert yes.is_premium_candidate is True
        assert no_tier.is_premium_candidate is False
        assert no_score.is_premium_candidate is False

    def test_cnpj_is_masked(self):
        base = self._make_base_lead()
        hl = HotelLead(hotel_lead_id="h13", base_lead=base, cnpj_placeholder="**MASKED**1234")
        assert "MASKED" in hl.cnpj_placeholder
        # Never real CNPJ

    def test_to_dict_roundtrip(self):
        base = self._make_base_lead()
        hl = HotelLead(
            hotel_lead_id="h14",
            base_lead=base,
            hotel_name="Pousada Mar Azul",
            city="Maragogi",
            state="AL",
            region="nordeste",
            hotel_tier="Growth",
            niche="pousada",
            room_count_placeholder=25,
            average_daily_rate_placeholder=350.0,
            decision_maker_name="Maria Silva",
            decision_maker_role="Gerente",
            fit_score=72,
            priority_tier="warm",
        )
        d = hl.to_dict()
        restored = HotelLead.from_dict(d)
        assert restored.hotel_lead_id == "h14"
        assert restored.hotel_name == "Pousada Mar Azul"
        assert restored.city == "Maragogi"
        assert restored.base_lead.name == "Hotel Sol RN"
        assert restored.room_count_placeholder == 25
        assert restored.average_daily_rate_placeholder == 350.0
        assert restored.decision_maker_name == "Maria Silva"

    def test_to_markdown(self):
        base = self._make_base_lead()
        hl = HotelLead(
            hotel_lead_id="h15",
            base_lead=base,
            hotel_name="Resort Costa Verde",
            city="Salvador",
            state="BA",
            hotel_tier="Premium",
            niche="resort",
            fit_score=90,
            priority_tier="hot",
        )
        md = hl.to_markdown()
        assert "Resort Costa Verde" in md
        assert "h15" in md
        assert "Salvador/BA" in md
        assert "Premium" in md

    def test_touch_updates_timestamp(self):
        import time
        base = self._make_base_lead()
        hl = HotelLead(hotel_lead_id="h16", base_lead=base)
        old = hl.updated_at
        time.sleep(0.01)
        hl.touch()
        assert hl.updated_at != old

    def test_default_values(self):
        base = self._make_base_lead()
        hl = HotelLead(hotel_lead_id="h17", base_lead=base)
        assert hl.hotel_tier == "Growth"
        assert hl.niche == "hotel"
        assert hl.priority_tier == "warm"
        assert hl.fit_score == 0
        assert hl.region == ""

    def test_dry_run_default(self):
        base = self._make_base_lead()
        hl = HotelLead(hotel_lead_id="h18", base_lead=base)
        assert hl.dry_run is True

    def test_no_external_api(self):
        base = self._make_base_lead()
        hl = HotelLead(hotel_lead_id="h19", base_lead=base, city="Natal")
        assert hl.dry_run is True
        assert hl.cnpj_placeholder == ""  # No enrichment
        # Zero network, zero env reads


class TestHotelLeadRegistry:
    def _make_base_lead(self) -> Lead:
        return Lead(lead_id="l1", name="Hotel Teste", segment="hotel")

    def test_create_and_get(self):
        registry = HotelLeadRegistry()
        base = self._make_base_lead()
        hl = registry.create(base_lead=base, hotel_name="Hotel Alpha", city="Natal", state="RN")
        assert registry.count == 1
        fetched = registry.get(hl.hotel_lead_id)
        assert fetched is not None
        assert fetched.hotel_name == "Hotel Alpha"

    def test_create_multiple(self):
        registry = HotelLeadRegistry()
        for i in range(3):
            base = Lead(lead_id=f"l{i}", name=f"Lead {i}")
            registry.create(base_lead=base, hotel_name=f"Hotel {i}", city=f"City {i}")
        assert registry.count == 3

    def test_get_by_base_lead(self):
        registry = HotelLeadRegistry()
        base = self._make_base_lead()
        hl = registry.create(base_lead=base, hotel_name="Hotel Beta")
        found = registry.get_by_base_lead(base.lead_id)
        assert found is not None
        assert found.hotel_lead_id == hl.hotel_lead_id

    def test_get_by_base_lead_not_found(self):
        registry = HotelLeadRegistry()
        assert registry.get_by_base_lead("nonexistent") is None

    def test_list_by_city(self):
        registry = HotelLeadRegistry()
        b1 = Lead(lead_id="l1", name="A")
        b2 = Lead(lead_id="l2", name="B")
        b3 = Lead(lead_id="l3", name="C")
        registry.create(base_lead=b1, city="Natal", state="RN")
        registry.create(base_lead=b2, city="Natal", state="RN")
        registry.create(base_lead=b3, city="Recife", state="PE")
        assert len(registry.list_by_city("Natal")) == 2
        assert len(registry.list_by_city("natal")) == 2  # case insensitive
        assert len(registry.list_by_city("Recife")) == 1

    def test_list_by_state(self):
        registry = HotelLeadRegistry()
        b1 = Lead(lead_id="l1", name="A")
        b2 = Lead(lead_id="l2", name="B")
        registry.create(base_lead=b1, state="RN")
        registry.create(base_lead=b2, state="PE")
        assert len(registry.list_by_state("RN")) == 1
        assert len(registry.list_by_state("rn")) == 1

    def test_list_by_niche(self):
        registry = HotelLeadRegistry()
        b1 = Lead(lead_id="l1", name="A")
        b2 = Lead(lead_id="l2", name="B")
        registry.create(base_lead=b1, niche="resort")
        registry.create(base_lead=b2, niche="pousada")
        assert len(registry.list_by_niche("resort")) == 1
        assert len(registry.list_by_niche("pousada")) == 1

    def test_list_by_tier(self):
        registry = HotelLeadRegistry()
        b1 = Lead(lead_id="l1", name="A")
        b2 = Lead(lead_id="l2", name="B")
        registry.create(base_lead=b1, hotel_tier="Starter")
        registry.create(base_lead=b2, hotel_tier="Premium")
        assert len(registry.list_by_tier("Starter")) == 1
        assert len(registry.list_by_tier("Premium")) == 1

    def test_list_pursuable(self):
        registry = HotelLeadRegistry()
        b1 = Lead(lead_id="l1", name="Hot")
        b2 = Lead(lead_id="l2", name="Cold")
        registry.create(base_lead=b1, priority_tier="hot")
        registry.create(base_lead=b2, priority_tier="cold")
        pursuable = registry.list_pursuable()
        assert len(pursuable) == 1
        assert pursuable[0].base_lead.name == "Hot"

    def test_list_by_priority(self):
        registry = HotelLeadRegistry()
        b1 = Lead(lead_id="l1", name="A")
        b2 = Lead(lead_id="l2", name="B")
        registry.create(base_lead=b1, priority_tier="hot")
        registry.create(base_lead=b2, priority_tier="warm")
        assert len(registry.list_by_priority("hot")) == 1
        assert len(registry.list_by_priority("warm")) == 1

    def test_pursuable_count(self):
        registry = HotelLeadRegistry()
        b1 = Lead(lead_id="l1", name="A")
        b2 = Lead(lead_id="l2", name="B")
        b3 = Lead(lead_id="l3", name="C")
        registry.create(base_lead=b1, priority_tier="hot")
        registry.create(base_lead=b2, priority_tier="warm")
        registry.create(base_lead=b3, priority_tier="cold")
        assert registry.pursuable_count == 2

    def test_premium_candidates(self):
        registry = HotelLeadRegistry()
        b1 = Lead(lead_id="l1", name="P1")
        b2 = Lead(lead_id="l2", name="P2")
        registry.create(base_lead=b1, hotel_tier="Premium", fit_score=90)
        registry.create(base_lead=b2, hotel_tier="Growth", fit_score=95)
        assert registry.premium_candidates == 1

    def test_update(self):
        registry = HotelLeadRegistry()
        base = self._make_base_lead()
        hl = registry.create(base_lead=base, hotel_name="Old Name", fit_score=50)
        updated = registry.update(hl.hotel_lead_id, hotel_name="New Name", fit_score=80)
        assert updated is not None
        assert updated.hotel_name == "New Name"
        assert updated.fit_score == 80

    def test_update_nonexistent(self):
        registry = HotelLeadRegistry()
        assert registry.update("nonexistent", hotel_name="X") is None

    def test_delete(self):
        registry = HotelLeadRegistry()
        base = self._make_base_lead()
        hl = registry.create(base_lead=base)
        assert registry.count == 1
        assert registry.delete(hl.hotel_lead_id) is True
        assert registry.count == 0

    def test_delete_nonexistent(self):
        registry = HotelLeadRegistry()
        assert registry.delete("nonexistent") is False

    def test_file_backed_save_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg1 = HotelLeadRegistry(storage_dir=tmp)
            b1 = Lead(lead_id="l1", name="Lead 1")
            b2 = Lead(lead_id="l2", name="Lead 2")
            reg1.create(base_lead=b1, hotel_name="H1", city="Natal")
            reg1.create(base_lead=b2, hotel_name="H2", city="Recife")

            reg2 = HotelLeadRegistry.load(tmp)
            assert reg2.count == 2
            names = {hl.hotel_name for hl in reg2.list_all()}
            assert "H1" in names
            assert "H2" in names

    def test_to_jsonl(self):
        registry = HotelLeadRegistry()
        base = self._make_base_lead()
        registry.create(base_lead=base, hotel_name="JSONL Hotel", city="Natal")
        jsonl = registry.to_jsonl()
        assert "JSONL Hotel" in jsonl

    def test_no_external_calls(self):
        registry = HotelLeadRegistry()
        base = self._make_base_lead()
        hl = registry.create(base_lead=base)
        assert hl.dry_run is True
        assert hl.base_lead.dry_run is True
