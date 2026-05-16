"""Tests for W129 — SDR Metrics & Dashboard Summary."""
from __future__ import annotations

import pytest

from src.sales.leads import Lead
from src.commercial.hotel_lead import HotelLead
from src.commercial.lead_qualifier import (
    BANTResult, LeadQualifier, QUALIFIED, NURTURE, DISQUALIFIED,
)
from src.commercial.package_matcher import PackageMatcher, PackageMatch
from src.commercial.proposal_brief import ProposalBriefBuilder, ProposalBrief
from src.commercial.pipeline_sync import (
    PipelineSyncBridge, PipelineSyncEntry, SyncStage,
)
from src.commercial.outreach_sequence import OutreachSequencer, OutreachChannel
from src.commercial.followup_schedule import FollowUpEntry, FollowUpSchedule
from src.commercial.sdr_metrics import (
    SDRMetricsSummary,
    SDRMetricsComputer,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_lead(hid: str, name: str, city: str, state: str, niche: str,
               tier: str, fit: int, priority: str,
               interest: str = "pacote", source: str = "indicacao") -> HotelLead:
    base = Lead(
        lead_id=hid, name=name, contact_channel="email", source=source,
        segment="hotel", interest=interest, tags=[niche], score=fit,
    )
    return HotelLead(
        hotel_lead_id=hid, base_lead=base, hotel_name=name,
        city=city, state=state, region="nordeste",
        hotel_tier=tier, niche=niche, fit_score=fit, priority_tier=priority,
    )


# ── SDRMetricsSummary Tests ────────────────────────────────────────────────

class TestSDRMetricsSummary:
    def test_create_empty(self):
        m = SDRMetricsSummary()
        assert m.total_leads == 0
        assert m.pipeline_health == "empty"

    def test_pipeline_health_strong(self):
        m = SDRMetricsSummary(
            total_leads=10, total_qualified=9,
            actionable_leads=5, bant_to_package_rate=0.8,
        )
        assert m.pipeline_health == "strong"

    def test_pipeline_health_healthy(self):
        m = SDRMetricsSummary(
            total_leads=10, total_qualified=6,
            actionable_leads=3, bant_to_package_rate=0.5,
        )
        assert m.pipeline_health == "healthy"

    def test_pipeline_health_weak(self):
        m = SDRMetricsSummary(
            total_leads=10, total_qualified=2,
            actionable_leads=1, bant_to_package_rate=0.2,
        )
        assert m.pipeline_health == "weak"

    def test_pipeline_health_attention(self):
        m = SDRMetricsSummary(
            total_leads=10, actionable_leads=3,
            followup_critical=3,
        )
        assert m.pipeline_health == "attention"

    def test_to_dict(self):
        m = SDRMetricsSummary(
            total_leads=5, total_qualified=3,
            actionable_leads=1,
            stage_distribution={"proposta": 2, "qualificado": 1},
            package_distribution={"Growth": 2, "Starter": 1},
            dashboard_summary="# Dashboard",
        )
        d = m.to_dict()
        assert d["total_leads"] == 5
        assert d["stage_distribution"]["proposta"] == 2
        assert d["dashboard_summary"] == "# Dashboard"
        assert d["pipeline_health"] in ("weak", "empty")


# ── SDRMetricsComputer Tests ───────────────────────────────────────────────

class TestSDRMetricsComputer:
    def test_compute_empty(self):
        computer = SDRMetricsComputer()
        m = computer.compute()
        assert m.total_leads == 0
        assert m.pipeline_health == "empty"
        assert m.dashboard_summary != ""

    def test_compute_with_bant_only(self):
        computer = SDRMetricsComputer()
        q = LeadQualifier()
        hl1 = _make_lead("h1", "Hotel A", "Natal", "RN", "resort",
                          "Premium", 90, "hot")
        hl2 = _make_lead("h2", "Hotel B", "Maceio", "AL", "pousada",
                          "Growth", 60, "warm")
        hl3 = _make_lead("h3", "Hotel C", "SP", "SP", "hostel",
                          "Starter", 10, "cold",
                          interest="", source="prospeccao")

        bant_results = [q.qualify(hl1), q.qualify(hl2), q.qualify(hl3)]
        m = computer.compute(bant_results=bant_results)
        assert m.total_leads == 3
        assert m.total_qualified >= 1
        assert m.qualification_rate >= 0.0
        assert m.avg_bant_score > 0

    def test_compute_full_pipeline(self):
        """Full pipeline: BANT → Package → Proposal → Sync → Outreach → FollowUp."""
        computer = SDRMetricsComputer()
        q = LeadQualifier()
        matcher = PackageMatcher()
        builder = ProposalBriefBuilder()
        bridge = PipelineSyncBridge()
        seqr = OutreachSequencer()

        hl1 = _make_lead("h1", "Resort Premium", "Natal", "RN", "resort",
                          "Premium", 90, "hot")
        hl2 = _make_lead("h2", "Pousada Media", "Maceio", "AL", "pousada",
                          "Growth", 60, "warm")

        # BANT
        bant = [q.qualify(hl1), q.qualify(hl2)]

        # Package
        pkg = [matcher.match(hl, br) for hl, br in zip([hl1, hl2], bant)]

        # Proposal
        proposals = [builder.build(pm, br, hl)
                     for hl, br, pm in zip([hl1, hl2], bant, pkg)
                     if pm.has_recommendation]

        # Sync — match proposals by hotel_lead_id
        pb_by_id = {pb.hotel_lead_id: pb for pb in proposals}
        sync = [bridge.sync(hl, br, pm, pb_by_id.get(hl.hotel_lead_id))
                for hl, br, pm in zip([hl1, hl2], bant, pkg)]

        # Outreach
        for hl in [hl1, hl2]:
            seqr.generate_sequence(hl, OutreachChannel.EMAIL)

        # Follow-up
        scheduler = FollowUpSchedule()
        followups = scheduler.build(seqr, sync)

        # Compute
        m = computer.compute(
            bant_results=bant,
            package_matches=pkg,
            proposal_briefs=proposals,
            pipeline_sync_entries=sync,
            outreach_sequences=seqr.list_all(),
            followup_entries=followups,
        )

        assert m.total_leads == 2
        assert m.total_qualified >= 1
        assert m.total_with_package >= 1
        assert m.total_in_outreach == 2
        assert m.followup_actions_total >= 2
        assert m.dashboard_summary != ""
        assert m.pipeline_health != "empty"

    def test_compute_dashboard_summary_sections(self):
        computer = SDRMetricsComputer()
        q = LeadQualifier()
        matcher = PackageMatcher()
        bridge = PipelineSyncBridge()

        hl = _make_lead("h1", "Hotel Test", "Natal", "RN", "resort",
                         "Premium", 90, "hot")
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        sync = bridge.sync(hl, br, pm)

        m = computer.compute(
            bant_results=[br],
            package_matches=[pm],
            pipeline_sync_entries=[sync],
        )

        summary = m.dashboard_summary
        assert "SDR Pipeline Dashboard" in summary
        assert "Pipeline Overview" in summary
        assert "Conversion Funnel" in summary
        assert "Package Distribution" in summary
        assert "Pipeline by Stage" in summary
        assert "**dry_run:** True" in summary

    def test_compute_stage_distribution(self):
        computer = SDRMetricsComputer()
        sync_entries = [
            PipelineSyncEntry(sync_id="s1", hotel_lead_id="h1", hotel_name="A",
                              suggested_stage=SyncStage.NEGOCIACAO, fit_score=90),
            PipelineSyncEntry(sync_id="s2", hotel_lead_id="h2", hotel_name="B",
                              suggested_stage=SyncStage.PROPOSTA, fit_score=70),
            PipelineSyncEntry(sync_id="s3", hotel_lead_id="h3", hotel_name="C",
                              suggested_stage=SyncStage.ARQUIVADO, fit_score=10),
        ]
        m = computer.compute(pipeline_sync_entries=sync_entries)
        assert m.stage_distribution[SyncStage.NEGOCIACAO] == 1
        assert m.stage_distribution[SyncStage.PROPOSTA] == 1
        assert m.stage_distribution[SyncStage.ARQUIVADO] == 1
        assert m.actionable_leads == 2
        assert m.non_actionable_leads == 1

    def test_compute_package_distribution(self):
        computer = SDRMetricsComputer()
        q = LeadQualifier()
        matcher = PackageMatcher()

        hl1 = _make_lead("h1", "Premium Hotel", "Natal", "RN", "resort",
                          "Premium", 95, "hot")
        hl2 = _make_lead("h2", "Growth Hotel", "Maceio", "AL", "pousada",
                          "Growth", 60, "warm")

        bant = [q.qualify(hl1), q.qualify(hl2)]
        pkg = [matcher.match(hl, br) for hl, br in zip([hl1, hl2], bant)]

        m = computer.compute(bant_results=bant, package_matches=pkg)
        assert m.total_with_package >= 1
        # Premium or Growth distribution present
        assert len(m.package_distribution) >= 1

    def test_compute_outreach_metrics(self):
        computer = SDRMetricsComputer()
        seqr = OutreachSequencer()

        hl1 = _make_lead("h1", "Active Lead", "Natal", "RN", "resort",
                          "Premium", 90, "hot")
        hl2 = _make_lead("h2", "Completed Lead", "Maceio", "AL", "pousada",
                          "Growth", 60, "warm")

        seqr.generate_sequence(hl1, OutreachChannel.EMAIL)
        seq2 = seqr.generate_sequence(hl2, OutreachChannel.EMAIL)

        # Complete hl2's sequence
        for step in seq2.steps:
            seq2.complete_step(step.step_number)

        m = computer.compute(outreach_sequences=seqr.list_all())
        assert m.total_in_outreach == 2
        assert m.outreach_active >= 1  # hl1 is active
        assert m.outreach_completed >= 1  # hl2 is completed

    def test_compute_followup_metrics(self):
        computer = SDRMetricsComputer()
        followups = [
            FollowUpEntry(entry_id="e1", hotel_lead_id="h1", hotel_name="A",
                          is_overdue=True, overdue_days=7, days_until_due=-7,
                          priority_rank=5, step_status="pending"),
            FollowUpEntry(entry_id="e2", hotel_lead_id="h2", hotel_name="B",
                          is_overdue=True, overdue_days=2, days_until_due=-2,
                          priority_rank=10, step_status="pending"),
            FollowUpEntry(entry_id="e3", hotel_lead_id="h3", hotel_name="C",
                          is_overdue=False, days_until_due=3, priority_rank=20,
                          step_status="ready"),
        ]
        m = computer.compute(followup_entries=followups)
        assert m.followup_actions_total == 3
        assert m.followup_overdue == 2
        assert m.followup_critical == 1  # only the 7-day overdue

    def test_compute_rates(self):
        computer = SDRMetricsComputer()
        q = LeadQualifier()
        matcher = PackageMatcher()
        builder = ProposalBriefBuilder()

        hl = _make_lead("h1", "Hotel", "Natal", "RN", "resort",
                         "Premium", 90, "hot")
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        pb = builder.build(pm, br, hl)

        m = computer.compute(
            bant_results=[br],
            package_matches=[pm],
            proposal_briefs=[pb],
        )
        assert 0.0 <= m.bant_to_package_rate <= 1.0
        assert 0.0 <= m.package_to_proposal_rate <= 1.0
        assert 0.0 <= m.qualification_rate <= 1.0

    def test_export_summary_dict(self):
        computer = SDRMetricsComputer()
        m = computer.compute()
        d = computer.export_summary_dict(m)
        assert isinstance(d, dict)
        assert "total_leads" in d
        assert "pipeline_health" in d

    def test_dry_run(self):
        computer = SDRMetricsComputer()
        q = LeadQualifier()
        hl = _make_lead("h1", "Hotel", "Natal", "RN", "resort",
                         "Premium", 90, "hot")
        br = q.qualify(hl)
        m = computer.compute(bant_results=[br])
        assert "dry_run" in m.dashboard_summary.lower()

    def test_deterministic(self):
        computer = SDRMetricsComputer()
        q = LeadQualifier()
        hl = _make_lead("h1", "Hotel", "Natal", "RN", "resort",
                         "Premium", 90, "hot")
        br = q.qualify(hl)
        m1 = computer.compute(bant_results=[br])
        m2 = computer.compute(bant_results=[br])
        assert m1.total_leads == m2.total_leads
        assert m1.pipeline_health == m2.pipeline_health
        assert m1.dashboard_summary == m2.dashboard_summary
