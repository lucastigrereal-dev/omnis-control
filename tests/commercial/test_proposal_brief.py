"""Tests for W126 — Commercial Proposal & Objection Brief."""
from __future__ import annotations

import pytest

from src.sales.leads import Lead
from src.commercial.hotel_lead import HotelLead
from src.commercial.lead_qualifier import (
    BANTResult, LeadQualifier,
    QUALIFIED, NURTURE, DISQUALIFIED,
)
from src.commercial.package_matcher import PackageMatcher, PackageMatch, PACKAGE_DETAILS
from src.commercial.proposal_brief import (
    ObjectionEntry,
    ProposalBrief,
    ProposalBriefBuilder,
    OBJECTION_TYPES,
    OBJECTION_RESPONSES,
    _commercial_angle,
    _talking_points,
    _expected_value,
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


def _make_qualified_package_match(hl: HotelLead) -> PackageMatch:
    matcher = PackageMatcher()
    q = LeadQualifier()
    br = q.qualify(hl)
    return matcher.match(hl, br)


# ── ObjectionEntry Tests ───────────────────────────────────────────────────

class TestObjectionEntry:
    def test_create(self):
        oe = ObjectionEntry(
            objection_type="preco",
            objection_text="Muito caro",
            response="Resposta preco",
            source="standard",
        )
        assert oe.objection_type == "preco"
        assert oe.source == "standard"

    def test_to_dict(self):
        oe = ObjectionEntry(
            objection_type="timing",
            objection_text="Agora nao",
            response="Sem pressa",
            source="standard",
        )
        d = oe.to_dict()
        assert d["objection_type"] == "timing"
        assert d["response"] == "Sem pressa"
        assert d["source"] == "standard"

    def test_source_default_empty(self):
        oe = ObjectionEntry(
            objection_type="preco", objection_text="X", response="Y",
        )
        assert oe.source == ""

    def test_bant_risk_source(self):
        oe = ObjectionEntry(
            objection_type="bant_risk",
            objection_text="Budget baixo",
            response="Risco mapeado",
            source="bant_risk",
        )
        assert oe.source == "bant_risk"


# ── ProposalBrief Tests ────────────────────────────────────────────────────

class TestProposalBrief:
    def test_create_with_package(self):
        brief = ProposalBrief(
            brief_id="b1", hotel_lead_id="h1", hotel_name="Hotel Test",
            recommended_package="Growth",
            offer_summary="Oferta Growth",
            commercial_angle="Angulo comercial",
            talking_points=["p1", "p2"],
            expected_value="Valor esperado",
            recommended_next_step="Enviar proposta",
        )
        assert brief.recommended_package == "Growth"
        assert brief.dry_run is True
        assert len(brief.talking_points) == 2

    def test_create_no_package(self):
        brief = ProposalBrief(
            brief_id="b2", hotel_lead_id="h2", hotel_name="Bad Hotel",
            recommended_package="",
        )
        assert brief.recommended_package == ""

    def test_total_objections(self):
        oe1 = ObjectionEntry(objection_type="preco", objection_text="X", response="Y")
        oe2 = ObjectionEntry(objection_type="timing", objection_text="X", response="Y")
        oe3 = ObjectionEntry(objection_type="bant_risk", objection_text="Z", response="W", source="bant_risk")
        brief = ProposalBrief(
            brief_id="b3", hotel_lead_id="h3", hotel_name="H",
            recommended_package="Growth",
            objection_map=[oe1, oe2],
            bant_risks_as_objections=[oe3],
        )
        assert brief.total_objections == 3

    def test_to_dict_roundtrip(self):
        oe = ObjectionEntry(objection_type="preco", objection_text="Caro", response="Resp", source="standard")
        brief = ProposalBrief(
            brief_id="b4", hotel_lead_id="h4", hotel_name="Hotel R",
            recommended_package="Premium",
            offer_summary="Oferta",
            commercial_angle="Angulo",
            talking_points=["tp1"],
            package_details={"price": "R$ 1.200"},
            expected_value="EV",
            objection_map=[oe],
            bant_risks_as_objections=[],
            recommended_next_step="Call",
            markdown_output="# MD",
        )
        d = brief.to_dict()
        restored = ProposalBrief.from_dict(d)
        assert restored.brief_id == "b4"
        assert restored.recommended_package == "Premium"
        assert restored.talking_points == ["tp1"]
        assert len(restored.objection_map) == 1
        assert restored.objection_map[0].objection_type == "preco"
        assert restored.markdown_output == "# MD"

    def test_from_dict_empty_lists(self):
        d = {
            "brief_id": "b5", "hotel_lead_id": "h5", "hotel_name": "H",
            "recommended_package": "Starter",
        }
        brief = ProposalBrief.from_dict(d)
        assert brief.objection_map == []
        assert brief.bant_risks_as_objections == []
        assert brief.talking_points == []


# ── Helper Function Tests ──────────────────────────────────────────────────

class TestCommercialAngle:
    def test_resort_angle(self):
        hl = _make_strong_lead()
        angle = _commercial_angle(hl)
        assert "Resort Paradiso" in angle
        assert "alta renda" in angle.lower()

    def test_pousada_angle(self):
        hl = _make_medium_lead()
        angle = _commercial_angle(hl)
        assert "Pousada Brisa" in angle
        assert "familia" in angle.lower()

    def test_fazenda_angle(self):
        base = Lead(lead_id="l6", name="Fazenda Vale", contact_channel="email",
                     source="indicacao", interest="collab")
        hl = HotelLead(
            hotel_lead_id="h6", base_lead=base, hotel_name="Fazenda Vale Verde",
            city="Serra Negra", state="SP", region="sudeste",
            hotel_tier="Growth", niche="fazenda", fit_score=70,
            decision_maker_name="Joao", decision_maker_role="Proprietario",
            priority_tier="warm",
        )
        angle = _commercial_angle(hl)
        assert "Fazenda Vale Verde" in angle
        assert "afamiliatigrereal" in angle

    def test_fallback_for_unknown_niche(self):
        base = Lead(lead_id="l7", name="Motel X", contact_channel="email",
                     source="prospeccao", interest="")
        hl = HotelLead(
            hotel_lead_id="h7", base_lead=base, hotel_name="Motel X",
            city="Campinas", state="SP", region="sudeste",
            hotel_tier="Starter", niche="urbano", fit_score=30,
            priority_tier="cold",
        )
        angle = _commercial_angle(hl)
        assert "Motel X" in angle
        assert "Campinas/SP" in angle


class TestTalkingPoints:
    def test_premium_talking_points(self):
        hl = _make_strong_lead()
        pts = _talking_points(hl, "Premium")
        assert len(pts) >= 6
        assert any("4 collabs" in p for p in pts)
        assert any("98%" in p for p in pts)

    def test_growth_talking_points(self):
        hl = _make_medium_lead()
        pts = _talking_points(hl, "Growth")
        assert len(pts) >= 6
        assert any("3 collabs" in p for p in pts)

    def test_starter_talking_points(self):
        hl = _make_weak_lead()
        pts = _talking_points(hl, "Starter")
        assert len(pts) >= 6
        assert any("1 collab" in p for p in pts)
        assert any("teste" in p.lower() for p in pts)

    def test_resultado_garantido_always_last(self):
        for hl, pkg in [(_make_strong_lead(), "Premium"),
                        (_make_medium_lead(), "Growth"),
                        (_make_weak_lead(), "Starter")]:
            pts = _talking_points(hl, pkg)
            assert "Resultado garantido" in pts[-1] or "risco zero" in pts[-1].lower()


class TestExpectedValue:
    def test_premium_value(self):
        hl = _make_strong_lead()
        ev = _expected_value(hl, "Premium")
        assert "1.5" in ev
        assert "R$1.200" in ev

    def test_growth_value(self):
        hl = _make_medium_lead()
        ev = _expected_value(hl, "Growth")
        assert "R$990" in ev

    def test_starter_value(self):
        hl = _make_weak_lead()
        ev = _expected_value(hl, "Starter")
        assert "R$350" in ev


# ── ProposalBriefBuilder Tests ─────────────────────────────────────────────

class TestProposalBriefBuilder:
    def test_build_from_qualified_match(self):
        builder = ProposalBriefBuilder()
        q = LeadQualifier()
        matcher = PackageMatcher()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        brief = builder.build(pm, br, hl)

        assert brief.recommended_package != ""
        assert brief.hotel_name == "Resort Paradiso"
        assert brief.offer_summary != ""
        assert brief.commercial_angle != ""
        assert len(brief.talking_points) >= 6
        assert brief.expected_value != ""
        assert len(brief.objection_map) == 6
        assert brief.markdown_output != ""
        assert brief.dry_run is True

    def test_build_markdown_contains_sections(self):
        builder = ProposalBriefBuilder()
        q = LeadQualifier()
        matcher = PackageMatcher()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        brief = builder.build(pm, br, hl)

        md = brief.markdown_output
        assert "Commercial Proposal Brief" in md
        assert "Resort Paradiso" in md
        assert "Offer Summary" in md
        assert "Commercial Angle" in md
        assert "Talking Points" in md
        assert "Package Details" in md
        assert "Expected Value" in md
        assert "Recommended Channels" in md
        assert "Suggested Profiles" in md
        assert "Objection Map" in md
        assert "Next Step" in md
        assert "**dry_run:** True" in md

    def test_build_objection_map_covers_all_types(self):
        builder = ProposalBriefBuilder()
        q = LeadQualifier()
        matcher = PackageMatcher()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        brief = builder.build(pm, br, hl)

        otypes = {o.objection_type for o in brief.objection_map}
        assert otypes == OBJECTION_TYPES

    def test_build_all_objections_have_responses(self):
        builder = ProposalBriefBuilder()
        q = LeadQualifier()
        matcher = PackageMatcher()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        brief = builder.build(pm, br, hl)

        for obj in brief.objection_map:
            assert obj.response != "", f"Empty response for {obj.objection_type}"
            assert obj.source == "standard"

    def test_build_bant_risks_as_objections(self):
        builder = ProposalBriefBuilder()
        q = LeadQualifier()
        matcher = PackageMatcher()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        brief = builder.build(pm, br, hl)

        for obj in brief.bant_risks_as_objections:
            assert obj.source == "bant_risk"
            assert obj.objection_type == "bant_risk"
            assert obj.response != ""

    def test_build_no_package_match(self):
        builder = ProposalBriefBuilder()
        hl = _make_weak_lead()
        br = BANTResult(
            qualifier_id="q1", hotel_lead_id="h3", hotel_name="Hostel",
            budget_score=5, authority_score=2, need_score=5, timing_score=0,
            total_score=12, qualification_tier=DISQUALIFIED,
        )
        pm = PackageMatch(
            match_id="m99", hotel_lead_id="h3", hotel_name="Hostel",
            bant_tier=DISQUALIFIED, recommended_package="",
        )
        brief = builder.build(pm, br, hl)
        assert brief.recommended_package == ""
        assert "No Proposal" in brief.markdown_output

    def test_build_for_disqualified(self):
        builder = ProposalBriefBuilder()
        hl = _make_weak_lead()
        br = BANTResult(
            qualifier_id="q2", hotel_lead_id="h3", hotel_name="Hostel",
            budget_score=5, authority_score=2, need_score=5, timing_score=0,
            total_score=12, qualification_tier=DISQUALIFIED,
            risks=["Budget muito baixo", "Sem autoridade identificada"],
        )
        brief = builder.build_for_disqualified(hl, br)
        assert brief.recommended_package == ""
        assert "No Proposal" in brief.markdown_output
        assert "Budget muito baixo" in brief.markdown_output

    def test_build_pousada_nurture(self):
        builder = ProposalBriefBuilder()
        q = LeadQualifier()
        matcher = PackageMatcher()
        hl = _make_medium_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        brief = builder.build(pm, br, hl)

        assert brief.hotel_name == "Pousada Brisa"
        assert len(brief.objection_map) == 6
        # Objection responses should adapt to package tier
        preco_obj = next(o for o in brief.objection_map if o.objection_type == "preco")
        assert preco_obj.response != ""

    def test_build_fazenda_niche_angle(self):
        builder = ProposalBriefBuilder()
        q = LeadQualifier()
        matcher = PackageMatcher()
        base = Lead(lead_id="l8", name="Fazenda Vale", contact_channel="email",
                     source="indicacao", interest="collab")
        hl = HotelLead(
            hotel_lead_id="h8", base_lead=base, hotel_name="Fazenda Vale Verde",
            city="Serra Negra", state="SP", region="sudeste",
            hotel_tier="Growth", niche="fazenda", fit_score=70,
            decision_maker_name="Joao", decision_maker_role="Proprietario",
            priority_tier="warm",
        )
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        brief = builder.build(pm, br, hl)

        assert "afamiliatigrereal" in brief.commercial_angle
        assert "Fazenda Vale Verde" in brief.markdown_output

    def test_dry_run_no_send(self):
        builder = ProposalBriefBuilder()
        q = LeadQualifier()
        matcher = PackageMatcher()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        brief = builder.build(pm, br, hl)

        assert brief.dry_run is True
        assert "**dry_run:** True" in brief.markdown_output
        assert "Nenhuma mensagem foi enviada" in brief.markdown_output

    def test_deterministic_same_input(self):
        builder = ProposalBriefBuilder()
        q = LeadQualifier()
        matcher = PackageMatcher()
        hl = _make_strong_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)

        b1 = builder.build(pm, br, hl)
        b2 = builder.build(pm, br, hl)
        assert b1.recommended_package == b2.recommended_package
        assert b1.commercial_angle == b2.commercial_angle
        assert b1.talking_points == b2.talking_points
        assert b1.objection_map[0].response == b2.objection_map[0].response

    def test_export_batch(self):
        builder = ProposalBriefBuilder()
        q = LeadQualifier()
        matcher = PackageMatcher()

        hl1 = _make_strong_lead()
        br1 = q.qualify(hl1)
        pm1 = matcher.match(hl1, br1)
        b1 = builder.build(pm1, br1, hl1)

        hl2 = _make_medium_lead()
        br2 = q.qualify(hl2)
        pm2 = matcher.match(hl2, br2)
        b2 = builder.build(pm2, br2, hl2)

        report = builder.export_batch([b1, b2])
        assert "Proposal Brief Batch Report" in report
        assert "Resort Paradiso" in report
        assert "Pousada Brisa" in report
        assert "**Total briefs:** 2" in report
        assert "**With recommendation:** 2" in report

    def test_export_batch_includes_no_match(self):
        builder = ProposalBriefBuilder()
        brief = ProposalBrief(
            brief_id="bn", hotel_lead_id="hn", hotel_name="No Match Hotel",
            recommended_package="",
            markdown_output="# No Proposal — No Match Hotel\nLead nao qualificado.",
        )
        report = builder.export_batch([brief])
        assert "No Match Hotel" in report
        assert "No Match" in report
        assert "**With recommendation:** 0" in report
        assert "0 objections" in report

    def test_objection_tone_adapts_by_tier(self):
        """Premium objections should differ from Starter objections for same type."""
        builder = ProposalBriefBuilder()
        q = LeadQualifier()
        matcher = PackageMatcher()

        # Strong → Premium
        hl_p = _make_strong_lead()
        br_p = q.qualify(hl_p)
        pm_p = matcher.match(hl_p, br_p)
        brief_p = builder.build(pm_p, br_p, hl_p)

        # Nurture basic lead that maps to Starter
        base = Lead(lead_id="ls", name="Hotel Simples", contact_channel="email",
                     source="instagram", interest="collab")
        hl_s = HotelLead(
            hotel_lead_id="hs", base_lead=base, hotel_name="Hotel Simples",
            city="Campinas", state="SP", region="sudeste",
            hotel_tier="Starter", niche="urbano", fit_score=50,
            decision_maker_name="Maria", decision_maker_role="Gerente",
            priority_tier="warm",
        )
        br_s = q.qualify(hl_s)
        pm_s = matcher.match(hl_s, br_s)
        brief_s = builder.build(pm_s, br_s, hl_s)

        assert brief_s.recommended_package != "", f"Expected Starter package, got: {brief_s.recommended_package}"
        preco_p = next(o for o in brief_p.objection_map if o.objection_type == "preco")
        preco_s = next(o for o in brief_s.objection_map if o.objection_type == "preco")
        assert preco_p.response != preco_s.response

    def test_starter_objection_price_mentions_low_risk(self):
        builder = ProposalBriefBuilder()
        q = LeadQualifier()
        matcher = PackageMatcher()
        hl = _make_weak_lead()
        br = q.qualify(hl)
        pm = matcher.match(hl, br)

        # Override with Starter if matched higher
        if pm.recommended_package != "Starter":
            pm.recommended_package = "Starter"
            pm.package_details = PACKAGE_DETAILS["Starter"]

        brief = builder.build(pm, br, hl)
        preco = next(o for o in brief.objection_map if o.objection_type == "preco")
        assert "R$350" in preco.response or "Starter" in preco.response
