"""Tests for W125 — Commercial Package Matcher."""
from __future__ import annotations

import pytest
from pathlib import Path

from src.sales.leads import Lead
from src.commercial.hotel_lead import HotelLead
from src.commercial.lead_qualifier import (
    BANTResult, LeadQualifier,
    QUALIFIED, NURTURE, LOW_FIT, DISQUALIFIED, MISSING_INFO,
    TIER_NEXT_ACTIONS,
)
from src.commercial.prospect_list import ProspectList
from src.commercial.package_matcher import (
    PackageMatch,
    PackageMatcher,
    PackageTier,
    PACKAGE_DETAILS,
    NICHE_PROFILES,
    CHANNEL_SUGGESTIONS,
    _generate_media_kit_brief,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_strong_lead() -> HotelLead:
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
        fit_score=10, priority_tier="cold",
    )


# ── PackageMatch Tests ─────────────────────────────────────────────────────

class TestPackageMatch:
    def test_create_match(self):
        m = PackageMatch(
            match_id="m1", hotel_lead_id="h1", hotel_name="Hotel Test",
            bant_tier=QUALIFIED, recommended_package="Growth",
            rationale=["Bom fit"], recommended_channels=["email", "whatsapp"],
            suggested_profiles=["@lucastigrereal (690K)"],
            package_details=PACKAGE_DETAILS["Growth"],
            media_kit_brief="Media kit placeholder",
            next_action="Enviar proposta",
        )
        assert m.recommended_package == "Growth"
        assert m.has_recommendation is True
        assert m.dry_run is True

    def test_no_recommendation(self):
        m = PackageMatch(
            match_id="m2", hotel_lead_id="h2", hotel_name="Bad Lead",
            bant_tier=DISQUALIFIED, recommended_package="",
            risk_notes=["Baixo fit"],
        )
        assert m.has_recommendation is False

    def test_to_dict_roundtrip(self):
        m = PackageMatch(
            match_id="m1", hotel_lead_id="h1", hotel_name="Hotel Test",
            bant_tier=QUALIFIED, recommended_package="Premium",
            rationale=["r1", "r2"], recommended_channels=["email"],
            suggested_profiles=["@a"], package_details=PACKAGE_DETAILS["Premium"],
            media_kit_brief="Media kit", risk_notes=["r1"],
            next_action="Enviar",
        )
        d = m.to_dict()
        restored = PackageMatch.from_dict(d)
        assert restored.match_id == "m1"
        assert restored.recommended_package == "Premium"
        assert restored.rationale == ["r1", "r2"]
        assert restored.risk_notes == ["r1"]

    def test_to_markdown_with_match(self):
        m = PackageMatch(
            match_id="m1", hotel_lead_id="h1", hotel_name="Hotel Test",
            bant_tier=QUALIFIED, recommended_package="Growth",
            rationale=["Bom ajuste"], recommended_channels=["email"],
            suggested_profiles=["@lucastigrereal (690K)"],
            package_details=PACKAGE_DETAILS["Growth"],
            media_kit_brief="## Media Kit Brief",
            next_action="Enviar proposta",
        )
        md = m.to_markdown()
        assert "Hotel Test" in md
        assert "Growth" in md
        assert "Media Kit Brief" in md

    def test_to_markdown_no_match(self):
        m = PackageMatch(
            match_id="m2", hotel_lead_id="h2", hotel_name="Bad Hotel",
            bant_tier=DISQUALIFIED, recommended_package="",
        )
        md = m.to_markdown()
        assert "NO MATCH" in md


# ── PackageMatcher Tests ───────────────────────────────────────────────────

class TestPackageMatcher:
    def test_match_qualified_premium_resort(self):
        matcher = PackageMatcher()
        q = LeadQualifier()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        result = matcher.match(hl, br)
        assert result.recommended_package in (PackageTier.GROWTH.value, PackageTier.PREMIUM.value)
        assert len(result.rationale) >= 2
        assert result.has_recommendation is True

    def test_match_nurture_growth_pousada(self):
        matcher = PackageMatcher()
        q = LeadQualifier()
        hl = _make_medium_lead()
        br = q.qualify(hl)
        result = matcher.match(hl, br)
        assert result.recommended_package in (PackageTier.GROWTH.value, PackageTier.STARTER.value)
        assert len(result.rationale) >= 1

    def test_match_low_fit_with_reservation(self):
        matcher = PackageMatcher()
        q = LeadQualifier()
        hl = _make_weak_lead()
        br = q.qualify(hl)
        result = matcher.match(hl, br)
        # Should either recommend with caveats or not recommend
        assert (result.recommended_package in (PackageTier.STARTER.value, "")
                or not result.has_recommendation)

    def test_match_disqualified_no_recommendation(self):
        matcher = PackageMatcher()
        hl = _make_weak_lead()
        br = BANTResult(
            qualifier_id="q1", hotel_lead_id="h3", hotel_name="Hostel",
            budget_score=5, authority_score=2, need_score=5, timing_score=0,
            total_score=12, qualification_tier=DISQUALIFIED,
        )
        result = matcher.match(hl, br)
        assert result.recommended_package == ""
        assert result.has_recommendation is False

    def test_match_fazenda_niche(self):
        matcher = PackageMatcher()
        q = LeadQualifier()
        base = Lead(lead_id="l4", name="Fazenda Vale", contact_channel="email",
                     source="indicacao", interest="collab")
        hl = HotelLead(
            hotel_lead_id="h4", base_lead=base, hotel_name="Fazenda Vale Verde",
            city="Serra Negra", state="SP", region="sudeste",
            hotel_tier="Growth", niche="fazenda", fit_score=70,
            decision_maker_name="Joao", decision_maker_role="Proprietario",
            priority_tier="warm",
        )
        br = q.qualify(hl)
        result = matcher.match(hl, br)
        assert result.has_recommendation is True
        assert len(result.recommended_package) > 0
        # Should suggest family profiles for fazenda
        assert any("@afamiliatigrereal" in p for p in result.suggested_profiles)

    def test_media_kit_brief_content(self):
        matcher = PackageMatcher()
        q = LeadQualifier()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        result = matcher.match(hl, br)
        assert result.media_kit_brief != ""
        assert "Resort Paradiso" in result.media_kit_brief
        assert "Media Kit" in result.media_kit_brief

    def test_rationale_not_empty(self):
        matcher = PackageMatcher()
        q = LeadQualifier()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        result = matcher.match(hl, br)
        assert len(result.rationale) >= 1

    def test_package_always_valid_tier(self):
        matcher = PackageMatcher()
        q = LeadQualifier()
        for hl in [_make_strong_lead(), _make_medium_lead(), _make_weak_lead()]:
            br = q.qualify(hl)
            result = matcher.match(hl, br)
            if result.recommended_package:
                assert result.recommended_package in (
                    PackageTier.STARTER.value,
                    PackageTier.GROWTH.value,
                    PackageTier.PREMIUM.value,
                )

    def test_deterministic_same_input(self):
        matcher = PackageMatcher()
        q = LeadQualifier()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        r1 = matcher.match(hl, br)
        r2 = matcher.match(hl, br)
        assert r1.recommended_package == r2.recommended_package
        assert r1.rationale == r2.rationale

    def test_match_batch_sorted(self):
        matcher = PackageMatcher()
        q = LeadQualifier()
        leads = [_make_weak_lead(), _make_strong_lead(), _make_medium_lead()]
        bant_results = [q.qualify(hl) for hl in leads]
        results = matcher.match_batch(leads, bant_results)
        assert len(results) == 3
        # First should be the strong lead (has recommendation, highest package)
        assert results[0].has_recommendation

    def test_match_from_prospect_list(self):
        matcher = PackageMatcher()
        q = LeadQualifier()
        pl = ProspectList()
        pl.add(_make_strong_lead())
        pl.add(_make_medium_lead())

        bant_results = [q.qualify(e.hotel_lead) for e in pl.list_all()]
        results = matcher.match_from_prospect_list(pl, bant_results)
        assert len(results) == 2

    def test_summary_by_package(self):
        matcher = PackageMatcher()
        matches = [
            PackageMatch(match_id="m1", hotel_lead_id="h1", hotel_name="A",
                         bant_tier=QUALIFIED, recommended_package="Premium"),
            PackageMatch(match_id="m2", hotel_lead_id="h2", hotel_name="B",
                         bant_tier=NURTURE, recommended_package="Growth"),
            PackageMatch(match_id="m3", hotel_lead_id="h3", hotel_name="C",
                         bant_tier=NURTURE, recommended_package="Growth"),
            PackageMatch(match_id="m4", hotel_lead_id="h4", hotel_name="D",
                         bant_tier=DISQUALIFIED, recommended_package=""),
        ]
        summary = matcher.summary_by_package(matches)
        assert summary["Premium"] == 1
        assert summary["Growth"] == 2
        assert summary["no_match"] == 1

    def test_export_report(self):
        matcher = PackageMatcher()
        q = LeadQualifier()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        m = matcher.match(hl, br)
        report = matcher.export_report([m])
        assert "Package Match Report" in report
        assert "Resort Paradiso" in report

    def test_dry_run_and_no_network(self):
        matcher = PackageMatcher()
        q = LeadQualifier()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        result = matcher.match(hl, br)
        assert result.dry_run is True
        assert hl.dry_run is True

    def test_channels_by_package(self):
        for tier, channels in CHANNEL_SUGGESTIONS.items():
            assert len(channels) >= 1
            for ch in channels:
                assert ch in ("email", "whatsapp", "instagram_dm", "call")

    def test_niche_profiles_all_covered(self):
        hot_top_niches = {"resort", "pousada", "boutique", "fazenda", "urbano",
                           "hostel", "eco_resort", "glamping", "apart_hotel", "hotel"}
        for niche in hot_top_niches:
            assert niche in NICHE_PROFILES


class TestMediaKitBrief:
    def test_generate_for_resort(self):
        hl = _make_strong_lead()
        brief = _generate_media_kit_brief(hl, "Premium")
        assert "Resort Paradiso" in brief
        assert "Media Kit" in brief
        assert "Premium" in brief
        assert "resort" in brief.lower()

    def test_generate_for_pousada(self):
        hl = _make_medium_lead()
        brief = _generate_media_kit_brief(hl, "Growth")
        assert "Pousada Brisa" in brief
        assert "familia" in brief.lower()
