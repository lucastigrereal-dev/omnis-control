"""W130 — Commercial SDR E2E + Safety Audit.

End-to-end test covering full Grupo 13 pipeline:
HotelLead → ProspectList → Outreach → BANT → Package → Proposal →
PipelineSync → FollowUpSchedule → Metrics → Safety Audit.

Validates: zero API, zero real send, dry_run enforced, determinism,
no legacy module rewrite, all contracts W121-W129 integrated.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.sales.leads import Lead
from src.commercial.hotel_lead import HotelLead
from src.commercial.prospect_list import ProspectList
from src.commercial.outreach_sequence import (
    OutreachSequencer, OutreachChannel, OutreachSequence, StepStatus,
)
from src.commercial.lead_qualifier import (
    LeadQualifier, BANTResult,
    QUALIFIED, NURTURE, LOW_FIT, DISQUALIFIED, MISSING_INFO,
)
from src.commercial.package_matcher import (
    PackageMatcher, PackageMatch, PackageTier, NICHE_PROFILES, CHANNEL_SUGGESTIONS,
)
from src.commercial.proposal_brief import (
    ProposalBriefBuilder, ProposalBrief, ObjectionEntry, OBJECTION_TYPES,
)
from src.commercial.pipeline_sync import (
    PipelineSyncBridge, PipelineSyncEntry, SyncStage, STAGE_ORDER,
)
from src.commercial.followup_schedule import (
    FollowUpSchedule, FollowUpEntry,
)
from src.commercial.sdr_metrics import (
    SDRMetricsComputer, SDRMetricsSummary,
)


# ── Full Pipeline E2E Test ─────────────────────────────────────────────────

class TestCommercialSDRE2E:
    """End-to-end: full Grupo 13 Commercial SDR pipeline."""

    def test_e2e_full_pipeline_single_lead(self):
        """Single lead from creation through all 9 waves to metrics."""
        # W121 — HotelLead
        base = Lead(
            lead_id="l_e2e", name="Resort Paradiso E2E",
            contact_channel="whatsapp", source="indicacao",
            segment="hotel", interest="pacote",
            tags=["resort", "praia", "oportunidade"], score=90,
        )
        hl = HotelLead(
            hotel_lead_id="h_e2e", base_lead=base,
            hotel_name="Resort Paradiso E2E",
            city="Porto de Galinhas", state="PE", region="nordeste",
            hotel_tier="Premium", niche="resort",
            room_count_placeholder=120, average_daily_rate_placeholder=850.0,
            decision_maker_name="Carlos Mendes",
            decision_maker_role="Proprietario",
            fit_score=90, priority_tier="hot",
        )
        assert hl.is_pursuable
        assert hl.dry_run is True

        # W122 — ProspectList
        pl = ProspectList()
        pl.add(hl)
        assert pl.count == 1
        assert len(pl.filter_pursuable()) == 1

        # W123 — OutreachSequencer
        seqr = OutreachSequencer()
        seq = seqr.generate_sequence(hl, OutreachChannel.WHATSAPP)
        assert seq.status == "active"
        assert seq.total_steps == 3
        assert seq.steps[0].status == StepStatus.READY
        assert seq.dry_run is True
        # Verify no real send
        for step in seq.steps:
            if step.message:
                assert step.message.sent is False
                assert step.message.dry_run is True

        # W124 — BANT Qualification
        q = LeadQualifier()
        br = q.qualify(hl)
        assert br.qualification_tier == QUALIFIED
        assert br.total_score >= 70
        assert len(br.reasons) >= 1

        # W125 — Package Matcher
        matcher = PackageMatcher()
        pm = matcher.match(hl, br)
        assert pm.has_recommendation
        assert pm.recommended_package in (
            PackageTier.PREMIUM.value, PackageTier.GROWTH.value,
        )
        assert len(pm.rationale) >= 2
        assert len(pm.recommended_channels) >= 1
        assert pm.media_kit_brief != ""
        assert pm.dry_run is True

        # W126 — Proposal Brief
        builder = ProposalBriefBuilder()
        pb = builder.build(pm, br, hl)
        assert pb.recommended_package != ""
        assert pb.hotel_name == "Resort Paradiso E2E"
        assert len(pb.objection_map) == 6
        assert pb.markdown_output != ""
        assert pb.dry_run is True

        # W127 — Pipeline Sync
        bridge = PipelineSyncBridge()
        sync_entry = bridge.sync(hl, br, pm, pb)
        assert sync_entry.suggested_stage == SyncStage.NEGOCIACAO
        assert sync_entry.is_actionable
        assert sync_entry.meeting_brief != ""
        assert sync_entry.dry_run is True

        # W128 — Follow-Up Schedule
        scheduler = FollowUpSchedule()
        followups = scheduler.build(seqr, [sync_entry])
        assert len(followups) >= 1
        assert followups[0].hotel_name == "Resort Paradiso E2E"
        best = scheduler.next_best_action(followups)
        assert best is not None
        assert best.dry_run is True

        # W129 — SDR Metrics
        computer = SDRMetricsComputer()
        metrics = computer.compute(
            bant_results=[br],
            package_matches=[pm],
            proposal_briefs=[pb],
            pipeline_sync_entries=[sync_entry],
            outreach_sequences=seqr.list_all(),
            followup_entries=followups,
        )
        assert metrics.total_leads == 1
        assert metrics.total_qualified == 1
        assert metrics.total_with_package == 1
        assert metrics.total_with_proposal == 1
        assert metrics.total_in_outreach == 1
        assert metrics.followup_actions_total >= 1
        assert metrics.pipeline_health in ("strong", "healthy")
        assert metrics.dashboard_summary != ""

    def test_e2e_multiple_leads_different_paths(self):
        """Multiple leads: strong → full pipeline, weak → disqualified."""
        # Strong
        base1 = Lead(lead_id="l_strong", name="Strong Resort",
                     contact_channel="whatsapp", source="indicacao",
                     interest="pacote", tags=["resort"], score=90)
        hl_strong = HotelLead(
            hotel_lead_id="h_strong", base_lead=base1,
            hotel_name="Strong Resort", city="Natal", state="RN",
            region="nordeste", hotel_tier="Premium", niche="resort",
            fit_score=90, priority_tier="hot",
        )

        # Weak
        base2 = Lead(lead_id="l_weak", name="Weak Hostel",
                     contact_channel="", source="prospeccao",
                     interest="", tags=["hostel"], score=10)
        hl_weak = HotelLead(
            hotel_lead_id="h_weak", base_lead=base2,
            hotel_name="Weak Hostel", city="SP", state="SP",
            region="sudeste", hotel_tier="Starter", niche="hostel",
            fit_score=10, priority_tier="cold",
        )

        # ProspectList
        pl = ProspectList()
        pl.add(hl_strong)
        pl.add(hl_weak)

        # Outreach for both
        seqr = OutreachSequencer()
        seqr.generate_sequence(hl_strong, OutreachChannel.EMAIL)
        seqr.generate_sequence(hl_weak, OutreachChannel.EMAIL)

        # BANT
        q = LeadQualifier()
        br_strong = q.qualify(hl_strong)
        br_weak = q.qualify(hl_weak)
        assert br_strong.qualification_tier in (QUALIFIED, NURTURE)
        assert br_weak.qualification_tier in (LOW_FIT, DISQUALIFIED, MISSING_INFO)

        # Package
        matcher = PackageMatcher()
        pm_strong = matcher.match(hl_strong, br_strong)
        pm_weak = matcher.match(hl_weak, br_weak)
        assert pm_strong.has_recommendation
        assert not pm_weak.has_recommendation

        # Pipeline Sync
        bridge = PipelineSyncBridge()
        sync_strong = bridge.sync(hl_strong, br_strong, pm_strong)
        sync_weak = bridge.sync(hl_weak, br_weak, pm_weak)
        assert sync_strong.is_actionable
        assert not sync_weak.is_actionable

        # Metrics
        computer = SDRMetricsComputer()
        metrics = computer.compute(
            bant_results=[br_strong, br_weak],
            package_matches=[pm_strong, pm_weak],
            pipeline_sync_entries=[sync_strong, sync_weak],
            outreach_sequences=seqr.list_all(),
        )
        assert metrics.total_leads == 2
        assert metrics.actionable_leads == 1
        assert metrics.non_actionable_leads == 1

    def test_e2e_batch_workflow(self):
        """Batch workflow: ProspectList → batch BANT → batch Package → batch Sync."""
        q = LeadQualifier()
        matcher = PackageMatcher()
        bridge = PipelineSyncBridge()
        seqr = OutreachSequencer()

        leads = []
        for i, (name, city, niche, tier, fit, priority) in enumerate([
            ("Resort A", "Natal", "resort", "Premium", 90, "hot"),
            ("Pousada B", "Maragogi", "pousada", "Growth", 65, "warm"),
            ("Hotel C", "Recife", "hotel", "Growth", 50, "warm"),
        ]):
            base = Lead(lead_id=f"b{i}", name=name, contact_channel="email",
                         source="instagram", interest="collab", tags=[niche], score=fit)
            hl = HotelLead(
                hotel_lead_id=f"b{i}", base_lead=base, hotel_name=name,
                city=city, state="RN" if city != "Maragogi" else "AL",
                region="nordeste", hotel_tier=tier, niche=niche,
                fit_score=fit, priority_tier=priority,
            )
            leads.append(hl)
            seqr.generate_sequence(hl, OutreachChannel.EMAIL)

        # Batch BANT
        bant_results = q.qualify_batch(leads)
        assert len(bant_results) == 3

        # Batch Package
        pkg_matches = [matcher.match(hl, br) for hl, br in zip(leads, bant_results)]

        # Batch Sync
        sync_entries = bridge.sync_batch(leads, bant_results, pkg_matches)
        assert len(sync_entries) == 3

        # Follow-up schedule for batch
        scheduler = FollowUpSchedule()
        followups = scheduler.build(seqr, sync_entries)

        # Metrics
        computer = SDRMetricsComputer()
        metrics = computer.compute(
            bant_results=bant_results,
            package_matches=pkg_matches,
            pipeline_sync_entries=sync_entries,
            outreach_sequences=seqr.list_all(),
            followup_entries=followups,
        )
        assert metrics.total_leads == 3
        assert metrics.total_qualified >= 1
        assert metrics.dashboard_summary != ""


# ── Safety Audit ───────────────────────────────────────────────────────────

class TestCommercialSDRSafetyAudit:
    """Safety audit: validates rules that apply across all Grupo 13 waves."""

    def test_zero_api_external_calls(self):
        """No module in commercial/ makes network calls."""
        import inspect
        from pathlib import Path

        commercial_dir = Path("src/commercial")
        for f in commercial_dir.glob("*.py"):
            if f.name.startswith("_"):
                continue
            content = f.read_text(encoding="utf-8")
            # No requests, urllib, httpx, aiohttp
            assert "requests." not in content, f"{f.name} imports requests"
            assert "urllib" not in content, f"{f.name} imports urllib"
            assert "httpx" not in content, f"{f.name} imports httpx"
            assert "aiohttp" not in content, f"{f.name} imports aiohttp"

    def test_zero_real_send(self):
        """No module sends real messages."""
        commercial_dir = Path("src/commercial")
        for f in commercial_dir.glob("*.py"):
            if f.name.startswith("_"):
                continue
            content = f.read_text(encoding="utf-8")
            # sent=False is the universal default
            if "sent" in content and "sent=False" not in content:
                # Check that sent is never set to True
                assert "sent = True" not in content, f"{f.name} has sent = True"
                assert "sent=True" not in content, f"{f.name} has sent=True"

    def test_dry_run_default_all_modules(self):
        """Every PipelineSyncEntry, PackageMatch, FollowUpEntry, etc. defaults dry_run=True."""
        from src.commercial.pipeline_sync import PipelineSyncEntry
        from src.commercial.package_matcher import PackageMatch
        from src.commercial.followup_schedule import FollowUpEntry
        from src.commercial.proposal_brief import ProposalBrief, ObjectionEntry
        from src.commercial.outreach_sequence import OutreachMessage, OutreachStep
        from src.commercial.hotel_lead import HotelLead
        from src.commercial.lead_qualifier import BANTResult

        # Create instances and verify dry_run
        e = PipelineSyncEntry(sync_id="t", hotel_lead_id="t", hotel_name="t")
        assert e.dry_run is True

        pm = PackageMatch(match_id="t", hotel_lead_id="t", hotel_name="t",
                          bant_tier=DISQUALIFIED, recommended_package="")
        assert pm.dry_run is True

        fe = FollowUpEntry(entry_id="t", hotel_lead_id="t", hotel_name="t")
        assert fe.dry_run is True

        pb = ProposalBrief(brief_id="t", hotel_lead_id="t", hotel_name="t",
                           recommended_package="")
        assert pb.dry_run is True

        oe = ObjectionEntry(objection_type="preco", objection_text="X", response="Y")
        # ObjectionEntry doesn't have dry_run — it's embedded in ProposalBrief

    def test_determinism_across_pipeline(self):
        """Same inputs → same outputs across key pipeline stages."""
        q = LeadQualifier()
        matcher = PackageMatcher()
        bridge = PipelineSyncBridge()

        base = Lead(lead_id="det", name="Det Hotel", contact_channel="email",
                     source="instagram", interest="collab", tags=["resort"], score=80)
        hl = HotelLead(
            hotel_lead_id="det", base_lead=base, hotel_name="Det Hotel",
            city="Natal", state="RN", region="nordeste",
            hotel_tier="Premium", niche="resort", fit_score=80, priority_tier="hot",
        )

        br1, br2 = q.qualify(hl), q.qualify(hl)
        assert br1.total_score == br2.total_score
        assert br1.qualification_tier == br2.qualification_tier

        pm1, pm2 = matcher.match(hl, br1), matcher.match(hl, br2)
        assert pm1.recommended_package == pm2.recommended_package

        se1, se2 = bridge.sync(hl, br1, pm1), bridge.sync(hl, br2, pm2)
        assert se1.suggested_stage == se2.suggested_stage

    def test_no_legacy_module_rewrite(self):
        """Commercial modules do not import from src/commercial_sdr/ or src/sales_crm/."""
        import re
        commercial_dir = Path("src/commercial")
        for f in commercial_dir.glob("*.py"):
            if f.name.startswith("_"):
                continue
            content = f.read_text(encoding="utf-8")
            for line in content.splitlines():
                if re.match(r'\s*(from|import)\s+.*(commercial_sdr|sales_crm)', line):
                    raise AssertionError(
                        f"{f.name}:{line.strip()} imports legacy module"
                    )

    def test_no_src_sales_import(self):
        """Commercial modules do not import from src/sales/ (pipeline, dashboard etc)."""
        commercial_dir = Path("src/commercial")
        for f in commercial_dir.glob("*.py"):
            if f.name.startswith("_"):
                continue
            content = f.read_text(encoding="utf-8")
            # Only hotel_lead.py and test files may import Lead from src.sales.leads
            if f.name == "hotel_lead.py":
                continue
            assert "from src.sales.pipeline" not in content, (
                f"{f.name} imports from src.sales.pipeline"
            )
            assert "from src.sales.dashboard" not in content, (
                f"{f.name} imports from src.sales.dashboard"
            )

    def test_all_contracts_integrated(self):
        """Every W121-W129 module is importable and has key classes accessible."""
        from src.commercial.hotel_lead import HotelLead, HotelLeadRegistry
        from src.commercial.prospect_list import ProspectList, ProspectEntry
        from src.commercial.outreach_sequence import OutreachSequencer, OutreachSequence
        from src.commercial.lead_qualifier import LeadQualifier, BANTResult
        from src.commercial.package_matcher import PackageMatcher, PackageMatch
        from src.commercial.proposal_brief import ProposalBriefBuilder, ProposalBrief
        from src.commercial.pipeline_sync import PipelineSyncBridge, PipelineSyncEntry
        from src.commercial.followup_schedule import FollowUpSchedule, FollowUpEntry
        from src.commercial.sdr_metrics import SDRMetricsComputer, SDRMetricsSummary

        # All imports successful — contracts integrated
        assert True

    def test_no_env_or_credentials(self):
        """No commercial module reads .env or credentials."""
        commercial_dir = Path("src/commercial")
        for f in commercial_dir.glob("*.py"):
            if f.name.startswith("_"):
                continue
            content = f.read_text(encoding="utf-8")
            assert "load_dotenv" not in content, f"{f.name} calls load_dotenv"
            assert "os.getenv" not in content, f"{f.name} calls os.getenv"
            assert "os.environ" not in content, f"{f.name} reads os.environ"

    def test_package_matcher_no_sales_proposals_import(self):
        """W125 mirrors PACKAGE_DETAILS — does NOT import src/sales/proposals.py."""
        content = Path("src/commercial/package_matcher.py").read_text(encoding="utf-8")
        assert "from src.sales.proposals" not in content
        assert "import src.sales.proposals" not in content


# ── Grupo 13 Integrity Check ───────────────────────────────────────────────

class TestGrupo13Integrity:
    """Cross-wave integrity: composition, tier alignment, stage consistency."""

    def test_hotel_lead_composes_lead_not_inherits(self):
        """W121: HotelLead composes Lead, not inherits."""
        base = Lead(lead_id="l", name="Test", contact_channel="email",
                     source="test", interest="test")
        hl = HotelLead(hotel_lead_id="h", base_lead=base, hotel_name="Test")
        assert hl.base_lead is base
        assert hl.name == "Test"  # proxy property

    def test_package_tiers_consistent(self):
        """Package tiers Starter/Growth/Premium are consistent across modules."""
        from src.commercial.package_matcher import PACKAGE_DETAILS
        from src.commercial.proposal_brief import OBJECTION_RESPONSES

        # PACKAGE_DETAILS has all 3 tiers
        for tier in ("Starter", "Growth", "Premium"):
            assert tier in PACKAGE_DETAILS
            assert "price" in PACKAGE_DETAILS[tier]

        # OBJECTION_RESPONSES has preco at minimum for all tiers
        for tier in ("Starter", "Growth", "Premium"):
            assert tier in OBJECTION_RESPONSES["preco"]

    def test_pipeline_stages_mirrored_correctly(self):
        """SyncStage mirrors src/sales/pipeline.py::PipelineStage exactly."""
        from src.sales.pipeline import PipelineStage
        from src.commercial.pipeline_sync import SyncStage

        sales_stages = {s.value for s in PipelineStage}
        sync_stages = {
            SyncStage.NOVO, SyncStage.QUALIFICADO, SyncStage.PROPOSTA,
            SyncStage.NEGOCIACAO, SyncStage.FECHADO, SyncStage.PERDIDO,
            SyncStage.ARQUIVADO,
        }
        assert sync_stages == sales_stages

    def test_niche_coverage_consistent(self):
        """Niche profiles and commercial angles cover the same niches."""
        from src.commercial.package_matcher import NICHE_PROFILES
        from src.commercial.proposal_brief import _commercial_angle

        # NICHE_PROFILES has 10 entries
        assert len(NICHE_PROFILES) == 10

        # All HOTEL_NICHE_VALUES have profile entries
        from src.commercial.hotel_lead import HOTEL_NICHE_VALUES
        for niche in HOTEL_NICHE_VALUES:
            assert niche in NICHE_PROFILES, f"Missing NICHE_PROFILES entry for {niche}"

    def test_bant_tiers_and_sync_stages_aligned(self):
        """BANT tiers and SyncStage values form a coherent pipeline."""
        # All BANT tiers are strings
        tiers = {QUALIFIED, NURTURE, LOW_FIT, DISQUALIFIED, MISSING_INFO}
        for t in tiers:
            assert isinstance(t, str)
            assert len(t) > 0

        # All sync stages map to valid pipeline positions
        for stage in STAGE_ORDER:
            assert stage in (
                SyncStage.NOVO, SyncStage.QUALIFICADO, SyncStage.PROPOSTA,
                SyncStage.NEGOCIACAO, SyncStage.FECHADO,
            )

    def test_channel_values_consistent(self):
        """Channel enums/suggestions use same base values."""
        from src.commercial.outreach_sequence import OutreachChannel
        from src.commercial.package_matcher import CHANNEL_SUGGESTIONS

        valid_channels = {ch.value for ch in OutreachChannel}
        for tier_channels in CHANNEL_SUGGESTIONS.values():
            for ch in tier_channels:
                assert ch in valid_channels, f"Unknown channel: {ch}"
