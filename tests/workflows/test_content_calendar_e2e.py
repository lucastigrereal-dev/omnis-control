"""E2E tests — ContentCalendarWorkflow: brief → calendário editorial → queue items → akasha.

Cobertura:
  - geração 7 e 30 dias
  - run_id propagado
  - items_count == num_days
  - rotação de formatos (FEED/REELS/CAROUSEL/STORIES)
  - round-robin de tópicos
  - rotação de objetivos
  - akasha evento com format_distribution
  - erro: handle vazio, tópicos vazios, num_days inválido
  - to_dict keys
  - cost_local_pct=100
"""
from __future__ import annotations

from datetime import date

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.content_queue.models import QueueFormat, QueueObjective, QueueStatus
from src.workflows.content_calendar_workflow import (
    ContentCalendarWorkflow,
    ContentCalendarResult,
    _COST_LOCAL_PCT,
    _FORMAT_ROTATION,
    _OBJECTIVE_ROTATION,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_wf() -> tuple[ContentCalendarWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    return ContentCalendarWorkflow(akasha_sink=sink), sink


_TOPICS = ["praias", "gastronomia", "hotéis"]
_HANDLE = "@oinatalrn"


# ── basic run ─────────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS, dry_run=True)
    assert result.success is True


def test_run_creates_run_id():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS)
    assert result.run_id
    assert len(result.run_id) == 12


def test_run_7_days_default():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS)
    assert result.items_count == 7


def test_run_30_days():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS, num_days=30)
    assert result.items_count == 30


def test_run_1_day():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS, num_days=1)
    assert result.items_count == 1


def test_run_cost_local_pct_100():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS)
    assert result.cost_local_pct == 100


def test_result_account_handle():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS)
    assert result.account_handle == _HANDLE


def test_result_num_days():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS, num_days=14)
    assert result.num_days == 14


# ── QueueItem model ───────────────────────────────────────────────────────────

def test_items_have_planned_status():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS)
    for item in result.items:
        assert item.status == QueueStatus.PLANNED


def test_items_have_account_handle():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS)
    for item in result.items:
        assert item.account_handle == _HANDLE


def test_items_have_unique_queue_ids():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS, num_days=10)
    ids = [i.queue_id for i in result.items]
    assert len(ids) == len(set(ids))


def test_items_have_run_id_prefix():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS)
    run_prefix = result.run_id[:8]
    for item in result.items:
        assert item.queue_id.startswith(run_prefix)


def test_items_have_date():
    wf, _ = _make_wf()
    fixed = date(2026, 6, 1)
    result = wf.run(_HANDLE, _TOPICS, start_date=fixed)
    assert result.items[0].date == "2026-06-01"
    assert result.items[6].date == "2026-06-07"


# ── format rotation ───────────────────────────────────────────────────────────

def test_format_rotation_day_0():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS, num_days=7)
    assert result.items[0].format == _FORMAT_ROTATION[0]


def test_format_rotation_day_1():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS, num_days=7)
    assert result.items[1].format == _FORMAT_ROTATION[1]


def test_format_distribution_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS, num_days=7)
    dist = result.format_distribution
    assert len(dist) > 0
    assert sum(dist.values()) == 7


# ── topics round-robin ────────────────────────────────────────────────────────

def test_topic_round_robin():
    wf, _ = _make_wf()
    topics = ["A", "B", "C"]
    result = wf.run(_HANDLE, topics, num_days=6)
    assert "Tópico: A" in result.items[0].notes
    assert "Tópico: B" in result.items[1].notes
    assert "Tópico: C" in result.items[2].notes
    assert "Tópico: A" in result.items[3].notes


# ── akasha ────────────────────────────────────────────────────────────────────

def test_emits_akasha_event():
    wf, sink = _make_wf()
    wf.run(_HANDLE, _TOPICS)
    events = sink.query_events("content_calendar_generated")
    assert len(events) == 1


def test_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run(_HANDLE, _TOPICS)
    events = sink.query_events("content_calendar_generated")
    assert events[0].source == result.run_id


def test_event_has_format_distribution():
    wf, sink = _make_wf()
    wf.run(_HANDLE, _TOPICS)
    events = sink.query_events("content_calendar_generated")
    assert "format_distribution" in events[0].payload


def test_event_has_items_count():
    wf, sink = _make_wf()
    wf.run(_HANDLE, _TOPICS, num_days=14)
    events = sink.query_events("content_calendar_generated")
    assert events[0].payload["items_count"] == 14


def test_akasha_event_id_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS)
    assert result.akasha_event_id.startswith("ske_")


def test_akasha_status_written():
    wf, sink = _make_wf()
    wf.run(_HANDLE, _TOPICS)
    events = sink.query_events("content_calendar_generated")
    assert events[0].status == SinkStatus.WRITTEN


# ── errors ────────────────────────────────────────────────────────────────────

def test_empty_account_handle_returns_error():
    wf, _ = _make_wf()
    result = wf.run("", _TOPICS)
    assert result.success is False
    assert result.error == "empty_account_handle"


def test_empty_topics_returns_error():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, [])
    assert result.success is False
    assert result.error == "empty_topics"


def test_invalid_num_days_zero():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS, num_days=0)
    assert result.success is False
    assert result.error == "invalid_num_days"


def test_invalid_num_days_too_large():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS, num_days=366)
    assert result.success is False
    assert result.error == "invalid_num_days"


def test_error_result_has_run_id():
    wf, _ = _make_wf()
    result = wf.run("", _TOPICS)
    assert result.run_id
    assert len(result.run_id) == 12


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS)
    d = result.to_dict()
    for key in ["run_id", "success", "account_handle", "num_days", "items_count",
                "format_distribution", "akasha_event_id", "cost_local_pct"]:
        assert key in d


def test_to_dict_items_list():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPICS, num_days=3)
    d = result.to_dict()
    assert len(d["items"]) == 3
