"""E2E tests — DeliverableMappingWorkflow: textos → intake → manifestos → akasha.

Cobertura:
  - run básico (success, run_id, cost_local_pct=100)
  - missions_count correto
  - results length = missions_count
  - total_deliverables > 0
  - setor "marketing" detectado de texto com "hotel"
  - setor "sales" detectado de texto com "lead"
  - setor "app_factory" detectado de texto com "app"
  - unique_sectors property
  - high_risk_count property
  - sectors list length = missions_count
  - result.deliverables_count > 0
  - result.sector property
  - to_dict keys
  - error: empty_missions
  - akasha evento "deliverables_mapped"
  - event source = run_id
  - event has missions_count in payload
  - akasha_event_id starts with ske_
  - event status WRITTEN
  - dry_run propagado
"""
from __future__ import annotations

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.deliverable_mapping_workflow import (
    DeliverableMappingWorkflow,
    DeliverableMappingResult,
    _COST_LOCAL_PCT,
)


# ── helpers ───────────────────────────────────────────────────────────────────

_MARKETING_TEXT = "Criar campanha de hotel com carrossel e legenda para Instagram"
_SALES_TEXT = "Prospectar leads SDR com sequência de DM para fechar vendas"
_APP_TEXT = "Desenvolver app com PRD, schema e deploy de API"
_RISKY_TEXT = "Apagar todos os arquivos e resetar o sistema para backup"


def _make_wf() -> tuple[DeliverableMappingWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    return DeliverableMappingWorkflow(akasha_sink=sink), sink


# ── basic run ─────────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT])
    assert result.success is True


def test_run_creates_run_id():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT])
    assert result.run_id
    assert len(result.run_id) == 12


def test_cost_local_pct_100():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT])
    assert result.cost_local_pct == _COST_LOCAL_PCT == 100


def test_dry_run_propagated():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT], dry_run=True)
    assert result.dry_run is True


# ── missions ──────────────────────────────────────────────────────────────────

def test_missions_count():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT, _SALES_TEXT, _APP_TEXT])
    assert result.missions_count == 3


def test_results_length_matches_missions():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT, _SALES_TEXT])
    assert len(result.results) == 2


def test_total_deliverables_positive():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT])
    assert result.total_deliverables > 0


def test_sectors_list_length():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT, _SALES_TEXT])
    assert len(result.sectors) == 2


# ── sector detection ──────────────────────────────────────────────────────────

def test_marketing_sector_detected():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT])
    assert result.results[0].sector == "marketing"


def test_sales_sector_detected():
    wf, _ = _make_wf()
    result = wf.run([_SALES_TEXT])
    assert result.results[0].sector == "sales"


def test_app_sector_detected():
    wf, _ = _make_wf()
    result = wf.run([_APP_TEXT])
    assert result.results[0].sector == "app_factory"


def test_unique_sectors_property():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT, _MARKETING_TEXT, _SALES_TEXT])
    assert result.unique_sectors == 2


# ── risk ──────────────────────────────────────────────────────────────────────

def test_high_risk_count_for_risky_text():
    wf, _ = _make_wf()
    result = wf.run([_RISKY_TEXT, _MARKETING_TEXT])
    assert result.high_risk_count >= 1


def test_high_risk_count_zero_for_normal_texts():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT, _SALES_TEXT])
    assert result.high_risk_count == 0


# ── deliverable properties ────────────────────────────────────────────────────

def test_result_deliverables_count_positive():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT])
    assert result.results[0].deliverables_count > 0


def test_result_sector_property():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT])
    assert result.results[0].sector == "marketing"


# ── error ─────────────────────────────────────────────────────────────────────

def test_empty_missions_returns_error():
    wf, _ = _make_wf()
    result = wf.run([])
    assert result.success is False
    assert result.error == "empty_missions"


def test_empty_missions_has_run_id():
    wf, _ = _make_wf()
    result = wf.run([])
    assert result.run_id
    assert len(result.run_id) == 12


# ── akasha ────────────────────────────────────────────────────────────────────

def test_emits_akasha_event():
    wf, sink = _make_wf()
    wf.run([_MARKETING_TEXT])
    events = sink.query_events("deliverables_mapped")
    assert len(events) == 1


def test_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run([_MARKETING_TEXT])
    events = sink.query_events("deliverables_mapped")
    assert events[0].source == result.run_id


def test_event_has_missions_count():
    wf, sink = _make_wf()
    wf.run([_MARKETING_TEXT, _SALES_TEXT])
    events = sink.query_events("deliverables_mapped")
    assert events[0].payload["missions_count"] == 2


def test_akasha_event_id_starts_with_ske():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT])
    assert result.akasha_event_id.startswith("ske_")


def test_event_status_written():
    wf, sink = _make_wf()
    wf.run([_MARKETING_TEXT])
    events = sink.query_events("deliverables_mapped")
    assert events[0].status == SinkStatus.WRITTEN


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run([_MARKETING_TEXT])
    d = result.to_dict()
    for key in ["run_id", "success", "missions_count", "total_deliverables",
                "unique_sectors", "high_risk_count", "sectors",
                "akasha_event_id", "cost_local_pct"]:
        assert key in d
