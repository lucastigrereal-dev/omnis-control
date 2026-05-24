"""Prova REAL — ContentCalendarWorkflow com dados reais de @oinatalrn.

Dívida retroativa da Onda 34: ContentCalendarWorkflow foi testado com dados
placeholder na Onda 17. Este arquivo prova com inputs reais do negócio do Lucas.

Dados reais:
  - @oinatalrn: perfil Turismo Natal/RN (630K seguidores)
  - Tópicos reais do calendário editorial da página
  - Data de início fixa para verificar datas reais do calendário
"""
from __future__ import annotations

from datetime import date

from src.akasha_event_sink.adapter import MockAkashaSink
from src.workflows.content_calendar_workflow import ContentCalendarWorkflow


_OINATAL_TOPICS = ["praias", "hoteis", "gastronomia", "turismo"]
_HANDLE = "@oinatalrn"


def test_real_oinatalrn_7_days():
    """PROVA REAL: calendário 7 dias para @oinatalrn com tópicos reais."""
    sink = MockAkashaSink()
    wf = ContentCalendarWorkflow(akasha_sink=sink)
    start = date(2026, 6, 2)  # segunda-feira real
    result = wf.run(_HANDLE, _OINATAL_TOPICS, num_days=7, start_date=start)

    print("\n" + "=" * 60)
    print(f"RUN_ID: {result.run_id} | ACCOUNT: {result.account_handle}")
    print(f"PERIODO: {start} a 2026-06-08 | ITEMS: {result.items_count}")
    print(f"FORMAT_DIST: {result.format_distribution}")
    print()
    for item in result.items:
        print(f"  {item.date} | {str(item.format):8s} | {item.notes[:60]}")
    print("=" * 60)

    assert result.success is True
    assert result.items_count == 7
    assert result.account_handle == _HANDLE
    assert result.items[0].date == "2026-06-02"
    assert result.items[6].date == "2026-06-08"


def test_real_topics_roundrobin():
    """Tópicos reais aparecem em round-robin nos itens."""
    sink = MockAkashaSink()
    wf = ContentCalendarWorkflow(akasha_sink=sink)
    result = wf.run(_HANDLE, _OINATAL_TOPICS, num_days=8)

    topics_in_notes = [item.notes for item in result.items]
    assert "Tópico: praias" in topics_in_notes[0]
    assert "Tópico: hoteis" in topics_in_notes[1]
    assert "Tópico: gastronomia" in topics_in_notes[2]
    assert "Tópico: turismo" in topics_in_notes[3]
    assert "Tópico: praias" in topics_in_notes[4]  # ciclo reinicia


def test_real_batch_6_profiles():
    """run_batch() com os 6 perfis reais do Lucas — 6 × 7 = 42 items."""
    sink = MockAkashaSink()
    wf = ContentCalendarWorkflow(akasha_sink=sink)

    accounts = [
        {"handle": "@lucastigrereal",    "topics": ["lifestyle", "viagem", "bastidores"]},
        {"handle": "@oinatalrn",          "topics": ["praias", "hoteis", "gastronomia", "turismo"]},
        {"handle": "@agenteviajabrasil",  "topics": ["destinos", "dicas", "roteiros"]},
        {"handle": "@afamiliatigrereal",  "topics": ["familia", "viagem", "experiencias"]},
        {"handle": "@oquecomernatalrn",   "topics": ["restaurantes", "gastronomia", "drinks"]},
        {"handle": "@natalaivoueu",       "topics": ["praias", "guia", "turismo local"]},
    ]

    result = wf.run_batch(accounts, num_days=7)

    print("\n" + "=" * 60)
    print(f"BATCH RUN_ID: {result.run_id}")
    print(f"CONTAS: {result.accounts_total} | OK: {result.accounts_ok} | FALHAS: {result.accounts_failed}")
    print(f"TOTAL_ITEMS: {result.total_items} (esperado: 42)")
    print()
    for cal in result.calendars:
        print(f"  {cal.account_handle:30s} -> {cal.items_count} items")
    print("=" * 60)

    assert result.success is True
    assert result.accounts_total == 6
    assert result.accounts_ok == 6
    assert result.total_items == 42
    assert result.accounts_failed == 0
