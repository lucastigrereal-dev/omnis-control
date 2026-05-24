"""E2E tests — DailyBriefingWorkflow: health + leads + calendar → briefing → akasha.

Cobertura:
  - run() mínimo (só health)
  - run() com prospects (health + leads)
  - run() com calendar (health + calendar)
  - run() completo (health + leads + calendar)
  - run_id propagado
  - briefing_date presente
  - health_ok property
  - hot_leads_count property
  - calendar_items property
  - briefing_text (markdown com seções)
  - akasha evento "daily_briefing_generated"
  - default() factory
  - to_dict keys
  - cost_local_pct=100
"""
from __future__ import annotations

from datetime import date

import pytest

from src.agentic.agency import AgencyRegistry
from src.commercial_sdr.models import LeadSource, ProspectProfile
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.system_health_workflow import SystemHealthWorkflow
from src.workflows.lead_scoring_workflow import LeadScoringWorkflow
from src.workflows.content_calendar_workflow import ContentCalendarWorkflow
from src.workflows.workflow_registry import WorkflowRegistry, WorkflowEntry
from src.workflows.daily_briefing_workflow import (
    DailyBriefingWorkflow,
    DailyBriefingResult,
    _COST_LOCAL_PCT,
)


# ── helpers ───────────────────────────────────────────────────────────────────

class _FakeWorkflow:
    def run(self, **kwargs): return {}


def _wf_reg(n: int = 2) -> WorkflowRegistry:
    reg = WorkflowRegistry()
    for i in range(n):
        reg.register(WorkflowEntry(
            name=f"wf_{i}", version="1.0", description="",
            cost_local_pct=100, dry_run_safe=True, factory=_FakeWorkflow,
        ))
    return reg


def _hotel(name: str = "Hotel Beira Mar") -> ProspectProfile:
    return ProspectProfile.new(
        company_name=name,
        contact_name="Gerente",
        segment="hotel",
        source=LeadSource.INSTAGRAM,
        instagram_handle=f"@{name.lower().replace(' ', '')}",
    )


def _make_wf() -> tuple[DailyBriefingWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    health = SystemHealthWorkflow(workflow_registry=_wf_reg(2), akasha_sink=MockAkashaSink())
    leads = LeadScoringWorkflow(akasha_sink=MockAkashaSink())
    calendar = ContentCalendarWorkflow(akasha_sink=MockAkashaSink())
    wf = DailyBriefingWorkflow(
        health_workflow=health,
        lead_workflow=leads,
        calendar_workflow=calendar,
        akasha_sink=sink,
    )
    return wf, sink


# ── basic run (health only) ───────────────────────────────────────────────────

def test_run_succeeds_no_prospects():
    wf, _ = _make_wf()
    result = wf.run(dry_run=True)
    assert result.success is True


def test_run_creates_run_id():
    wf, _ = _make_wf()
    result = wf.run()
    assert result.run_id
    assert len(result.run_id) == 12


def test_briefing_date_set():
    wf, _ = _make_wf()
    fixed = date(2026, 6, 1)
    result = wf.run(start_date=fixed)
    assert result.briefing_date == "2026-06-01"


def test_cost_local_pct_100():
    wf, _ = _make_wf()
    result = wf.run()
    assert result.cost_local_pct == 100


def test_health_always_runs():
    wf, _ = _make_wf()
    result = wf.run()
    assert result.health is not None


def test_health_ok_property():
    wf, _ = _make_wf()
    result = wf.run()
    assert isinstance(result.health_ok, bool)


# ── with prospects ────────────────────────────────────────────────────────────

def test_run_with_prospects_scores_leads():
    wf, _ = _make_wf()
    result = wf.run(prospects=[_hotel(), _hotel("Hotel Sol")])
    assert result.leads is not None
    assert result.leads.total_scored == 2


def test_hot_leads_count_when_no_prospects():
    wf, _ = _make_wf()
    result = wf.run()
    assert result.hot_leads_count == 0


def test_hot_leads_count_with_hotels():
    wf, _ = _make_wf()
    result = wf.run(prospects=[_hotel()])
    assert result.hot_leads_count >= 0


def test_leads_none_when_no_prospects():
    wf, _ = _make_wf()
    result = wf.run()
    assert result.leads is None


# ── with calendar ─────────────────────────────────────────────────────────────

def test_calendar_items_none_when_no_account():
    wf, _ = _make_wf()
    result = wf.run()
    assert result.calendar_items == 0
    assert result.calendar is None


def test_run_with_calendar():
    wf, _ = _make_wf()
    result = wf.run(
        account_handle="@oinatalrn",
        topics=["praias", "hoteis"],
        num_days=7,
    )
    assert result.calendar is not None
    assert result.calendar_items == 7


def test_calendar_needs_both_handle_and_topics():
    wf, _ = _make_wf()
    # account_handle without topics → no calendar
    result = wf.run(account_handle="@oinatalrn")
    assert result.calendar is None


# ── full run ──────────────────────────────────────────────────────────────────

def test_full_run_all_sections():
    wf, _ = _make_wf()
    result = wf.run(
        prospects=[_hotel()],
        account_handle="@oinatalrn",
        topics=["praias"],
        num_days=7,
    )
    assert result.health is not None
    assert result.leads is not None
    assert result.calendar is not None


# ── briefing_text ─────────────────────────────────────────────────────────────

def test_briefing_text_has_title():
    wf, _ = _make_wf()
    result = wf.run()
    assert "Briefing Matinal OMNIS" in result.briefing_text


def test_briefing_text_has_health_section():
    wf, _ = _make_wf()
    result = wf.run()
    assert "Sistema" in result.briefing_text


def test_briefing_text_has_leads_section_when_scored():
    wf, _ = _make_wf()
    result = wf.run(prospects=[_hotel()])
    assert "Leads SDR" in result.briefing_text


def test_briefing_text_has_calendar_section_when_generated():
    wf, _ = _make_wf()
    result = wf.run(account_handle="@oinatalrn", topics=["praias"])
    assert "Calendario Editorial" in result.briefing_text


# ── akasha ────────────────────────────────────────────────────────────────────

def test_emits_akasha_event():
    wf, sink = _make_wf()
    wf.run()
    events = sink.query_events("daily_briefing_generated")
    assert len(events) == 1


def test_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run()
    events = sink.query_events("daily_briefing_generated")
    assert events[0].source == result.run_id


def test_event_has_briefing_date():
    wf, sink = _make_wf()
    wf.run()
    events = sink.query_events("daily_briefing_generated")
    assert "briefing_date" in events[0].payload


def test_event_has_sections_generated():
    wf, sink = _make_wf()
    wf.run()
    events = sink.query_events("daily_briefing_generated")
    assert "sections_generated" in events[0].payload


def test_akasha_event_id_nonempty():
    wf, _ = _make_wf()
    result = wf.run()
    assert result.akasha_event_id.startswith("ske_")


def test_akasha_status_written():
    wf, sink = _make_wf()
    wf.run()
    events = sink.query_events("daily_briefing_generated")
    assert events[0].status == SinkStatus.WRITTEN


# ── default() factory ────────────────────────────────────────────────────────

def test_default_factory():
    wf = DailyBriefingWorkflow.default()
    wf._sink = MockAkashaSink()
    result = wf.run(dry_run=True)
    assert result.success is True
    assert result.health is not None


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run()
    d = result.to_dict()
    for key in ["run_id", "success", "briefing_date", "health_ok",
                "hot_leads_count", "calendar_items",
                "akasha_event_id", "cost_local_pct"]:
        assert key in d
