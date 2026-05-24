"""E2E tests — CaptionGeneratorWorkflow (Onda 32).

Suite dividida em duas marcas:
  - sem marca: usa MockLLMAdapter (dry_run=True) — rápido, sem IO
  - @pytest.mark.real_llm: chama Ollama real (llama3.1:8b) — prova fundação real

Cobertura (mock):
  - run() basic: success, run_id, account_handle, format, topic
  - full_caption property: hook + body + cta + hashtags presentes
  - char_count > 0
  - akasha evento emitido com source=run_id
  - to_dict keys
  - cost_local_pct = 100
  - erros: empty_account_handle, empty_topic, invalid_format
  - dry_run=True usa MockLLMAdapter (model_used = mock/deterministic)

Cobertura (real):
  - Ollama llama3.1:8b gera hook em português não vazio
  - output tem estrutura JSON válida (hook/body/cta/hashtags)
  - tokens_used > 0
  - legenda real mostrada no log
"""
from __future__ import annotations

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.caption_generator_workflow import CaptionGeneratorWorkflow


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_wf() -> tuple[CaptionGeneratorWorkflow, MockAkashaSink]:
    sink = MockAkashaSink()
    return CaptionGeneratorWorkflow(akasha_sink=sink), sink


_HANDLE = "@oinatalrn"
_TOPIC = "Praia de Ponta Negra ao entardecer — cenas únicas do pôr do sol"


# ── mock tests (dry_run=True, sem Ollama) ────────────────────────────────────

def test_run_succeeds():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.success is True


def test_run_creates_run_id():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.run_id
    assert len(result.run_id) == 12


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


def test_run_format_reels():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, format="REELS", dry_run=True)
    assert result.format == "REELS"


def test_run_format_lowercase_normalised():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, format="carousel", dry_run=True)
    assert result.format == "CAROUSEL"


def test_run_objective_default_alcance():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.objective == "alcance"


def test_dry_run_uses_mock_model():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.model_used == "mock/deterministic"


def test_cost_local_pct_100():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.cost_local_pct == 100


def test_hook_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert len(result.hook) > 0


def test_hashtags_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert len(result.hashtags) > 0


def test_full_caption_nonempty():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert len(result.full_caption) > 20


def test_char_count_positive():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.char_count > 0


def test_akasha_event_emitted():
    wf, sink = _make_wf()
    wf.run(_HANDLE, _TOPIC, dry_run=True)
    events = sink.query_events("caption_generated")
    assert len(events) == 1


def test_akasha_event_source_is_run_id():
    wf, sink = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    events = sink.query_events("caption_generated")
    assert events[0].source == result.run_id


def test_akasha_event_id_prefix():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    assert result.akasha_event_id.startswith("ske_")


def test_akasha_event_status_written():
    wf, sink = _make_wf()
    wf.run(_HANDLE, _TOPIC, dry_run=True)
    events = sink.query_events("caption_generated")
    assert events[0].status == SinkStatus.WRITTEN


def test_to_dict_keys():
    wf, _ = _make_wf()
    result = wf.run(_HANDLE, _TOPIC, dry_run=True)
    d = result.to_dict()
    for key in ["run_id", "success", "account_handle", "topic", "format",
                "objective", "hook", "body", "cta", "hashtags", "model_used",
                "tokens_used", "char_count", "akasha_event_id", "cost_local_pct"]:
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
    result = wf.run(_HANDLE, _TOPIC, format="VIDEO", dry_run=True)
    assert result.success is False
    assert "invalid_format" in result.error


def test_error_result_has_run_id():
    wf, _ = _make_wf()
    result = wf.run("", _TOPIC, dry_run=True)
    assert len(result.run_id) == 12


# ── REAL LLM test — chama Ollama (llama3.1:8b) ───────────────────────────────

@pytest.mark.real_llm
def test_real_ollama_caption_oinatalrn():
    """PROVA REAL: Ollama llama3.1:8b gera legenda para @oinatalrn.

    Este teste NÃO usa mock — chama o modelo real.
    Output completo impresso no log para inspeção humana.
    """
    from src.agentic.ollama_adapter import OllamaAdapter

    sink = MockAkashaSink()
    wf = CaptionGeneratorWorkflow(
        llm=OllamaAdapter(model="llama3.1:8b"),
        akasha_sink=sink,
    )

    result = wf.run(
        account_handle="@oinatalrn",
        topic="Praia de Ponta Negra ao entardecer — cenas únicas do pôr do sol em Natal/RN",
        format="FEED",
        objective="alcance",
        dry_run=False,
    )

    # Imprime output real para EVOLUCAO_LOG
    print("\n" + "=" * 60)
    print(f"MODEL: {result.model_used} | TOKENS: {result.tokens_used}")
    print(f"HOOK: {result.hook}")
    print(f"BODY: {result.body}")
    print(f"CTA:  {result.cta}")
    print(f"TAGS: {' '.join(result.hashtags)}")
    print(f"CHARS: {result.char_count}")
    print("LEGENDA COMPLETA:")
    print(result.full_caption)
    print("=" * 60)

    assert result.success is True
    assert result.tokens_used > 0
    assert len(result.hook) > 0
    assert len(result.hashtags) >= 3
    assert result.char_count > 50
    assert result.model_used == "llama3.1:8b"
