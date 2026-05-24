"""Retroativa Onda 35 — ContentQualityWorkflow com captions reais.

ContentQualityWorkflow usa QualityScorer (regras deterministicas, zero LLM).
Prova com conteudo real dos perfis do Lucas Tigre:
  - Caption real de @oinatalrn (Ponta Negra)
  - Caption ruim propositalmente (muito curta, sem CTA, sem hashtag)
  - Caption excelente (gancho + corpo + CTA + hashtags)
  - Lote misto: 3 captions, distribuicao de grades
  - Comparacao: boa > ruim
"""
from __future__ import annotations

from src.akasha_event_sink.adapter import MockAkashaSink
from src.workflows.content_quality_workflow import ContentQualityWorkflow

# Captions reais simuladas a partir dos perfis do Lucas
_CAPTION_PONTA_NEGRA = (
    "Por do sol na Praia de Ponta Negra. Esse momento e de Deus! "
    "A praia mais famosa de Natal com a duna gigante ao fundo. "
    "Uma das melhores coisas de morar em Natal e poder ver isso a vida toda. "
    "Salva esse post para sua lista de lugares para visitar em Natal! "
    "#praiadenatal #pontanegra #natal #riograndenorte #nordeste #viagem #praia "
    "#turismo #destinosbrasil #praias #ferias #verao"
)

_CAPTION_RUIM = "Natal RN"

_CAPTION_EXCELENTE = (
    "Voce PRECISA ir a Praia de Ponta Negra antes de morrer! "
    "A duna do Morro do Careca ao fundo faz dessa praia um cartao postal unico no Brasil. "
    "Aguas mornas, piscinas naturais e um por do sol que para o tempo. "
    "Ja esteve aqui? Marca quem voce levaria! "
    "-> Salva para sua lista de viagens "
    "#pontanegra #natal #riograndenorte #nordeste #turismo #viagem #praia "
    "#praiasnordeste #destinosbrasil #verao #ferias #rn #natality #oinatalrn"
)


def _wf() -> ContentQualityWorkflow:
    return ContentQualityWorkflow(akasha_sink=MockAkashaSink())


def test_real_caption_ponta_negra_scores_above_5():
    wf = _wf()
    result = wf.run([
        {"id": "ponta-negra-01", "type": "caption", "content": _CAPTION_PONTA_NEGRA},
    ], dry_run=False)

    print("\n--- ContentQuality REAL: Ponta Negra ---")
    r = result.reports[0]
    print(f"SCORE: {r.overall_score:.1f}/10")
    print(f"GRADE: {r.grade}")
    print(f"READY: {r.ready_for_use}")
    print(f"DIMS_PASSED: {r.passed_dimensions}/{len(r.dimensions)}")
    print("----------------------------------------")

    assert result.success is True
    assert result.items_total == 1
    assert r.overall_score > 5.0
    assert r.grade in {"A", "B", "C"}


def test_real_caption_ruim_scores_below_good():
    wf = _wf()
    result = wf.run([
        {"id": "ruim-01", "type": "caption", "content": _CAPTION_RUIM},
    ], dry_run=False)

    print("\n--- ContentQuality REAL: caption ruim ---")
    r = result.reports[0]
    print(f"SCORE: {r.overall_score:.1f}/10")
    print(f"GRADE: {r.grade}")
    print(f"DIMS_PASSED: {r.passed_dimensions}/{len(r.dimensions)}")
    print("-----------------------------------------")

    assert result.success is True
    assert r.overall_score < 7.0


def test_real_excelente_beats_ruim():
    wf = _wf()
    result_good = wf.run([
        {"id": "excelente", "type": "caption", "content": _CAPTION_EXCELENTE},
    ], dry_run=False)
    result_bad = wf.run([
        {"id": "ruim", "type": "caption", "content": _CAPTION_RUIM},
    ], dry_run=False)

    score_good = result_good.reports[0].overall_score
    score_bad = result_bad.reports[0].overall_score

    print("\n--- ContentQuality REAL: excelente vs ruim ---")
    print(f"EXCELENTE: {score_good:.1f} ({result_good.reports[0].grade})")
    print(f"RUIM:      {score_bad:.1f} ({result_bad.reports[0].grade})")
    print("----------------------------------------------")

    assert score_good > score_bad


def test_real_lote_misto_3_captions():
    wf = _wf()
    result = wf.run([
        {"id": "ponta-negra", "type": "caption", "content": _CAPTION_PONTA_NEGRA},
        {"id": "ruim",        "type": "caption", "content": _CAPTION_RUIM},
        {"id": "excelente",   "type": "caption", "content": _CAPTION_EXCELENTE},
    ], dry_run=False)

    print("\n--- ContentQuality REAL: lote misto ---")
    for r in result.reports:
        print(f"  {r.output_id}: {r.overall_score:.1f} ({r.grade}) ready={r.ready_for_use}")
    print(f"MEDIA: {result.average_score:.1f}")
    print(f"DISTRIBUICAO: {result.grade_distribution}")
    print(f"AKASHA: {result.akasha_event_id}")
    print("----------------------------------------")

    assert result.success is True
    assert result.items_total == 3
    assert result.average_score > 0
    assert result.akasha_event_id.startswith("ske_")


def test_real_akasha_event_emitido():
    sink = MockAkashaSink()
    wf = ContentQualityWorkflow(akasha_sink=sink)
    wf.run([
        {"id": "test-real", "type": "caption", "content": _CAPTION_PONTA_NEGRA},
    ], dry_run=False)
    events = sink.query_events("content_quality_scored")
    assert len(events) == 1
    assert events[0].payload["items_total"] == 1
