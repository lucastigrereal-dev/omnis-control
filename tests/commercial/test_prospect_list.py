"""Tests for W122 — ProspectList + ProspectEntry."""
from __future__ import annotations

import pytest
import tempfile
from pathlib import Path

from src.sales.leads import Lead
from src.commercial.hotel_lead import HotelLead
from src.commercial.prospect_list import ProspectEntry, ProspectList


class TestProspectEntry:
    def _make_hotel_lead(self) -> HotelLead:
        base = Lead(
            lead_id="l1", name="Hotel Sol RN", company="Sol Resorts",
            contact_channel="instagram", source="indicacao", segment="hotel",
        )
        return HotelLead(
            hotel_lead_id="h1", base_lead=base, hotel_name="Hotel Sol RN Resort",
            city="Natal", state="RN", region="nordeste", hotel_tier="Premium",
            niche="resort", fit_score=85, priority_tier="hot",
        )

    def test_create_entry(self):
        hl = self._make_hotel_lead()
        entry = ProspectEntry(entry_id="e1", hotel_lead=hl)
        assert entry.entry_id == "e1"
        assert entry.hotel_lead.hotel_name == "Hotel Sol RN Resort"
        assert entry.dry_run is True

    def test_priority_score_hot_premium_nordeste(self):
        hl = self._make_hotel_lead()
        entry = ProspectEntry(entry_id="e1", hotel_lead=hl)
        # fit_score=85 + hot(3*10=30) + Premium(+15) + nordeste(+10) = 140
        assert entry.priority_score == 140

    def test_priority_score_cold_starter_no_region(self):
        base = Lead(lead_id="l2", name="Hotel Frio")
        hl = HotelLead(
            hotel_lead_id="h2", base_lead=base, hotel_name="Hotel Frio",
            hotel_tier="Starter", fit_score=20, priority_tier="cold",
        )
        entry = ProspectEntry(entry_id="e2", hotel_lead=hl)
        # fit=20 + cold(1*10=10) + Starter(+0) + no_region(+0) = 30
        assert entry.priority_score == 30

    def test_priority_score_disqualified(self):
        base = Lead(lead_id="l3", name="Fora")
        hl = HotelLead(
            hotel_lead_id="h3", base_lead=base, priority_tier="disqualified",
            fit_score=50,
        )
        entry = ProspectEntry(entry_id="e3", hotel_lead=hl)
        # fit=50 + disqualified(0) + Growth(5) = 55
        assert entry.priority_score == 55

    def test_to_dict_roundtrip(self):
        hl = self._make_hotel_lead()
        entry = ProspectEntry(entry_id="e1", hotel_lead=hl, tags=["vip"], notes="top prospect")
        d = entry.to_dict()
        restored = ProspectEntry.from_dict(d)
        assert restored.entry_id == "e1"
        assert restored.hotel_lead.hotel_name == "Hotel Sol RN Resort"
        assert restored.tags == ["vip"]
        assert restored.notes == "top prospect"

    def test_to_markdown(self):
        hl = self._make_hotel_lead()
        entry = ProspectEntry(entry_id="e1", hotel_lead=hl)
        md = entry.to_markdown()
        assert "Hotel Sol RN Resort" in md
        assert "e1" in md
        assert "Natal/RN" in md
        assert "Premium" in md


class TestProspectList:
    def _make_hotel_lead(self, lead_id: str = "l1", hotel_lead_id: str = "h1",
                         hotel_name: str = "Hotel Test", city: str = "Natal",
                         state: str = "RN", region: str = "nordeste",
                         hotel_tier: str = "Premium", niche: str = "resort",
                         fit_score: int = 80, priority_tier: str = "hot") -> HotelLead:
        base = Lead(lead_id=lead_id, name=hotel_name, contact_channel="instagram")
        return HotelLead(
            hotel_lead_id=hotel_lead_id, base_lead=base, hotel_name=hotel_name,
            city=city, state=state, region=region, hotel_tier=hotel_tier,
            niche=niche, fit_score=fit_score, priority_tier=priority_tier,
        )

    def test_create_empty_list(self):
        pl = ProspectList()
        assert pl.count == 0
        assert pl.list_all() == []

    def test_add_hotel_lead(self):
        pl = ProspectList()
        hl = self._make_hotel_lead()
        entry = pl.add(hl, tags=["vip"])
        assert pl.count == 1
        assert entry.hotel_lead.hotel_name == "Hotel Test"
        assert entry.tags == ["vip"]

    def test_add_multiple(self):
        pl = ProspectList()
        for i in range(3):
            hl = self._make_hotel_lead(lead_id=f"l{i}", hotel_lead_id=f"h{i}",
                                        hotel_name=f"Hotel {i}")
            pl.add(hl)
        assert pl.count == 3

    def test_get_entry(self):
        pl = ProspectList()
        hl = self._make_hotel_lead()
        entry = pl.add(hl)
        fetched = pl.get(entry.entry_id)
        assert fetched is not None
        assert fetched.entry_id == entry.entry_id

    def test_get_nonexistent(self):
        pl = ProspectList()
        assert pl.get("nonexistent") is None

    def test_remove_entry(self):
        pl = ProspectList()
        hl = self._make_hotel_lead()
        entry = pl.add(hl)
        assert pl.count == 1
        assert pl.remove(entry.entry_id) is True
        assert pl.count == 0

    def test_remove_nonexistent(self):
        pl = ProspectList()
        assert pl.remove("nonexistent") is False

    def test_filter_by_city(self):
        pl = ProspectList()
        pl.add(self._make_hotel_lead(hotel_lead_id="h1", city="Natal"))
        pl.add(self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2", city="Recife"))
        pl.add(self._make_hotel_lead(hotel_lead_id="h3", lead_id="l3", city="Natal"))
        assert len(pl.filter_by_city("Natal")) == 2
        assert len(pl.filter_by_city("natal")) == 2  # case insensitive
        assert len(pl.filter_by_city("Recife")) == 1

    def test_filter_by_state(self):
        pl = ProspectList()
        pl.add(self._make_hotel_lead(hotel_lead_id="h1", state="RN"))
        pl.add(self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2", state="PE"))
        assert len(pl.filter_by_state("RN")) == 1
        assert len(pl.filter_by_state("rn")) == 1

    def test_filter_by_tier(self):
        pl = ProspectList()
        pl.add(self._make_hotel_lead(hotel_lead_id="h1", hotel_tier="Premium"))
        pl.add(self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2", hotel_tier="Starter"))
        assert len(pl.filter_by_tier("Premium")) == 1
        assert len(pl.filter_by_tier("Starter")) == 1

    def test_filter_by_priority(self):
        pl = ProspectList()
        pl.add(self._make_hotel_lead(hotel_lead_id="h1", priority_tier="hot"))
        pl.add(self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2", priority_tier="warm"))
        assert len(pl.filter_by_priority("hot")) == 1

    def test_filter_by_niche(self):
        pl = ProspectList()
        pl.add(self._make_hotel_lead(hotel_lead_id="h1", niche="resort"))
        pl.add(self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2", niche="pousada"))
        assert len(pl.filter_by_niche("resort")) == 1

    def test_filter_by_region(self):
        pl = ProspectList()
        pl.add(self._make_hotel_lead(hotel_lead_id="h1", region="nordeste"))
        pl.add(self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2", region="sul"))
        assert len(pl.filter_by_region("nordeste")) == 1
        assert len(pl.filter_by_region("NORDESTE")) == 1

    def test_filter_pursuable(self):
        pl = ProspectList()
        pl.add(self._make_hotel_lead(hotel_lead_id="h1", priority_tier="hot"))
        pl.add(self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2", priority_tier="warm"))
        pl.add(self._make_hotel_lead(hotel_lead_id="h3", lead_id="l3", priority_tier="cold"))
        assert len(pl.filter_pursuable()) == 2

    def test_prioritized_order(self):
        pl = ProspectList()
        # High priority
        pl.add(self._make_hotel_lead(hotel_lead_id="h1", hotel_tier="Premium",
                                      priority_tier="hot", fit_score=90, region="nordeste"))
        # Low priority
        pl.add(self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2", hotel_tier="Starter",
                                      priority_tier="cold", fit_score=10))
        sorted_entries = pl.prioritized()
        assert sorted_entries[0].hotel_lead.hotel_lead_id == "h1"  # highest first

    def test_top_n(self):
        pl = ProspectList()
        for i in range(5):
            pl.add(self._make_hotel_lead(
                hotel_lead_id=f"h{i}", lead_id=f"l{i}",
                hotel_name=f"Hotel {i}", fit_score=50 + i * 10,
                priority_tier="hot" if i < 3 else "warm",
            ))
        top3 = pl.top(3)
        assert len(top3) == 3

    def test_hot_list(self):
        pl = ProspectList()
        pl.add(self._make_hotel_lead(hotel_lead_id="h1", priority_tier="hot", fit_score=90))
        pl.add(self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2", priority_tier="hot", fit_score=70))
        pl.add(self._make_hotel_lead(hotel_lead_id="h3", lead_id="l3", priority_tier="warm", fit_score=95))
        hot = pl.hot_list()
        assert len(hot) == 2
        assert hot[0].hotel_lead.fit_score == 90  # sorted by fit_score desc

    def test_pursuable_count(self):
        pl = ProspectList()
        pl.add(self._make_hotel_lead(hotel_lead_id="h1", priority_tier="hot"))
        pl.add(self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2", priority_tier="warm"))
        pl.add(self._make_hotel_lead(hotel_lead_id="h3", lead_id="l3", priority_tier="cold"))
        assert pl.pursuable_count == 2

    def test_premium_candidates(self):
        pl = ProspectList()
        pl.add(self._make_hotel_lead(hotel_lead_id="h1", hotel_tier="Premium", fit_score=90))
        pl.add(self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2", hotel_tier="Premium", fit_score=50))
        pl.add(self._make_hotel_lead(hotel_lead_id="h3", lead_id="l3", hotel_tier="Growth", fit_score=95))
        assert pl.premium_candidates == 1

    def test_compute_scores(self):
        pl = ProspectList()
        pl.add(self._make_hotel_lead(hotel_lead_id="h1", hotel_tier="Premium",
                                      priority_tier="hot", fit_score=90))
        pl.add(self._make_hotel_lead(hotel_lead_id="h2", lead_id="l2", hotel_tier="Starter",
                                      priority_tier="cold", fit_score=10))
        scores = pl.compute_scores()
        assert len(scores) == 2
        # Premium/hot should rank higher
        assert scores[0]["composite"] > scores[1]["composite"]

    def test_export_summary(self):
        pl = ProspectList()
        pl.add(self._make_hotel_lead())
        summary = pl.export_summary()
        assert "SDR Prospect List Summary" in summary
        assert "Hotel Test" in summary

    def test_to_jsonl(self):
        pl = ProspectList()
        pl.add(self._make_hotel_lead())
        jsonl = pl.to_jsonl()
        assert "Hotel Test" in jsonl

    def test_file_backed_save_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            pl1 = ProspectList(storage_dir=tmp)
            pl1.add(self._make_hotel_lead(hotel_lead_id="h1"))
            pl1.add(self._make_hotel_lead(
                hotel_lead_id="h2", lead_id="l2", hotel_name="Hotel 2", city="Recife",
            ))

            pl2 = ProspectList.load(tmp)
            assert pl2.count == 2
            names = {e.hotel_lead.hotel_name for e in pl2.list_all()}
            assert "Hotel Test" in names
            assert "Hotel 2" in names

    def test_no_external_calls(self):
        pl = ProspectList()
        hl = self._make_hotel_lead()
        entry = pl.add(hl)
        assert entry.dry_run is True
        assert entry.hotel_lead.dry_run is True
        assert entry.hotel_lead.base_lead.dry_run is True

    def test_dry_run_default(self):
        pl = ProspectList()
        hl = self._make_hotel_lead()
        entry = pl.add(hl)
        assert entry.dry_run is True
