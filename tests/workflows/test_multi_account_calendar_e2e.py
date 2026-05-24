"""E2E tests — MultiAccountCalendarWorkflow: batch de contas → calendários → akasha.

Cobertura:
  - batch 2 e 6 contas
  - run_id propagado
  - total_items == accounts × num_days
  - accounts_ok == accounts_total (para casos válidos)
  - accounts_failed
  - format_distribution_all consolidado
  - AccountCalendar.to_dict
  - akasha evento com totais
  - erro: lista vazia
  - default_accounts() retorna 6 contas
  - to_dict keys
  - cost_local_pct=100
"""
from __future__ import annotations

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.multi_account_calendar_workflow import (
    MultiAccountCalendarWorkflow,
    MultiAccountCalendarResult,
    AccountCalendar,
    _COST_LOCAL_PCT,
    _DEFAULT_ACCOUNTS,
)
from src.workflows.content_calendar_workflow import ContentCalendarWorkflow


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_wf() -> tuple[MultiAccountCalendarWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    cal = ContentCalendarWorkflow(akasha_sink=MockAkashaSink())
    return MultiAccountCalendarWorkflow(calendar_workflow=cal, akasha_sink=sink), sink


_TWO_ACCOUNTS = [
    {"handle": "@oinatalrn", "topics": ["praias", "hoteis"]},
    {"handle": "@agenteviajabrasil", "topics": ["destinos", "dicas"]},
]


# ── basic run ─────────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf, _ = _make_wf()
    result = wf.run(_TWO_ACCOUNTS, dry_run=True)
    assert result.success is True


def test_run_creates_run_id():
    wf, _ = _make_wf()
    result = wf.run(_TWO_ACCOUNTS)
    assert result.run_id
    assert len(result.run_id) == 12


def test_accounts_total():
    wf, _ = _make_wf()
    result = wf.run(_TWO_ACCOUNTS)
    assert result.accounts_total == 2


def test_accounts_ok_all_valid():
    wf, _ = _make_wf()
    result = wf.run(_TWO_ACCOUNTS)
    assert result.accounts_ok == 2


def test_cost_local_pct_100():
    wf, _ = _make_wf()
    result = wf.run(_TWO_ACCOUNTS)
    assert result.cost_local_pct == 100


# ── items count ───────────────────────────────────────────────────────────────

def test_total_items_2_accounts_7_days():
    wf, _ = _make_wf()
    result = wf.run(_TWO_ACCOUNTS, num_days=7)
    assert result.total_items == 14


def test_total_items_6_accounts_7_days():
    wf, _ = _make_wf()
    result = wf.run(MultiAccountCalendarWorkflow.default_accounts(), num_days=7)
    assert result.total_items == 42


def test_total_items_1_account_30_days():
    wf, _ = _make_wf()
    result = wf.run([_TWO_ACCOUNTS[0]], num_days=30)
    assert result.total_items == 30


# ── calendars list ────────────────────────────────────────────────────────────

def test_calendars_count_equals_accounts():
    wf, _ = _make_wf()
    result = wf.run(_TWO_ACCOUNTS)
    assert len(result.calendars) == 2


def test_calendar_has_correct_handle():
    wf, _ = _make_wf()
    result = wf.run(_TWO_ACCOUNTS)
    handles = {c.account_handle for c in result.calendars}
    assert "@oinatalrn" in handles
    assert "@agenteviajabrasil" in handles


def test_accounts_failed_zero_for_valid_input():
    wf, _ = _make_wf()
    result = wf.run(_TWO_ACCOUNTS)
    assert result.accounts_failed == 0


# ── format distribution ───────────────────────────────────────────────────────

def test_format_distribution_all_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_TWO_ACCOUNTS)
    dist = result.format_distribution_all
    assert len(dist) > 0
    assert sum(dist.values()) == result.total_items


# ── AccountCalendar model ─────────────────────────────────────────────────────

def test_account_calendar_items_count():
    wf, _ = _make_wf()
    result = wf.run([_TWO_ACCOUNTS[0]], num_days=7)
    assert result.calendars[0].items_count == 7


def test_account_calendar_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run([_TWO_ACCOUNTS[0]])
    d = result.calendars[0].to_dict()
    for key in ["account_handle", "topics", "items_count", "success", "format_distribution"]:
        assert key in d


# ── default_accounts() ────────────────────────────────────────────────────────

def test_default_accounts_count():
    accounts = MultiAccountCalendarWorkflow.default_accounts()
    assert len(accounts) == 6


def test_default_accounts_have_handles():
    accounts = MultiAccountCalendarWorkflow.default_accounts()
    for acc in accounts:
        assert acc["handle"].startswith("@")
        assert len(acc["topics"]) > 0


def test_default_accounts_includes_oinatalrn():
    accounts = MultiAccountCalendarWorkflow.default_accounts()
    handles = [a["handle"] for a in accounts]
    assert "@oinatalrn" in handles


# ── akasha ────────────────────────────────────────────────────────────────────

def test_emits_akasha_event():
    wf, sink = _make_wf()
    wf.run(_TWO_ACCOUNTS)
    events = sink.query_events("multi_account_calendar_generated")
    assert len(events) == 1


def test_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run(_TWO_ACCOUNTS)
    events = sink.query_events("multi_account_calendar_generated")
    assert events[0].source == result.run_id


def test_event_has_total_items():
    wf, sink = _make_wf()
    wf.run(_TWO_ACCOUNTS, num_days=7)
    events = sink.query_events("multi_account_calendar_generated")
    assert events[0].payload["total_items"] == 14


def test_event_has_accounts_ok():
    wf, sink = _make_wf()
    wf.run(_TWO_ACCOUNTS)
    events = sink.query_events("multi_account_calendar_generated")
    assert "accounts_ok" in events[0].payload


def test_akasha_event_id_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_TWO_ACCOUNTS)
    assert result.akasha_event_id.startswith("ske_")


def test_akasha_status_written():
    wf, sink = _make_wf()
    wf.run(_TWO_ACCOUNTS)
    events = sink.query_events("multi_account_calendar_generated")
    assert events[0].status == SinkStatus.WRITTEN


# ── errors ────────────────────────────────────────────────────────────────────

def test_empty_accounts_returns_error():
    wf, _ = _make_wf()
    result = wf.run([])
    assert result.success is False
    assert result.error == "empty_accounts_list"


def test_empty_accounts_has_run_id():
    wf, _ = _make_wf()
    result = wf.run([])
    assert result.run_id
    assert len(result.run_id) == 12


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run(_TWO_ACCOUNTS)
    d = result.to_dict()
    for key in ["run_id", "success", "accounts_total", "accounts_ok",
                "accounts_failed", "total_items", "format_distribution_all",
                "akasha_event_id", "cost_local_pct"]:
        assert key in d
