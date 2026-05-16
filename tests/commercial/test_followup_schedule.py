"""Tests for W128 — Follow-Up Schedule Optimizer."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from src.sales.leads import Lead
from src.commercial.hotel_lead import HotelLead
from src.commercial.lead_qualifier import LeadQualifier
from src.commercial.package_matcher import PackageMatcher
from src.commercial.pipeline_sync import PipelineSyncBridge
from src.commercial.outreach_sequence import (
    OutreachSequencer, OutreachChannel, StepStatus,
)
from src.commercial.prospect_list import ProspectList
from src.commercial.followup_schedule import (
    FollowUpEntry,
    FollowUpSchedule,
)


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_lead(hid: str, name: str, city: str, state: str, niche: str,
               tier: str, fit: int, priority: str, channel: str = "email",
               source: str = "indicacao", interest: str = "pacote") -> HotelLead:
    base = Lead(
        lead_id=hid, name=name, contact_channel=channel, source=source,
        segment="hotel", interest=interest, tags=[niche], score=fit,
    )
    return HotelLead(
        hotel_lead_id=hid, base_lead=base, hotel_name=name,
        city=city, state=state, region="nordeste",
        hotel_tier=tier, niche=niche,
        room_count_placeholder=50, average_daily_rate_placeholder=500.0,
        decision_maker_name="Teste", decision_maker_role="Gerente",
        fit_score=fit, priority_tier=priority,
    )


def _make_sequencer_with_leads(leads: list[HotelLead]) -> OutreachSequencer:
    seqr = OutreachSequencer()
    for hl in leads:
        seqr.generate_sequence(hl, OutreachChannel.EMAIL)
    return seqr


# ── FollowUpEntry Tests ────────────────────────────────────────────────────

class TestFollowUpEntry:
    def test_create_entry(self):
        entry = FollowUpEntry(
            entry_id="e1", hotel_lead_id="h1", hotel_name="Test Hotel",
            sequence_id="s1", step_number=1, step_label="D+0 — Abertura",
            channel="email", call_to_action="Responder",
            due_date="2026-05-15T00:00:00", days_until_due=0,
            is_overdue=False, overdue_days=0,
            fit_score=90, priority_tier="hot",
            suggested_stage="negociacao", priority_rank=5,
            step_status="ready",
        )
        assert entry.hotel_name == "Test Hotel"
        assert entry.urgency == "imminent"
        assert entry.is_actionable is True

    def test_urgency_critical(self):
        entry = FollowUpEntry(
            entry_id="e2", hotel_lead_id="h2", hotel_name="H",
            is_overdue=True, overdue_days=7, days_until_due=-7,
            priority_rank=10, step_status="pending",
        )
        assert entry.urgency == "critical"

    def test_urgency_overdue(self):
        entry = FollowUpEntry(
            entry_id="e3", hotel_lead_id="h3", hotel_name="H",
            is_overdue=True, overdue_days=2, days_until_due=-2,
            priority_rank=10, step_status="pending",
        )
        assert entry.urgency == "overdue"

    def test_urgency_scheduled(self):
        entry = FollowUpEntry(
            entry_id="e4", hotel_lead_id="h4", hotel_name="H",
            is_overdue=False, overdue_days=0, days_until_due=5,
            priority_rank=10, step_status="pending",
        )
        assert entry.urgency == "scheduled"

    def test_urgency_soon(self):
        entry = FollowUpEntry(
            entry_id="e5", hotel_lead_id="h5", hotel_name="H",
            is_overdue=False, overdue_days=0, days_until_due=2,
            priority_rank=10, step_status="pending",
        )
        assert entry.urgency == "soon"

    def test_is_actionable_not_overdue(self):
        entry = FollowUpEntry(
            entry_id="e6", hotel_lead_id="h6", hotel_name="H",
            is_overdue=False, step_status="ready", priority_rank=5,
        )
        assert entry.is_actionable is True

    def test_to_dict(self):
        entry = FollowUpEntry(
            entry_id="e7", hotel_lead_id="h7", hotel_name="H",
            fit_score=70, priority_tier="warm", priority_rank=15,
            step_status="ready",
        )
        d = entry.to_dict()
        assert d["entry_id"] == "e7"
        assert d["fit_score"] == 70
        assert d["dry_run"] is True


# ── FollowUpSchedule Tests ─────────────────────────────────────────────────

class TestFollowUpSchedule:
    def test_build_from_sequencer(self):
        scheduler = FollowUpSchedule()
        hl = _make_lead("h1", "Hotel A", "Natal", "RN", "resort",
                         "Premium", 90, "hot")
        seqr = _make_sequencer_with_leads([hl])

        entries = scheduler.build(seqr)
        assert len(entries) >= 1
        assert entries[0].hotel_name == "Hotel A"
        assert entries[0].step_status in ("ready", "pending")
        assert entries[0].dry_run is True

    def test_build_respects_active_only(self):
        scheduler = FollowUpSchedule()
        hl1 = _make_lead("h1", "Active", "Natal", "RN", "resort",
                          "Premium", 90, "hot")
        hl2 = _make_lead("h2", "Cancelled", "Maceio", "AL", "pousada",
                          "Growth", 60, "warm")
        seqr = _make_sequencer_with_leads([hl1, hl2])

        # Cancel hl2's sequence
        for seq in seqr.list_all():
            if seq.hotel_lead_id == "h2":
                seq.cancel()

        entries = scheduler.build(seqr)
        hotel_names = {e.hotel_name for e in entries}
        assert "Active" in hotel_names
        assert "Cancelled" not in hotel_names

    def test_build_with_sync_entries(self):
        scheduler = FollowUpSchedule()
        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        matcher = PackageMatcher()

        hl = _make_lead("h1", "Hotel X", "Natal", "RN", "resort",
                         "Premium", 90, "hot")
        seqr = _make_sequencer_with_leads([hl])
        br = q.qualify(hl)
        pm = matcher.match(hl, br)
        sync_entry = bridge.sync(hl, br, pm)

        entries = scheduler.build(seqr, [sync_entry])
        assert entries[0].fit_score == 90
        assert entries[0].priority_tier == "hot"
        assert entries[0].suggested_stage != ""

    def test_build_sorted_by_priority(self):
        scheduler = FollowUpSchedule()
        bridge = PipelineSyncBridge()
        q = LeadQualifier()
        matcher = PackageMatcher()

        hl_hot = _make_lead("h_hot", "Hot Hotel", "Natal", "RN", "resort",
                             "Premium", 90, "hot")
        hl_cold = _make_lead("h_cold", "Cold Hotel", "SP", "SP", "hostel",
                              "Starter", 10, "cold",
                              source="prospeccao", interest="")

        seqr = _make_sequencer_with_leads([hl_cold, hl_hot])

        br_hot = q.qualify(hl_hot)
        pm_hot = matcher.match(hl_hot, br_hot)
        se_hot = bridge.sync(hl_hot, br_hot, pm_hot)

        br_cold = q.qualify(hl_cold)
        pm_cold = matcher.match(hl_cold, br_cold)
        se_cold = bridge.sync(hl_cold, br_cold, pm_cold)

        entries = scheduler.build(seqr, [se_hot, se_cold])
        # Hot hotel should come before cold
        assert entries[0].hotel_name == "Hot Hotel"

    def test_detect_overdue(self):
        scheduler = FollowUpSchedule()
        entries = [
            FollowUpEntry(entry_id="e1", hotel_lead_id="h1", hotel_name="A",
                          is_overdue=True, overdue_days=5, priority_rank=10, step_status="pending"),
            FollowUpEntry(entry_id="e2", hotel_lead_id="h2", hotel_name="B",
                          is_overdue=True, overdue_days=1, priority_rank=20, step_status="pending"),
            FollowUpEntry(entry_id="e3", hotel_lead_id="h3", hotel_name="C",
                          is_overdue=False, priority_rank=5, step_status="ready"),
        ]
        overdue = scheduler.detect_overdue(entries)
        assert len(overdue) == 2
        # Most overdue first
        assert overdue[0].hotel_name == "A"

    def test_next_best_action(self):
        scheduler = FollowUpSchedule()
        entries = [
            FollowUpEntry(entry_id="e1", hotel_lead_id="h1", hotel_name="Low",
                          priority_rank=30, step_status="ready"),
            FollowUpEntry(entry_id="e2", hotel_lead_id="h2", hotel_name="High",
                          priority_rank=5, step_status="ready"),
            FollowUpEntry(entry_id="e3", hotel_lead_id="h3", hotel_name="Done",
                          priority_rank=1, step_status="completed"),
        ]
        best = scheduler.next_best_action(entries)
        assert best.hotel_name == "High"

    def test_next_best_action_none(self):
        scheduler = FollowUpSchedule()
        entries = [
            FollowUpEntry(entry_id="e1", hotel_lead_id="h1", hotel_name="Done",
                          priority_rank=1, step_status="completed"),
        ]
        best = scheduler.next_best_action(entries)
        assert best is None

    def test_summary_by_urgency(self):
        scheduler = FollowUpSchedule()
        entries = [
            FollowUpEntry(entry_id="e1", hotel_lead_id="h1", hotel_name="A",
                          is_overdue=True, overdue_days=7, days_until_due=-7, priority_rank=5, step_status="pending"),
            FollowUpEntry(entry_id="e2", hotel_lead_id="h2", hotel_name="B",
                          is_overdue=True, overdue_days=2, days_until_due=-2, priority_rank=10, step_status="pending"),
            FollowUpEntry(entry_id="e3", hotel_lead_id="h3", hotel_name="C",
                          is_overdue=False, days_until_due=0, priority_rank=15, step_status="ready"),
            FollowUpEntry(entry_id="e4", hotel_lead_id="h4", hotel_name="D",
                          is_overdue=False, days_until_due=5, priority_rank=20, step_status="ready"),
        ]
        summary = scheduler.summary_by_urgency(entries)
        assert summary["critical"] == 1
        assert summary["overdue"] == 1
        assert summary["imminent"] == 1
        assert summary["scheduled"] == 1

    def test_export_schedule_report(self):
        scheduler = FollowUpSchedule()
        hl = _make_lead("h1", "Report Hotel", "Natal", "RN", "resort",
                         "Premium", 80, "hot")
        seqr = _make_sequencer_with_leads([hl])

        entries = scheduler.build(seqr)
        report = scheduler.export_schedule_report(entries)
        assert "Follow-Up Schedule Report" in report
        assert "Report Hotel" in report
        assert "**dry_run:** True" in report

    def test_export_calendar_dict(self):
        scheduler = FollowUpSchedule()
        entries = [
            FollowUpEntry(entry_id="e1", hotel_lead_id="h1", hotel_name="A",
                          due_date="2026-05-15T00:00:00", channel="email",
                          step_label="D+0 — Abertura",
                          is_overdue=False, overdue_days=0, days_until_due=0,
                          priority_rank=5, step_status="ready"),
            FollowUpEntry(entry_id="e2", hotel_lead_id="h2", hotel_name="B",
                          due_date="2026-05-15T00:00:00", channel="whatsapp",
                          step_label="D+2 — Reforco",
                          is_overdue=False, overdue_days=0, days_until_due=2,
                          priority_rank=10, step_status="pending"),
        ]
        cal = scheduler.export_calendar_dict(entries)
        assert "2026-05-15" in cal
        assert len(cal["2026-05-15"]) == 2

    def test_dry_run_default(self):
        scheduler = FollowUpSchedule()
        hl = _make_lead("h1", "Hotel", "Natal", "RN", "resort",
                         "Premium", 80, "hot")
        seqr = _make_sequencer_with_leads([hl])
        entries = scheduler.build(seqr)
        for e in entries:
            assert e.dry_run is True

    def test_deterministic(self):
        scheduler = FollowUpSchedule()
        hl = _make_lead("h1", "Hotel", "Natal", "RN", "resort",
                         "Premium", 80, "hot")
        seqr = _make_sequencer_with_leads([hl])

        e1 = scheduler.build(seqr)
        e2 = scheduler.build(seqr)
        assert len(e1) == len(e2)
        for a, b in zip(e1, e2):
            assert a.hotel_name == b.hotel_name
            assert a.priority_rank == b.priority_rank

    def test_build_from_prospect_list(self):
        scheduler = FollowUpSchedule()
        hl1 = _make_lead("h1", "In List", "Natal", "RN", "resort",
                          "Premium", 80, "hot")
        hl2 = _make_lead("h2", "Not In List", "Maceio", "AL", "pousada",
                          "Growth", 60, "warm")

        pl = ProspectList()
        pl.add(hl1)

        seqr = _make_sequencer_with_leads([hl1, hl2])
        entries = scheduler.build_from_prospect_list(seqr, pl)
        hotel_names = {e.hotel_name for e in entries}
        assert "In List" in hotel_names
        assert "Not In List" not in hotel_names

    def test_suggest_priority_returns_sorted(self):
        scheduler = FollowUpSchedule()
        entries = [
            FollowUpEntry(entry_id="e3", hotel_lead_id="h3", hotel_name="Last",
                          priority_rank=30, step_status="pending"),
            FollowUpEntry(entry_id="e1", hotel_lead_id="h1", hotel_name="First",
                          priority_rank=5, step_status="ready"),
            FollowUpEntry(entry_id="e2", hotel_lead_id="h2", hotel_name="Mid",
                          priority_rank=15, step_status="pending"),
        ]
        sorted_entries = scheduler.suggest_priority(entries)
        assert sorted_entries[0].hotel_name == "First"
        assert sorted_entries[-1].hotel_name == "Last"
