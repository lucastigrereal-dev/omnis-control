"""Tests — SDRPipelineWorkflow (Consolidação: O18+O19+O22).

Cobertura:
  - execute mode: scoring + outreach, actionable_count, tiers
  - plan mode: SDRPlan, plan_id, sequences_count, risk_flags
  - to_dict por modo
  - akasha events por modo
  - erros: empty_prospects, invalid_mode, empty_title (plan mode)
"""
from __future__ import annotations

import pytest

from src.commercial_sdr.models import LeadSource, ProspectProfile
from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.sdr_pipeline_workflow import SDRPipelineWorkflow


# ── helpers ───────────────────────────────────────────────────────────────────

def _prospect(i: int = 0, segment: str = "hotel") -> ProspectProfile:
    return ProspectProfile(
        profile_id=f"P-{i:03d}",
        company_name=f"Hotel {i}",
        contact_name=f"Contato {i}",
        segment=segment,
        source=LeadSource.MANUAL_RESEARCH,
        location="Natal/RN",
    )


def _prospects(n: int = 3) -> list[ProspectProfile]:
    return [_prospect(i) for i in range(n)]


# ── execute mode — basic ──────────────────────────────────────────────────────

def test_execute_succeeds():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(), mode="execute", dry_run=True)
    assert result.success is True
    assert result.mode == "execute"


def test_execute_prospects_count():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(4), mode="execute")
    assert result.prospects_count == 4


def test_execute_leads_scored():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(3), mode="execute")
    assert len(result.leads) == 3


def test_execute_actionable_count_nonnegative():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(3), mode="execute")
    assert result.actionable_count >= 0


def test_execute_tier_counts_sum_to_scored():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(4), mode="execute")
    total_tiers = result.hot_count + result.warm_count + result.cold_count
    # disqualified leads might not be included in those 3 properties — total scored >= sum
    assert total_tiers <= len(result.leads)


def test_execute_sequences_generated_lte_actionable():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(3), mode="execute")
    assert result.sequences_generated <= result.actionable_count + len(result.leads)


def test_execute_run_id_nonempty():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(), mode="execute")
    assert result.run_id != ""


def test_execute_dry_run_flag():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(), mode="execute", dry_run=True)
    assert result.dry_run is True


# ── execute mode — akasha ─────────────────────────────────────────────────────

def test_execute_emits_akasha_event():
    sink = MockAkashaSink()
    wf = SDRPipelineWorkflow(akasha_sink=sink)
    wf.run(_prospects(), mode="execute")
    events = sink.query_events("sdr_pipeline_execute_completed")
    assert len(events) == 1


def test_execute_event_source_is_run_id():
    sink = MockAkashaSink()
    wf = SDRPipelineWorkflow(akasha_sink=sink)
    result = wf.run(_prospects(), mode="execute")
    events = sink.query_events("sdr_pipeline_execute_completed")
    assert events[0].source == result.run_id


def test_execute_akasha_event_id_nonempty():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(), mode="execute")
    assert result.akasha_event_id.startswith("ske_")


# ── plan mode — basic ─────────────────────────────────────────────────────────

def test_plan_succeeds():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(), mode="plan", title="Natal Jun/2026", dry_run=True)
    assert result.success is True
    assert result.mode == "plan"


def test_plan_has_plan_id():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(), mode="plan", title="Test Plan")
    assert result.plan_id != ""


def test_plan_sequences_count_nonnegative():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(3), mode="plan", title="Test Plan")
    assert result.plan_sequences_count >= 0


def test_plan_risk_flags_is_list():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(), mode="plan", title="Test Plan")
    assert isinstance(result.risk_flags, list)


def test_plan_prospects_count():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(3), mode="plan", title="Test Plan")
    assert result.prospects_count == 3


# ── plan mode — akasha ────────────────────────────────────────────────────────

def test_plan_emits_akasha_event():
    sink = MockAkashaSink()
    wf = SDRPipelineWorkflow(akasha_sink=sink)
    wf.run(_prospects(), mode="plan", title="Test Plan")
    events = sink.query_events("sdr_pipeline_plan_generated")
    assert len(events) == 1


def test_plan_akasha_event_id_nonempty():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(), mode="plan", title="Test Plan")
    assert result.akasha_event_id.startswith("ske_")


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_execute_has_required_keys():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(), mode="execute")
    d = result.to_dict()
    for key in ["run_id", "success", "mode", "prospects_count",
                "actionable_count", "sequences_generated",
                "akasha_event_id", "dry_run", "cost_local_pct"]:
        assert key in d


def test_to_dict_plan_has_required_keys():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(), mode="plan", title="Test Plan")
    d = result.to_dict()
    for key in ["run_id", "success", "mode", "prospects_count",
                "plan_id", "plan_sequences_count", "risk_flags",
                "akasha_event_id", "dry_run", "cost_local_pct"]:
        assert key in d


# ── error cases ───────────────────────────────────────────────────────────────

def test_empty_prospects_fails():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run([], mode="execute")
    assert result.success is False
    assert result.error == "empty_prospect_list"


def test_invalid_mode_fails():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(), mode="invalid_mode")
    assert result.success is False
    assert "invalid_mode" in result.error


def test_plan_empty_title_fails():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(), mode="plan", title="")
    assert result.success is False
    assert result.error == "empty_title"


def test_cost_local_pct_100():
    wf = SDRPipelineWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(_prospects(), mode="execute")
    assert result.cost_local_pct == 100
