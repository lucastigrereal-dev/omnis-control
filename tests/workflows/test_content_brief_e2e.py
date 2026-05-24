"""E2E tests — ContentBriefWorkflow (Onda 34).

Cobertura (mock / dry_run=True):
  - success, run_id, account_handle, topic, format, objective
  - angle, key_points, photo_tips, hook_ideas, caption_draft, research_qs presentes
  - is_complete property
  - model_used = mock/template em dry_run
  - akasha evento content_brief_generated, source=run_id
  - to_dict keys e cost_local_pct=100
  - erros: empty_account_handle, empty_topic, invalid_format

Real LLM (pytest.mark.real_llm):
  - Ollama llama3.1:8b gera brief real para @oinatalrn, CAROUSEL "Roteiro 48h Natal"
  - angle nonempty, key_points >= 2, hook_ideas >= 1
  - tokens_used > 0, output impresso
"""
from __future__ import annotations

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.content_brief_workflow import ContentBriefWorkflow


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_wf() -> tuple[ContentBriefWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    return ContentBriefWorkflow(akasha_sink=sink), sink


_HANDLE = "@oinatalrn"
_TOPIC = "Roteiro 48h em Natal: o que ninguém te conta"


# ── basic ─────────────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.success is True


def test_run_creates_run_id():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.run_id and len(result.run_id) == 12


def test_run_account_handle():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.account_handle == _HANDLE


def test_run_topic_stored():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.topic == _TOPIC


def test_run_format_default_feed():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.format == "FEED"


def test_run_format_normalised():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, format="carousel", dry_run=True)
    assert result.format == "CAROUSEL"


def test_run_objective_stored():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, objective="engajamento", dry_run=True)
    assert result.objective == "engajamento"


def test_cost_local_pct_100():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.cost_local_pct == 100


def test_dry_run_model_template():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.model_used == "mock/template"


# ── brief content ─────────────────────────────────────────────────────────────

def test_angle_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert len(result.angle) > 0


def test_key_points_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert len(result.key_points) >= 1


def test_photo_tips_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert len(result.photo_tips) >= 1


def test_hook_ideas_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert len(result.hook_ideas) >= 1


def test_research_qs_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert len(result.research_qs) >= 1


def test_is_complete_true():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.is_complete is True


# ── akasha ────────────────────────────────────────────────────────────────────

def test_akasha_event_emitted():
    wf, sink = _make_wf()
    wf.run(_HANDLE, _TOPIC, dry_run=True)
    events = sink.query_events("content_brief_generated")
    assert len(events) == 1


def test_akasha_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    events = sink.query_events("content_brief_generated")
    assert events[0].source == result.run_id


def test_akasha_event_id_prefix():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.akasha_event_id.startswith("ske_")


def test_akasha_event_status_written():
    wf, sink = _make_wf()
    wf.run(_HANDLE, _TOPIC, dry_run=True)
    events = sink.query_events("content_brief_generated")
    assert events[0].status == SinkStatus.WRITTEN


def test_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    d = result.to_dict()
    for key in ["run_id", "success", "account_handle", "topic", "format", "objective",
                "angle", "key_points", "photo_tips", "hook_ideas", "caption_draft",
                "research_qs", "model_used", "tokens_used", "akasha_event_id", "cost_local_pct"]:
        assert key in d


# ── error cases ───────────────────────────────────────────────────────────────

def test_empty_account_handle_error():
    wf, _ = _make_wf()
    result = wf.run("", _TOPIC, dry_run=True)
    assert result.success is False
    assert result.error == "empty_account_handle"


def test_empty_topic_error():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, "", dry_run=True)
    assert result.success is False
    assert result.error == "empty_topic"


def test_invalid_format_error():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, format="PODCAST", dry_run=True)
    assert result.success is False
    assert "invalid_format" in result.error


def test_error_has_run_id():
    wf, _ = _make_wf()
    result = wf.run("", _TOPIC, dry_run=True)
    assert len(result.run_id) == 12


# ── REAL LLM — Ollama llama3.1:8b ─────────────────────────────────────────────

@pytest.mark.real_llm
def test_real_ollama_brief_oinatalrn_carousel():
    """PROVA REAL: Ollama gera brief editorial para @oinatalrn, CAROUSEL."""
    sink = MockAkashaSink()
    wf = ContentBriefWorkflow(akasha_sink=sink)

    result = wf.run(
        account_handle="@oinatalrn",
        topic="Roteiro 48h em Natal: o que ninguém te conta — praias secretas e gastronomia local",
        format="CAROUSEL",
        objective="alcance",
        dry_run=False,
    )

    print("\n" + "=" * 60)
    print(f"MODEL: {result.model_used} | TOKENS: {result.tokens_used}")
    print(f"ANGLE: {result.angle}")
    print(f"KEY_POINTS ({len(result.key_points)}):")
    for p in result.key_points:
        print(f"  • {p}")
    print(f"PHOTO_TIPS ({len(result.photo_tips)}):")
    for t in result.photo_tips:
        print(f"  > {t}")
    print(f"HOOK_IDEAS ({len(result.hook_ideas)}):")
    for h in result.hook_ideas:
        print(f"  * {h}")
    print(f"CAPTION_DRAFT: {result.caption_draft}")
    print(f"RESEARCH_QS ({len(result.research_qs)}):")
    for q in result.research_qs:
        print(f"  ? {q}")
    print(f"IS_COMPLETE: {result.is_complete}")
    print("=" * 60)

    assert result.success is True
    assert result.tokens_used > 0
    assert len(result.angle) > 0
    assert len(result.key_points) >= 2
    assert len(result.hook_ideas) >= 1
    assert result.model_used == "llama3.1:8b"
    assert result.is_complete is True
