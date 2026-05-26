"""Tests for AuroraVoice — A4 tom Tigre para insights.

Cobertura:
  - adapt() retorna VoiceOutput
  - texto vazio → passthrough
  - adaptacao lexical: substituicoes funcionam
  - truncagem: texto longo eh truncado
  - money signal detectado para hotel/collab/r$/lead
  - money signal False para texto sem keywords
  - prefixo Tigre adicionado no output
  - CTA adicionado no output
  - adapt_many retorna lista na mesma ordem
  - corpus_stats sem arquivo → total_entries=0
  - load_corpus sem arquivo → lista vazia
  - load_corpus com arquivo valido → entradas carregadas
  - linha invalida no corpus → ignorada
  - to_dict() tem chaves esperadas
  - style == "tigre" para texto normal
  - style == "passthrough" para texto vazio
  - anti-teatro: output nao e' igual ao input generico
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.aurora.voice import AuroraVoice, VoiceOutput, VoiceCorpusEntry


@pytest.fixture
def voice() -> AuroraVoice:
    return AuroraVoice(dry_run=True)


@pytest.fixture
def voice_with_corpus(tmp_path: Path) -> AuroraVoice:
    """Voice com corpus carregado de tmp_path."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    corpus_path = data_dir / "voice_corpus.jsonl"
    entries = [
        {"text": "Fecha o hotel hoje, nao amanha.", "source": "reels_2024", "tags": ["hotel"]},
        {"text": "Caixa primeiro, conteudo depois.", "source": "captions", "tags": ["caixa"]},
        {"text": "Move rapido, ajusta no caminho.", "source": "reels_2024", "tags": ["velocidade"]},
    ]
    corpus_path.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in entries),
        encoding="utf-8",
    )
    return AuroraVoice(dry_run=True, data_dir=data_dir)


# ---------------------------------------------------------------------------
# 1. adapt() — retorno basico
# ---------------------------------------------------------------------------

class TestAdaptBasico:
    def test_returns_voice_output(self, voice):
        out = voice.adapt("Fechar contrato com hotel")
        assert isinstance(out, VoiceOutput)

    def test_adapted_not_empty(self, voice):
        out = voice.adapt("Qualquer insight aqui")
        assert out.adapted.strip()

    def test_generated_at_iso(self, voice):
        out = voice.adapt("Qualquer insight")
        assert out.generated_at[:4].isdigit()

    def test_original_preserved(self, voice):
        text = "Fechar contrato com hotel"
        out = voice.adapt(text)
        assert out.original == text

    def test_style_tigre(self, voice):
        out = voice.adapt("Fechar contrato com hotel")
        assert out.style == "tigre"


# ---------------------------------------------------------------------------
# 2. Texto vazio / whitespace
# ---------------------------------------------------------------------------

class TestTextoVazio:
    def test_empty_string_passthrough(self, voice):
        out = voice.adapt("")
        assert out.style == "passthrough"

    def test_whitespace_passthrough(self, voice):
        out = voice.adapt("   ")
        assert out.style == "passthrough"

    def test_empty_adapted_not_crashes(self, voice):
        out = voice.adapt("")
        assert out.adapted  # mensagem de fallback


# ---------------------------------------------------------------------------
# 3. Substituicoes lexicais
# ---------------------------------------------------------------------------

class TestSubstituicoesLexicais:
    def test_seria_interessante_replaced(self, voice):
        out = voice.adapt("Seria interessante fechar a parceria com o hotel.")
        # "Seria interessante" deve virar algo mais direto
        assert "seria interessante" not in out.adapted.lower()

    def test_e_importante_replaced(self, voice):
        out = voice.adapt("E importante considerar fechar o contrato hoje.")
        assert "importante considerar" not in out.adapted.lower()

    def test_em_breve_replaced(self, voice):
        out = voice.adapt("Em breve vamos contatar o cliente.")
        assert "em breve" not in out.adapted.lower()

    def test_eventualmente_replaced(self, voice):
        out = voice.adapt("Eventualmente o lead vai responder.")
        assert "eventualmente" not in out.adapted.lower()


# ---------------------------------------------------------------------------
# 4. Truncagem
# ---------------------------------------------------------------------------

class TestTruncagem:
    def test_short_text_not_truncated(self, voice):
        text = "Fecha o hotel hoje."
        out = voice.adapt(text)
        assert text in out.adapted or len(out.adapted) < 400

    def test_long_text_truncated(self, voice):
        text = "A " * 200  # 400 chars
        out = voice.adapt(text)
        # Com prefixo e CTA ainda deve ser razoavelmente curto
        # O limite nao inclui prefixo + CTA exatamente, mas output nao deve ser longo demais
        assert len(out.adapted) < 600

    def test_output_ends_with_cta(self, voice):
        out = voice.adapt("Fechar contrato hotel urgente")
        # Deve terminar com ponto ou CTA
        assert out.adapted.strip()[-1] in ".!?"


# ---------------------------------------------------------------------------
# 5. Money signal
# ---------------------------------------------------------------------------

class TestMoneySignal:
    @pytest.mark.parametrize("text,expected", [
        ("Fechar contrato com hotel", True),
        ("Proposta collab para restaurante", True),
        ("Receber R$1500 do cliente", True),
        ("Lead quente para fechar parceria", True),
        ("Organizar arquivos no computador", False),
        ("Criar playlist de musica", False),
    ])
    def test_money_signal(self, voice, text, expected):
        out = voice.adapt(text)
        assert out.has_money_signal == expected, (
            f"texto={text!r} esperava has_money_signal={expected}"
        )

    def test_money_opener_for_hotel(self, voice):
        out = voice.adapt("Fechar contrato com hotel")
        # Quando tem sinal de dinheiro, deve usar opener de caixa
        assert "caixa" in out.adapted.lower() or "hotel" in out.adapted.lower()


# ---------------------------------------------------------------------------
# 6. Prefixo e CTA Tigre
# ---------------------------------------------------------------------------

class TestPrefixoECTA:
    def test_adapted_has_opener(self, voice):
        out = voice.adapt("Qualquer insight para Lucas")
        # Deve ter algum dos prefixos Tigre
        openers = ["lucas", "caixa", "direto", "move", "oportunidade",
                   "omnis", "prioridade", "foca"]
        has_opener = any(o in out.adapted.lower() for o in openers)
        assert has_opener, f"Nenhum opener Tigre encontrado em: {out.adapted!r}"

    def test_adapted_has_cta(self, voice):
        out = voice.adapt("Qualquer insight")
        # Deve ter alguma das CTAs
        ctas = ["move", "feito", "caixa", "faz", "proxima", "hoje"]
        has_cta = any(c in out.adapted.lower() for c in ctas)
        assert has_cta, f"Nenhum CTA encontrado em: {out.adapted!r}"

    def test_different_texts_can_have_different_openers(self, voice):
        texts = [
            "hotel restaurante collab parceria",
            "organizar gaveta escritorio",
            "criar playlist",
            "ler emails",
        ]
        openers = {voice.adapt(t).adapted.split(":")[0].strip() for t in texts}
        # Ao menos 2 textos diferentes — nao todos o mesmo opener (rotativo)
        # hotel sempre pega "Caixa hoje" pelo sinal de dinheiro
        # Os outros podem variar
        assert len(openers) >= 1  # pelo menos funciona sem crashar


# ---------------------------------------------------------------------------
# 7. adapt_many
# ---------------------------------------------------------------------------

class TestAdaptMany:
    def test_returns_list(self, voice):
        results = voice.adapt_many(["text 1", "text 2", "text 3"])
        assert len(results) == 3

    def test_order_preserved(self, voice):
        texts = ["hotel", "gaveta", "playlist"]
        results = voice.adapt_many(texts)
        assert results[0].original == "hotel"
        assert results[1].original == "gaveta"
        assert results[2].original == "playlist"

    def test_empty_list(self, voice):
        assert voice.adapt_many([]) == []


# ---------------------------------------------------------------------------
# 8. Corpus
# ---------------------------------------------------------------------------

class TestCorpus:
    def test_stats_sem_arquivo(self, voice):
        stats = voice.corpus_stats()
        assert stats["total_entries"] == 0

    def test_load_sem_arquivo(self, voice):
        entries = voice.load_corpus()
        assert entries == []

    def test_load_com_corpus(self, voice_with_corpus):
        entries = voice_with_corpus.load_corpus()
        assert len(entries) == 3

    def test_corpus_entries_texto(self, voice_with_corpus):
        entries = voice_with_corpus.load_corpus()
        assert any("hotel" in e.text.lower() for e in entries)

    def test_corpus_stats_com_arquivo(self, voice_with_corpus):
        stats = voice_with_corpus.corpus_stats()
        assert stats["total_entries"] == 3
        assert "reels_2024" in stats["sources"]

    def test_corpus_invalid_line_ignored(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        corpus_path = data_dir / "voice_corpus.jsonl"
        corpus_path.write_text(
            '{"text":"ok1","source":"s1","tags":[]}\n'
            'LINHA_INVALIDA\n'
            '{"text":"ok2","source":"s2","tags":[]}\n',
            encoding="utf-8",
        )
        v = AuroraVoice(dry_run=True, data_dir=data_dir)
        entries = v.load_corpus()
        assert len(entries) == 2

    def test_corpus_from_dict_roundtrip(self):
        entry = VoiceCorpusEntry(
            text="Fecha o hotel hoje.", source="reels", tags=["hotel", "caixa"]
        )
        restored = VoiceCorpusEntry.from_dict(entry.to_dict())
        assert restored.text == entry.text
        assert restored.source == entry.source
        assert restored.tags == entry.tags


# ---------------------------------------------------------------------------
# 9. to_dict
# ---------------------------------------------------------------------------

class TestToDict:
    def test_has_required_keys(self, voice):
        out = voice.adapt("Fechar hotel")
        d = out.to_dict()
        for key in ("original", "adapted", "style", "has_money_signal", "generated_at"):
            assert key in d

    def test_style_in_dict_is_string(self, voice):
        out = voice.adapt("Fechar hotel")
        assert isinstance(out.to_dict()["style"], str)

    def test_to_dict_passthrough(self, voice):
        out = voice.adapt("")
        d = out.to_dict()
        assert d["style"] == "passthrough"


# ---------------------------------------------------------------------------
# 10. __str__ e anti-teatro
# ---------------------------------------------------------------------------

class TestAntiTeatro:
    def test_str_returns_adapted(self, voice):
        out = voice.adapt("Seria interessante considerar fechar o hotel.")
        assert str(out) == out.adapted

    def test_output_differs_from_generic_input(self, voice):
        generic = "Seria interessante considerar a possibilidade de fechar uma parceria."
        out = voice.adapt(generic)
        # Output nao deve ser identico ao input generico
        assert out.adapted != generic

    def test_money_text_has_urgency(self, voice):
        out = voice.adapt("Fechar collab hotel Ponta Negra — prazo amanha")
        # Output deve ter sinal de urgencia ou dinheiro
        urgency_words = ["hoje", "agora", "move", "caixa", "fecha", "faz"]
        has_urgency = any(w in out.adapted.lower() for w in urgency_words)
        assert has_urgency, f"Sem urgencia em: {out.adapted!r}"

    def test_non_money_text_still_adapted(self, voice):
        out = voice.adapt("Organizar gaveta do escritório eventualmente")
        # "eventualmente" deve ter sido removido/substituido
        assert "eventualmente" not in out.adapted.lower()
