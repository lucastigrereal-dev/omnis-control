"""Tests — CostTrackingWorkflow (Onda 31).

Cobertura:
  - run() com entries válidas
  - entries_recorded, daily_total_usd, remaining_budget
  - by_model, by_provider, by_task_type keys
  - unique_models, unique_providers
  - within_limit com dry_run=True
  - zero cost when tokens_used=0
  - akasha event emitido
  - error: empty_entries
  - to_dict keys
"""
from __future__ import annotations

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.cost_tracking_workflow import CostTrackingWorkflow


# ── helpers ───────────────────────────────────────────────────────────────────

def _entry(
    model_name: str = "claude-haiku",
    provider: str = "anthropic",
    task_type: str = "caption",
    tokens_used: int = 1000,
    cost_per_1k_tokens: float = 0.002,
) -> dict:
    return {
        "model_name": model_name,
        "provider": provider,
        "task_type": task_type,
        "tokens_used": tokens_used,
        "cost_per_1k_tokens": cost_per_1k_tokens,
    }


# ── basic run ────────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry()])
    assert result.success is True


def test_run_entries_recorded():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry(), _entry("gpt-4o", "openai")])
    assert result.entries_recorded == 2


def test_run_run_id_nonempty():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry()])
    assert result.run_id
    assert len(result.run_id) == 12


def test_run_dry_run_flag():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry()], dry_run=True)
    assert result.dry_run is True


# ── cost calculations ─────────────────────────────────────────────────────────

def test_daily_total_nonzero():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry(tokens_used=1000, cost_per_1k_tokens=0.002)])
    assert result.daily_total_usd > 0.0


def test_daily_total_zero_tokens():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry(tokens_used=0)])
    assert result.daily_total_usd == 0.0


def test_remaining_budget_decreases():
    wf = CostTrackingWorkflow(daily_limit_usd=5.0, akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry(tokens_used=1000, cost_per_1k_tokens=0.002)])
    assert result.remaining_budget_usd < 5.0


def test_within_limit_true_in_dry_run():
    # dry_run=True → check_limit always returns True
    wf = CostTrackingWorkflow(daily_limit_usd=0.001, akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry(tokens_used=10000, cost_per_1k_tokens=1.0)], dry_run=True)
    assert result.within_limit is True


# ── by_model / by_provider / by_task_type ────────────────────────────────────

def test_by_model_has_model_key():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry("claude-haiku")])
    assert "claude-haiku" in result.by_model


def test_by_provider_has_provider_key():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry(provider="anthropic")])
    assert "anthropic" in result.by_provider


def test_by_task_type_has_task_key():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry(task_type="caption")])
    assert "caption" in result.by_task_type


def test_unique_models_count():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry("model-a"), _entry("model-b"), _entry("model-a")])
    assert result.unique_models == 2


def test_unique_providers_count():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry(provider="anthropic"), _entry(provider="openai")])
    assert result.unique_providers == 2


# ── akasha event ──────────────────────────────────────────────────────────────

def test_run_emits_akasha_event():
    sink = MockAkashaSink()
    wf = CostTrackingWorkflow(akasha_sink=sink)
    wf.run(entries=[_entry()])
    events = sink.query_events("cost_tracking_report")
    assert len(events) == 1


def test_run_event_source_is_run_id():
    sink = MockAkashaSink()
    wf = CostTrackingWorkflow(akasha_sink=sink)
    result = wf.run(entries=[_entry()])
    events = sink.query_events("cost_tracking_report")
    assert events[0].source == result.run_id


def test_run_akasha_event_id_nonempty():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry()])
    assert result.akasha_event_id.startswith("ske_")


def test_run_event_status_written():
    sink = MockAkashaSink()
    wf = CostTrackingWorkflow(akasha_sink=sink)
    wf.run(entries=[_entry()])
    events = sink.query_events("cost_tracking_report")
    assert events[0].status == SinkStatus.WRITTEN


# ── error: empty_entries ──────────────────────────────────────────────────────

def test_empty_entries_success_false():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[])
    assert result.success is False


def test_empty_entries_error_field():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[])
    assert result.error == "empty_entries"


def test_empty_entries_still_emits_event():
    sink = MockAkashaSink()
    wf = CostTrackingWorkflow(akasha_sink=sink)
    wf.run(entries=[])
    events = sink.query_events("cost_tracking_report")
    assert len(events) == 1


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_has_required_keys():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry()])
    d = result.to_dict()
    for key in ["run_id", "success", "entries_recorded", "daily_total_usd",
                "remaining_budget_usd", "unique_models", "unique_providers",
                "by_model", "by_task_type", "within_limit",
                "akasha_event_id", "dry_run", "cost_local_pct"]:
        assert key in d


def test_cost_local_pct_100():
    wf = CostTrackingWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(entries=[_entry()])
    assert result.cost_local_pct == 100
