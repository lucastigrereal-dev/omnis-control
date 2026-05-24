"""E2E tests — ContentQualityWorkflow: items → QualityReport lote → akasha.

Cobertura:
  - run básico (success, run_id, cost_local_pct=100)
  - items_total e items_ready
  - reports list length = items_total
  - cada report tem output_id correto
  - ready_rate property
  - average_score > 0
  - grade_distribution keys presentes
  - items_not_ready property
  - tipo caption/reel/dm respeitado
  - metadata passado ao scorer (personalization)
  - akasha evento "content_quality_scored"
  - event source = run_id
  - akasha_event_id starts with ske_
  - event has items_total in payload
  - event status WRITTEN
  - erro: empty_items
  - to_dict keys
  - dry_run flag propagado
"""
from __future__ import annotations

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.content_quality_workflow import (
    ContentQualityWorkflow,
    ContentQualityResult,
    _COST_LOCAL_PCT,
)


# ── helpers ───────────────────────────────────────────────────────────────────

_GOOD_CAPTION = (
    "Descubra o hotel mais lindo de Natal! "
    "Fui eu mesmo que testei e aprovei. Ame cada detalhe do lugar. "
    "Salva para a sua viagem! Comenta o que você acha. "
    "#hotel #natal #viagem #turismo #nordeste "
    "Aproveite cada momento desta experiência incrível. "
    "Compartilha com quem vai viajar com você."
)

_WEAK_CAPTION = "ok"


def _make_wf() -> tuple[ContentQualityWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    return ContentQualityWorkflow(akasha_sink=sink), sink


def _item(item_id: str = "cap_001", output_type: str = "caption", content: str = _GOOD_CAPTION) -> dict:
    return {"id": item_id, "type": output_type, "content": content}


# ── basic run ─────────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf, _ = _make_wf()
    result = wf.run([_item()], dry_run=True)
    assert result.success is True


def test_run_creates_run_id():
    wf, _ = _make_wf()
    result = wf.run([_item()])
    assert result.run_id
    assert len(result.run_id) == 12


def test_cost_local_pct_100():
    wf, _ = _make_wf()
    result = wf.run([_item()])
    assert result.cost_local_pct == _COST_LOCAL_PCT == 100


def test_dry_run_flag_propagated():
    wf, _ = _make_wf()
    result = wf.run([_item()], dry_run=True)
    assert result.dry_run is True


# ── items counts ──────────────────────────────────────────────────────────────

def test_items_total():
    wf, _ = _make_wf()
    items = [_item(f"c{i}") for i in range(4)]
    result = wf.run(items)
    assert result.items_total == 4


def test_reports_length_matches_items():
    wf, _ = _make_wf()
    items = [_item(f"c{i}") for i in range(3)]
    result = wf.run(items)
    assert len(result.reports) == 3


def test_report_output_ids_match_input():
    wf, _ = _make_wf()
    ids = ["alpha", "beta", "gamma"]
    items = [_item(i) for i in ids]
    result = wf.run(items)
    report_ids = [r.output_id for r in result.reports]
    assert report_ids == ids


def test_items_ready_lte_items_total():
    wf, _ = _make_wf()
    result = wf.run([_item(f"c{i}") for i in range(5)])
    assert result.items_ready <= result.items_total


def test_items_not_ready_complements_ready():
    wf, _ = _make_wf()
    result = wf.run([_item(f"c{i}") for i in range(3)])
    assert result.items_ready + result.items_not_ready == result.items_total


def test_ready_rate_between_0_and_1():
    wf, _ = _make_wf()
    result = wf.run([_item(f"c{i}") for i in range(3)])
    assert 0.0 <= result.ready_rate <= 1.0


# ── scoring ───────────────────────────────────────────────────────────────────

def test_average_score_positive():
    wf, _ = _make_wf()
    result = wf.run([_item()])
    assert result.average_score > 0.0


def test_average_score_le_10():
    wf, _ = _make_wf()
    result = wf.run([_item(f"c{i}") for i in range(3)])
    assert result.average_score <= 10.0


def test_grade_distribution_has_all_keys():
    wf, _ = _make_wf()
    result = wf.run([_item()])
    dist = result.grade_distribution
    for key in ["A", "B", "C", "D", "F"]:
        assert key in dist


def test_grade_distribution_sums_to_items_total():
    wf, _ = _make_wf()
    items = [_item(f"c{i}") for i in range(4)]
    result = wf.run(items)
    dist = result.grade_distribution
    total = sum(v for k, v in dist.items() if k != "N/A")
    assert total == result.items_total


def test_reel_type_accepted():
    wf, _ = _make_wf()
    result = wf.run([_item("r1", "reel", _GOOD_CAPTION)])
    assert result.reports[0].output_type == "reel"


def test_dm_type_with_metadata():
    wf, _ = _make_wf()
    item = {
        "id": "dm_001",
        "type": "dm",
        "content": "Oi Hotel Beira Mar, vi seu perfil e quero propor uma parceria.",
        "metadata": {"recipient_name": "Hotel Beira Mar", "company_name": "Hotel Beira Mar"},
    }
    result = wf.run([item])
    assert result.reports[0].output_type == "dm"


def test_unknown_type_falls_back_to_caption():
    wf, _ = _make_wf()
    result = wf.run([_item("x1", "unknown_type", _GOOD_CAPTION)])
    assert result.reports[0].output_type == "caption"


# ── akasha ────────────────────────────────────────────────────────────────────

def test_emits_akasha_event():
    wf, sink = _make_wf()
    wf.run([_item()])
    events = sink.query_events("content_quality_scored")
    assert len(events) == 1


def test_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run([_item()])
    events = sink.query_events("content_quality_scored")
    assert events[0].source == result.run_id


def test_event_has_items_total():
    wf, sink = _make_wf()
    wf.run([_item(f"c{i}") for i in range(3)])
    events = sink.query_events("content_quality_scored")
    assert events[0].payload["items_total"] == 3


def test_akasha_event_id_starts_with_ske():
    wf, _ = _make_wf()
    result = wf.run([_item()])
    assert result.akasha_event_id.startswith("ske_")


def test_event_status_written():
    wf, sink = _make_wf()
    wf.run([_item()])
    events = sink.query_events("content_quality_scored")
    assert events[0].status == SinkStatus.WRITTEN


# ── error ─────────────────────────────────────────────────────────────────────

def test_empty_items_returns_error():
    wf, _ = _make_wf()
    result = wf.run([])
    assert result.success is False
    assert result.error == "empty_items"


def test_empty_items_has_run_id():
    wf, _ = _make_wf()
    result = wf.run([])
    assert result.run_id
    assert len(result.run_id) == 12


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run([_item()])
    d = result.to_dict()
    for key in ["run_id", "success", "items_total", "items_ready",
                "items_not_ready", "ready_rate", "average_score",
                "grade_distribution", "akasha_event_id", "cost_local_pct"]:
        assert key in d
