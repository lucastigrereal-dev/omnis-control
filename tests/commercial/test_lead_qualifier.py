"""Tests for W124 — Lead Qualifier BANT."""
from __future__ import annotations

import pytest
from pathlib import Path

from src.sales.leads import Lead
from src.commercial.hotel_lead import HotelLead
from src.commercial.prospect_list import ProspectList
from src.commercial.lead_qualifier import (
    BANTResult,
    LeadQualifier,
    _score_budget,
    _score_authority,
    _score_need,
    _score_timing,
    _determine_tier,
    QUALIFIED,
    NURTURE,
    LOW_FIT,
    DISQUALIFIED,
    MISSING_INFO,
    QUALIFICATION_TIERS,
    TIER_NEXT_ACTIONS,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_strong_lead() -> HotelLead:
    """HotelLead with strong BANT signals across all dimensions."""
    base = Lead(
        lead_id="l1", name="Resort Paradiso", company="Paradiso Hoteis Ltda",
        contact_channel="whatsapp", source="indicacao", segment="hotel",
        interest="pacote", tags=["resort", "praia", "oportunidade"],
        score=90,
    )
    return HotelLead(
        hotel_lead_id="h1", base_lead=base, hotel_name="Resort Paradiso",
        city="Porto de Galinhas", state="PE", region="nordeste",
        hotel_tier="Premium", niche="resort",
        room_count_placeholder=120, average_daily_rate_placeholder=850.0,
        decision_maker_name="Carlos Mendes", decision_maker_role="Proprietario",
        fit_score=90, priority_tier="hot",
    )


def _make_medium_lead() -> HotelLead:
    """HotelLead with medium BANT signals."""
    base = Lead(
        lead_id="l2", name="Pousada Brisa", company="Brisa Turismo Ltda",
        contact_channel="email", source="instagram", segment="hotel",
        interest="collab", tags=["pousada", "praia"],
        score=60,
    )
    return HotelLead(
        hotel_lead_id="h2", base_lead=base, hotel_name="Pousada Brisa",
        city="Maragogi", state="AL", region="nordeste",
        hotel_tier="Growth", niche="pousada",
        room_count_placeholder=25, average_daily_rate_placeholder=350.0,
        decision_maker_name="Ana Souza", decision_maker_role="Gerente",
        fit_score=60, priority_tier="warm",
    )


def _make_weak_lead() -> HotelLead:
    """HotelLead with weak BANT signals."""
    base = Lead(
        lead_id="l3", name="Hostel Centro", company="Centro Hospedagem Ltda",
        contact_channel="", source="prospeccao", segment="hotel",
        interest="", tags=["hostel"],
        score=10,
    )
    return HotelLead(
        hotel_lead_id="h3", base_lead=base, hotel_name="Hostel Centro",
        city="Sao Paulo", state="SP", region="sudeste",
        hotel_tier="Starter", niche="hostel",
        room_count_placeholder=10, average_daily_rate_placeholder=80.0,
        decision_maker_name="", decision_maker_role="",
        fit_score=10, priority_tier="cold",
    )


def _make_missing_info_lead() -> HotelLead:
    """HotelLead with mostly placeholder/missing data."""
    base = Lead(lead_id="l4", name="Hotel Vazio")
    return HotelLead(
        hotel_lead_id="h4", base_lead=base, hotel_name="Hotel Vazio",
    )


# ── Dimension Scoring Tests ────────────────────────────────────────────────

class TestBudgetScoring:
    def test_premium_high_adr(self):
        hl = _make_strong_lead()
        result = _score_budget(hl)
        assert result["score"] >= 20
        assert result["score"] <= 25
        assert any("Premium" in r for r in result["reasons"])
        assert result["missing"] == []

    def test_growth_medium(self):
        hl = _make_medium_lead()
        result = _score_budget(hl)
        assert 10 <= result["score"] <= 18

    def test_starter_low(self):
        hl = _make_weak_lead()
        result = _score_budget(hl)
        assert result["score"] < 12

    def test_zero_adr_and_rooms(self):
        base = Lead(lead_id="l5", name="H")
        hl = HotelLead(hotel_lead_id="h5", base_lead=base, hotel_tier="Growth")
        result = _score_budget(hl)
        assert "average_daily_rate_placeholder" in result["missing"] or \
               "room_count_placeholder" in result["missing"]
        assert result["score"] >= 10  # Growth tier floor

    def test_premium_no_extras(self):
        base = Lead(lead_id="l6", name="P")
        hl = HotelLead(hotel_lead_id="h6", base_lead=base, hotel_tier="Premium")
        result = _score_budget(hl)
        assert result["score"] >= 15  # Premium alone


class TestAuthorityScoring:
    def test_owner_whatsapp(self):
        hl = _make_strong_lead()
        result = _score_authority(hl)
        assert result["score"] >= 20
        assert any("Proprietario" in r for r in result["reasons"])
        assert any("whatsapp" in r.lower() for r in result["reasons"])

    def test_manager_email(self):
        hl = _make_medium_lead()
        result = _score_authority(hl)
        assert 10 <= result["score"] <= 20
        assert any("Gerente" in r for r in result["reasons"])

    def test_no_decision_maker(self):
        hl = _make_weak_lead()
        result = _score_authority(hl)
        assert result["score"] <= 5
        assert "decision_maker_name" in result["missing"]

    def test_no_role(self):
        base = Lead(lead_id="l7", name="H", contact_channel="email")
        hl = HotelLead(
            hotel_lead_id="h7", base_lead=base,
            decision_maker_name="Joao Silva",
        )
        result = _score_authority(hl)
        assert result["score"] >= 10  # Has name
        assert "decision_maker_role" in result["missing"]

    def test_no_channel(self):
        base = Lead(lead_id="l8", name="H")
        hl = HotelLead(
            hotel_lead_id="h8", base_lead=base,
            decision_maker_name="Maria", decision_maker_role="CEO",
        )
        result = _score_authority(hl)
        assert "contact_channel" in result["missing"]


class TestNeedScoring:
    def test_resort_pacote_high_fit(self):
        hl = _make_strong_lead()
        result = _score_need(hl)
        assert result["score"] >= 20
        assert any("resort" in r for r in result["reasons"])

    def test_pousada_collab_medium(self):
        hl = _make_medium_lead()
        result = _score_need(hl)
        assert 20 <= result["score"] <= 25

    def test_hostel_low(self):
        hl = _make_weak_lead()
        result = _score_need(hl)
        assert result["score"] < 10

    def test_no_fit_score(self):
        base = Lead(lead_id="l9", name="H", interest="pacote")
        hl = HotelLead(hotel_lead_id="h9", base_lead=base, niche="resort")
        result = _score_need(hl)
        assert "fit_score" in result["missing"]

    def test_nordeste_bonus(self):
        base = Lead(lead_id="l10", name="H", interest="collab")
        hl = HotelLead(
            hotel_lead_id="h10", base_lead=base, niche="resort",
            fit_score=60, region="nordeste",
        )
        result = _score_need(hl)
        assert any("Nordeste" in r for r in result["reasons"])


class TestTimingScoring:
    def test_hot_indicacao(self):
        hl = _make_strong_lead()
        result = _score_timing(hl)
        assert result["score"] >= 20
        assert any("hot" in r.lower() for r in result["reasons"])

    def test_warm_instagram(self):
        hl = _make_medium_lead()
        result = _score_timing(hl)
        assert 10 <= result["score"] <= 18

    def test_cold_prospeccao(self):
        hl = _make_weak_lead()
        result = _score_timing(hl)
        assert result["score"] < 10

    def test_disqualified_zero(self):
        base = Lead(lead_id="l11", name="D", source="outro")
        hl = HotelLead(
            hotel_lead_id="h11", base_lead=base, priority_tier="disqualified",
        )
        result = _score_timing(hl)
        assert result["score"] <= 5

    def test_urgency_tags(self):
        base = Lead(lead_id="l12", name="U", tags=["verao", "urgente"], source="indicacao")
        hl = HotelLead(
            hotel_lead_id="h12", base_lead=base, priority_tier="hot",
        )
        result = _score_timing(hl)
        assert any("urgencia" in r.lower() or "verao" in r.lower() for r in result["reasons"])


# ── Tier Determination Tests ───────────────────────────────────────────────

class TestTierDetermination:
    def test_qualified(self):
        assert _determine_tier(85, 0) == QUALIFIED
        assert _determine_tier(70, 0) == QUALIFIED
        assert _determine_tier(100, 1) == QUALIFIED

    def test_nurture(self):
        assert _determine_tier(69, 0) == NURTURE
        assert _determine_tier(50, 1) == NURTURE
        assert _determine_tier(45, 1) == NURTURE

    def test_low_fit(self):
        assert _determine_tier(44, 0) == LOW_FIT
        assert _determine_tier(25, 1) == LOW_FIT
        assert _determine_tier(20, 2) == LOW_FIT

    def test_disqualified(self):
        assert _determine_tier(19, 0) == DISQUALIFIED
        assert _determine_tier(5, 1) == DISQUALIFIED
        assert _determine_tier(0, 2) == DISQUALIFIED

    def test_missing_info_overrides(self):
        assert _determine_tier(90, 3) == MISSING_INFO
        assert _determine_tier(50, 4) == MISSING_INFO
        assert _determine_tier(10, 3) == MISSING_INFO


# ── BANTResult Tests ───────────────────────────────────────────────────────

class TestBANTResult:
    def test_create_result(self):
        result = BANTResult(
            qualifier_id="q1", hotel_lead_id="h1", hotel_name="Resort Test",
            budget_score=20, authority_score=22, need_score=23, timing_score=21,
            total_score=86, qualification_tier=QUALIFIED,
            reasons=["Forte em todas as dimensoes"],
            risks=[],
            missing_information=[],
            recommended_next_action=TIER_NEXT_ACTIONS[QUALIFIED],
        )
        assert result.total_score == 86
        assert result.is_actionable is True
        assert result.dry_run is True

    def test_is_actionable_false(self):
        result = BANTResult(
            qualifier_id="q2", hotel_lead_id="h2", hotel_name="Cold Hotel",
            budget_score=3, authority_score=2, need_score=3, timing_score=1,
            total_score=9, qualification_tier=DISQUALIFIED,
        )
        assert result.is_actionable is False

    def test_max_score(self):
        result = BANTResult(
            qualifier_id="q3", hotel_lead_id="h3", hotel_name="H",
            budget_score=25, authority_score=25, need_score=25, timing_score=25,
            total_score=100, qualification_tier=QUALIFIED,
        )
        assert result.max_score == 100

    def test_to_dict_roundtrip(self):
        result = BANTResult(
            qualifier_id="q1", hotel_lead_id="h1", hotel_name="Resort Test",
            budget_score=20, authority_score=22, need_score=23, timing_score=21,
            total_score=86, qualification_tier=QUALIFIED,
            reasons=["Bom budget", "Autoridade clara", "Alta necessidade", "Timing quente"],
            risks=["Risco: concorrencia local"],
            missing_information=["room_count_placeholder"],
            recommended_next_action=TIER_NEXT_ACTIONS[QUALIFIED],
            dimension_details={
                "budget": {"score": 20, "reasons": ["Tier Premium"]},
            },
        )
        d = result.to_dict()
        restored = BANTResult.from_dict(d)
        assert restored.qualifier_id == "q1"
        assert restored.total_score == 86
        assert restored.qualification_tier == QUALIFIED
        assert "Bom budget" in restored.reasons
        assert "Risco: concorrencia local" in restored.risks
        assert "room_count_placeholder" in restored.missing_information

    def test_to_markdown(self):
        result = BANTResult(
            qualifier_id="q1", hotel_lead_id="h1", hotel_name="Resort Test",
            budget_score=20, authority_score=22, need_score=23, timing_score=21,
            total_score=86, qualification_tier=QUALIFIED,
            reasons=["Forte budget"],
            risks=["Risco teste"],
            missing_information=["Campo X"],
            recommended_next_action=TIER_NEXT_ACTIONS[QUALIFIED],
        )
        md = result.to_markdown()
        assert "Resort Test" in md
        assert "86/100" in md
        assert "QUALIFIED" in md.upper() or "qualified" in md.lower()
        assert "Risco teste" in md
        assert "Campo X" in md


# ── LeadQualifier Integration Tests ────────────────────────────────────────

class TestLeadQualifier:
    def test_qualify_strong_as_qualified(self):
        q = LeadQualifier()
        hl = _make_strong_lead()
        result = q.qualify(hl)
        assert result.qualification_tier == QUALIFIED
        assert result.total_score >= 70
        assert result.is_actionable is True
        assert len(result.reasons) >= 4  # At least one per dimension

    def test_qualify_medium_as_nurture(self):
        q = LeadQualifier()
        hl = _make_medium_lead()
        result = q.qualify(hl)
        assert result.qualification_tier in (NURTURE, QUALIFIED)
        assert result.total_score >= 40
        assert len(result.reasons) >= 3

    def test_qualify_weak_as_low_fit_or_disqualified(self):
        q = LeadQualifier()
        hl = _make_weak_lead()
        result = q.qualify(hl)
        assert result.qualification_tier in (LOW_FIT, DISQUALIFIED)
        assert result.total_score < 45
        assert len(result.risks) >= 1

    def test_qualify_missing_info(self):
        q = LeadQualifier()
        hl = _make_missing_info_lead()
        result = q.qualify(hl)
        assert result.qualification_tier == MISSING_INFO
        assert len(result.missing_information) >= 3

    def test_total_score_is_sum_of_dimensions(self):
        q = LeadQualifier()
        hl = _make_strong_lead()
        result = q.qualify(hl)
        expected = (result.budget_score + result.authority_score +
                    result.need_score + result.timing_score)
        assert result.total_score == expected

    def test_reasons_not_empty(self):
        q = LeadQualifier()
        hl = _make_strong_lead()
        result = q.qualify(hl)
        assert len(result.reasons) > 0

    def test_recommended_next_action_set(self):
        q = LeadQualifier()
        for hl, expected_tier in [
            (_make_strong_lead(), QUALIFIED),
            (_make_medium_lead(), NURTURE),
            (_make_weak_lead(), DISQUALIFIED),
            (_make_missing_info_lead(), MISSING_INFO),
        ]:
            result = q.qualify(hl)
            assert result.recommended_next_action != ""
            assert result.recommended_next_action == TIER_NEXT_ACTIONS.get(
                result.qualification_tier, ""
            )

    def test_all_dimensions_in_details(self):
        q = LeadQualifier()
        hl = _make_strong_lead()
        result = q.qualify(hl)
        for dim in ("budget", "authority", "need", "timing"):
            assert dim in result.dimension_details
            assert "score" in result.dimension_details[dim]
            assert "reasons" in result.dimension_details[dim]
            assert 0 <= result.dimension_details[dim]["score"] <= 25

    def test_qualify_batch_sorted(self):
        q = LeadQualifier()
        leads = [_make_weak_lead(), _make_strong_lead(), _make_medium_lead()]
        results = q.qualify_batch(leads)
        assert len(results) == 3
        # Sorted by total_score descending
        assert results[0].total_score >= results[1].total_score >= results[2].total_score

    def test_qualify_from_prospect_list(self):
        q = LeadQualifier()
        pl = ProspectList()
        pl.add(_make_strong_lead())
        pl.add(_make_medium_lead())
        pl.add(_make_weak_lead())

        results = q.qualify_from_prospect_list(pl)
        assert len(results) == 3
        assert results[0].total_score >= results[-1].total_score

    def test_summary_by_tier(self):
        q = LeadQualifier()
        results = [
            BANTResult(qualifier_id="q1", hotel_lead_id="h1", hotel_name="A",
                       budget_score=25, authority_score=25, need_score=25, timing_score=25,
                       total_score=100, qualification_tier=QUALIFIED),
            BANTResult(qualifier_id="q2", hotel_lead_id="h2", hotel_name="B",
                       budget_score=15, authority_score=15, need_score=15, timing_score=15,
                       total_score=60, qualification_tier=NURTURE),
            BANTResult(qualifier_id="q3", hotel_lead_id="h3", hotel_name="C",
                       budget_score=5, authority_score=5, need_score=5, timing_score=5,
                       total_score=20, qualification_tier=LOW_FIT),
        ]
        summary = q.summary_by_tier(results)
        assert summary[QUALIFIED] == 1
        assert summary[NURTURE] == 1
        assert summary[LOW_FIT] == 1
        assert summary[DISQUALIFIED] == 0

    def test_export_report(self):
        q = LeadQualifier()
        hl = _make_strong_lead()
        results = q.qualify_batch([hl])
        report = q.export_report(results)
        assert "BANT Qualification Report" in report
        assert "Resort Paradiso" in report
        assert str(results[0].total_score) in report

    def test_handles_placeholder_data(self):
        """Qualifier must handle placeholder/default data without crashing."""
        q = LeadQualifier()
        hl = _make_missing_info_lead()
        result = q.qualify(hl)
        # Should not crash, should produce valid result
        assert result.qualifier_id != ""
        assert result.qualification_tier == MISSING_INFO
        assert result.total_score >= 0
        assert result.total_score <= 100

    def test_no_external_api(self):
        q = LeadQualifier()
        hl = _make_strong_lead()
        result = q.qualify(hl)
        assert result.dry_run is True
        assert hl.dry_run is True
        assert hl.base_lead.dry_run is True

    def test_dry_run_default(self):
        q = LeadQualifier()
        hl = _make_strong_lead()
        result = q.qualify(hl)
        assert result.dry_run is True

    def test_qualification_tiers_complete(self):
        """All 5 tier values are defined with next actions."""
        for tier in [QUALIFIED, NURTURE, LOW_FIT, DISQUALIFIED, MISSING_INFO]:
            assert tier in QUALIFICATION_TIERS
            assert tier in TIER_NEXT_ACTIONS
            assert TIER_NEXT_ACTIONS[tier] != ""

    def test_scoring_is_deterministic(self):
        q = LeadQualifier()
        hl = _make_strong_lead()
        r1 = q.qualify(hl)
        r2 = q.qualify(hl)
        assert r1.total_score == r2.total_score
        assert r1.budget_score == r2.budget_score
        assert r1.qualification_tier == r2.qualification_tier

    def test_dimension_scores_in_range(self):
        q = LeadQualifier()
        for hl in [_make_strong_lead(), _make_medium_lead(), _make_weak_lead(),
                    _make_missing_info_lead()]:
            result = q.qualify(hl)
            assert 0 <= result.budget_score <= 25
            assert 0 <= result.authority_score <= 25
            assert 0 <= result.need_score <= 25
            assert 0 <= result.timing_score <= 25
            assert 0 <= result.total_score <= 100
