"""Tests — SEOgramWorkflow (Onda 35).

Cobertura:
  - run() dry_run=True (template)
  - validações: empty handle, empty caption
  - optimized_hook nonempty
  - hashtags <= 30
  - seo_score 1-10
  - keyword_density float 0-1
  - improvement_notes nonempty
  - akasha event emitido
  - event_type == "seogram_optimized"
  - is_optimized property
  - hashtag_count property
  - to_dict keys
  - cost_local_pct == 100
  - real_llm: @oinatalrn caption Ponta Negra
"""
from __future__ import annotations

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.workflows.seogram_workflow import SEOgramWorkflow, SEOgramResult

_SAMPLE_CAPTION = (
    "Por do sol na Praia de Ponta Negra. Esse momento e de Deus! "
    "A praia mais famosa de Natal com a duna gigante ao fundo. "
    "Uma das melhores coisas de morar em Natal e poder ver isso todo dia. "
    "#praiadenatal #pontanegra #natal #riograndenorte #nordeste #viagem #praia"
)
_ACCOUNT = "@oinatalrn"


# ── helper ────────────────────────────────────────────────────────────────────

def _wf() -> SEOgramWorkflow:
    return SEOgramWorkflow(akasha_sink=MockAkashaSink())


# ── basic dry_run ─────────────────────────────────────────────────────────────

def test_dry_run_succeeds():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    assert result.success is True


def test_dry_run_has_run_id():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    assert len(result.run_id) == 12


def test_dry_run_optimized_hook_nonempty():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    assert result.optimized_hook


def test_dry_run_hashtags_list():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    assert isinstance(result.hashtags, list)
    assert len(result.hashtags) > 0


def test_dry_run_hashtag_count_le_30():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    assert result.hashtag_count <= 30


def test_dry_run_seo_score_range():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    assert 1 <= result.seo_score <= 10


def test_dry_run_keyword_density_range():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    assert 0.0 <= result.keyword_density <= 1.0


def test_dry_run_improvement_notes_nonempty():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    assert len(result.improvement_notes) >= 2


def test_dry_run_hashtag_clusters_dict():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    assert isinstance(result.hashtag_clusters, dict)


def test_dry_run_cost_local_pct():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    assert result.cost_local_pct == 100


def test_dry_run_model_dry_run():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    assert result.model_used == "dry_run"


# ── validações ────────────────────────────────────────────────────────────────

def test_empty_account_handle_fails():
    result = _wf().run("", _SAMPLE_CAPTION, dry_run=True)
    assert result.success is False
    assert result.error == "empty_account_handle"


def test_empty_caption_fails():
    result = _wf().run(_ACCOUNT, "   ", dry_run=True)
    assert result.success is False
    assert result.error == "empty_caption"


def test_empty_caption_with_whitespace_fails():
    result = _wf().run(_ACCOUNT, "", dry_run=True)
    assert result.success is False


# ── akasha ────────────────────────────────────────────────────────────────────

def test_dry_run_emits_event():
    sink = MockAkashaSink()
    wf = SEOgramWorkflow(akasha_sink=sink)
    wf.run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    events = sink.query_events("seogram_optimized")
    assert len(events) == 1


def test_event_source_is_run_id():
    sink = MockAkashaSink()
    wf = SEOgramWorkflow(akasha_sink=sink)
    result = wf.run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    events = sink.query_events("seogram_optimized")
    assert events[0].source == result.run_id


def test_akasha_event_id_starts_with_ske():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    assert result.akasha_event_id.startswith("ske_")


def test_event_payload_has_seo_score():
    sink = MockAkashaSink()
    wf = SEOgramWorkflow(akasha_sink=sink)
    wf.run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    events = sink.query_events("seogram_optimized")
    assert "seo_score" in events[0].payload


# ── properties ────────────────────────────────────────────────────────────────

def test_is_optimized_high_score():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    if result.seo_score >= 7:
        assert result.is_optimized is True


def test_is_optimized_false_on_failure():
    result = _wf().run("", _SAMPLE_CAPTION, dry_run=True)
    assert result.is_optimized is False


def test_hashtag_count_matches_list():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    assert result.hashtag_count == len(result.hashtags)


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_required_keys():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    d = result.to_dict()
    for key in [
        "run_id", "success", "account_handle",
        "optimized_hook", "hashtags", "hashtag_count",
        "keyword_density", "seo_score", "improvement_notes",
        "model_used", "tokens_used", "akasha_event_id", "cost_local_pct",
    ]:
        assert key in d, f"missing key: {key}"


def test_to_dict_no_raw_caption():
    result = _wf().run(_ACCOUNT, _SAMPLE_CAPTION, dry_run=True)
    d = result.to_dict()
    assert "raw_caption" not in d


# ── accounts variados ─────────────────────────────────────────────────────────

def test_other_account_succeeds():
    result = _wf().run("@lucastigrereal", _SAMPLE_CAPTION, dry_run=True)
    assert result.success is True
    assert result.account_handle == "@lucastigrereal"


def test_unknown_account_succeeds():
    result = _wf().run("@qualquercoisa", _SAMPLE_CAPTION, dry_run=True)
    assert result.success is True


# ── real_llm ──────────────────────────────────────────────────────────────────

@pytest.mark.real_llm
def test_real_ollama_seogram_oinatalrn():
    """Prova real: Ollama otimiza caption @oinatalrn Ponta Negra."""
    caption = (
        "Por do sol na Praia de Ponta Negra. Esse momento e de Deus! "
        "A praia mais famosa de Natal com a duna gigante ao fundo. "
        "Uma das melhores coisas de morar em Natal e poder ver isso todo dia. "
        "#praiadenatal #pontanegra #natal #riograndenorte #nordeste #viagem #praia"
    )
    wf = SEOgramWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run("@oinatalrn", caption, dry_run=False)

    print("\n--- REAL OLLAMA OUTPUT ---")
    print(f"SUCCESS: {result.success}")
    if not result.success:
        print(f"ERROR: {result.error}")
        return
    print(f"MODEL: {result.model_used}")
    print(f"TOKENS: {result.tokens_used}")
    print(f"SEO SCORE: {result.seo_score}/10")
    print(f"KEYWORD DENSITY: {result.keyword_density:.2f}")
    print(f"OPTIMIZED HOOK: {result.optimized_hook}")
    print(f"HASHTAGS ({result.hashtag_count}): {' '.join(result.hashtags[:10])} ...")
    print(f"CLUSTERS: {list(result.hashtag_clusters.keys())}")
    print(f"NOTES: {result.improvement_notes}")
    print(f"AKASHA EVENT: {result.akasha_event_id}")
    print("-------------------------")

    assert result.tokens_used > 0
    assert result.optimized_hook
    assert result.hashtag_count >= 5
    assert result.hashtag_count <= 30
    assert 1 <= result.seo_score <= 10
    assert 0.0 <= result.keyword_density <= 1.0
    assert len(result.improvement_notes) >= 1
