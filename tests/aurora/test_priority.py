"""Tests for AuroraPriority — A1 priorizador por impacto.

Cobertura mínima:
  - score calculation (3 dimensões)
  - ordenação por score DESC
  - cores (green/yellow/red)
  - rank atribuído corretamente
  - lista vazia → warnings, items=[]
  - itens inválidos → ignorados com warning
  - to_dict() round-trip
  - top(N)
  - summary() retorna string com todos os itens
  - keyword específica por dimensão
  - anti-teatro: score reflete valor real dos dados
"""
from __future__ import annotations

import pytest

from src.aurora.priority import AuroraPriority, PriorityItem, PriorityReport


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def prio() -> AuroraPriority:
    return AuroraPriority(dry_run=True)


# ---------------------------------------------------------------------------
# 1. API básica — rank() retorna PriorityReport
# ---------------------------------------------------------------------------

class TestRankRetorno:
    def test_returns_priority_report(self, prio):
        r = prio.rank(["Fechar contrato hotel"])
        assert isinstance(r, PriorityReport)

    def test_report_id_not_empty(self, prio):
        r = prio.rank(["qualquer coisa"])
        assert r.report_id and len(r.report_id) == 8

    def test_generated_at_iso(self, prio):
        r = prio.rank(["qualquer coisa"])
        # ISO 8601 começa com 4 dígitos de ano
        assert r.generated_at[:4].isdigit()


# ---------------------------------------------------------------------------
# 2. Lista vazia
# ---------------------------------------------------------------------------

class TestListaVazia:
    def test_empty_list_zero_items(self, prio):
        r = prio.rank([])
        assert r.total_items == 0
        assert r.items == []

    def test_empty_list_warning(self, prio):
        r = prio.rank([])
        assert r.warnings  # deve ter ao menos 1 aviso


# ---------------------------------------------------------------------------
# 3. Itens inválidos
# ---------------------------------------------------------------------------

class TestItensInvalidos:
    def test_none_ignored(self, prio):
        r = prio.rank([None, "Fechar hotel"])  # type: ignore[list-item]
        assert r.total_items == 1

    def test_empty_string_ignored(self, prio):
        r = prio.rank(["", "Fechar hotel"])
        assert r.total_items == 1

    def test_whitespace_string_ignored(self, prio):
        r = prio.rank(["   ", "Fechar hotel"])
        assert r.total_items == 1

    def test_invalid_item_generates_warning(self, prio):
        r = prio.rank([None, "Fechar hotel"])  # type: ignore[list-item]
        assert any("inválido" in w or "invalid" in w.lower() for w in r.warnings)


# ---------------------------------------------------------------------------
# 4. Dimensão Dinheiro (peso 50)
# ---------------------------------------------------------------------------

class TestDimensaoDinheiro:
    def test_hotel_tem_score_dinheiro(self, prio):
        r = prio.rank(["Fechar contrato com hotel Ponta Negra"])
        item = r.items[0]
        assert item.score_dinheiro > 0

    def test_sem_keyword_dinheiro_zero(self, prio):
        # Texto sem keywords de dinheiro, desbloqueio ou risco
        r = prio.rank(["Organizar gaveta do escritório"])
        item = r.items[0]
        assert item.score_dinheiro == 0

    def test_keyword_r_cifrao(self, prio):
        r = prio.rank(["Receber R$1500 do cliente"])
        item = r.items[0]
        assert item.score_dinheiro > 0


# ---------------------------------------------------------------------------
# 5. Dimensão Desbloqueio (peso 30)
# ---------------------------------------------------------------------------

class TestDimensaoDesbloqueio:
    def test_depende_tem_score_desbloqueio(self, prio):
        r = prio.rank(["Deploy depende desse PR estar aprovado"])
        item = r.items[0]
        assert item.score_desbloqueio > 0

    def test_travado_tem_score_desbloqueio(self, prio):
        r = prio.rank(["Time está travado esperando resposta"])
        item = r.items[0]
        assert item.score_desbloqueio > 0


# ---------------------------------------------------------------------------
# 6. Dimensão Risco (peso 20)
# ---------------------------------------------------------------------------

class TestDimensaoRisco:
    def test_deadline_hoje_tem_score_risco(self, prio):
        r = prio.rank(["Prazo deadline vence hoje para envio"])
        item = r.items[0]
        assert item.score_risco > 0

    def test_urgente_tem_score_risco(self, prio):
        r = prio.rank(["Situação urgente — pode perder o cliente"])
        item = r.items[0]
        assert item.score_risco > 0


# ---------------------------------------------------------------------------
# 7. Scores somam corretamente
# ---------------------------------------------------------------------------

class TestSomaDimensoes:
    def test_score_soma_dimensoes(self, prio):
        r = prio.rank(["Fechar contrato com hotel — prazo hoje"])
        item = r.items[0]
        assert item.score == item.score_dinheiro + item.score_desbloqueio + item.score_risco

    def test_sem_keywords_score_zero(self, prio):
        r = prio.rank(["Organizar gaveta do escritório"])
        assert r.items[0].score == 0


# ---------------------------------------------------------------------------
# 8. Cores (green >= 70, yellow >= 40, red < 40)
# ---------------------------------------------------------------------------

class TestCores:
    def test_zero_score_red(self, prio):
        r = prio.rank(["Organizar gaveta do escritório"])
        assert r.items[0].color == "red"

    def test_high_score_green(self, prio):
        # hotel + collab + r$ + prazo + urgente = múltiplas keywords → alto score
        r = prio.rank(["Fechar proposta collab hotel cliente R$ urgente prazo hoje"])
        item = r.items[0]
        assert item.score >= 70
        assert item.color == "green"

    def test_color_consistency(self, prio):
        r = prio.rank([
            "Fechar proposta collab hotel cliente R$ urgente prazo hoje",
            "Responder DMs pendentes",
        ])
        for item in r.items:
            if item.score >= 70:
                assert item.color == "green"
            elif item.score >= 40:
                assert item.color == "yellow"
            else:
                assert item.color == "red"


# ---------------------------------------------------------------------------
# 9. Ordenação e rank
# ---------------------------------------------------------------------------

class TestOrdenacaoERank:
    def test_ordered_desc_by_score(self, prio):
        r = prio.rank([
            "Organizar gaveta",
            "Fechar contrato hotel R$ urgente prazo hoje",
            "Depende de resposta do cliente para liberar collab",
        ])
        scores = [i.score for i in r.items]
        assert scores == sorted(scores, reverse=True)

    def test_rank_starts_at_one(self, prio):
        r = prio.rank(["A", "B", "C"])
        assert r.items[0].rank == 1

    def test_rank_sequential(self, prio):
        r = prio.rank(["Fechar hotel", "Responder DMs", "Organizar"])
        ranks = [i.rank for i in r.items]
        assert ranks == list(range(1, len(ranks) + 1))

    def test_high_priority_count(self, prio):
        r = prio.rank([
            "Fechar proposta collab hotel cliente R$ urgente prazo hoje",
            "Organizar gaveta",
        ])
        assert r.high_priority >= 1


# ---------------------------------------------------------------------------
# 10. to_dict() e round-trip
# ---------------------------------------------------------------------------

class TestToDict:
    def test_report_to_dict_has_keys(self, prio):
        r = prio.rank(["Fechar hotel"])
        d = r.to_dict()
        for key in ("report_id", "generated_at", "items", "total_items", "high_priority", "warnings"):
            assert key in d

    def test_item_to_dict_has_keys(self, prio):
        r = prio.rank(["Fechar hotel"])
        d = r.items[0].to_dict()
        for key in ("item_id", "texto", "score", "color", "score_dinheiro",
                    "score_desbloqueio", "score_risco", "reasoning", "rank"):
            assert key in d

    def test_items_in_dict_match_items(self, prio):
        texts = ["Fechar hotel prazo hoje", "Organizar gaveta"]
        r = prio.rank(texts)
        d = r.to_dict()
        assert d["total_items"] == len(r.items)
        assert len(d["items"]) == len(r.items)


# ---------------------------------------------------------------------------
# 11. top(N)
# ---------------------------------------------------------------------------

class TestTop:
    def test_top_returns_n_items(self, prio):
        r = prio.rank(["A", "B", "C", "D"])
        assert len(r.top(2)) == 2

    def test_top_are_highest_rank(self, prio):
        r = prio.rank(["Fechar hotel R$ hoje", "Responder DMs", "Organizar"])
        top1 = r.top(1)
        assert top1[0].rank == 1


# ---------------------------------------------------------------------------
# 12. summary() e summary_line()
# ---------------------------------------------------------------------------

class TestSummary:
    def test_summary_contains_all_items(self, prio):
        texts = ["Fechar hotel prazo hoje", "Organizar gaveta"]
        r = prio.rank(texts)
        s = r.summary()
        assert "PRIORIDADE AURORA" in s
        # Cada item deve aparecer no summary (primeiros 60 chars do texto)
        for item in r.items:
            assert item.texto[:30] in s

    def test_summary_line_has_score(self, prio):
        r = prio.rank(["Fechar hotel R$ urgente prazo hoje"])
        line = r.items[0].summary_line()
        assert str(r.items[0].score) in line


# ---------------------------------------------------------------------------
# 13. Anti-teatro — score reflete a query real
# ---------------------------------------------------------------------------

class TestAntiTeatro:
    def test_item_id_reflects_position(self, prio):
        r = prio.rank(["primeiro", "segundo"])
        # item_ids são derivados do índice original
        ids = {i.item_id for i in r.items}
        assert "item_000" in ids
        assert "item_001" in ids

    def test_reasoning_non_empty(self, prio):
        r = prio.rank(["qualquer texto"])
        assert r.items[0].reasoning  # nunca vazio

    def test_high_impact_item_ranked_first(self, prio):
        r = prio.rank([
            "Organizar gaveta",
            "Fechar proposta hotel cliente R$ urgente prazo hoje",
        ])
        # O item de alto impacto deve ser rank 1
        top = r.items[0]
        assert "hotel" in top.texto.lower() or top.score > 0

    def test_score_bounded_0_100(self, prio):
        r = prio.rank([
            "Fechar contrato publi collab hotel restaurante cliente R$ venda prazo deadline urgente hoje",
            "Organizar arquivos",
        ])
        for item in r.items:
            assert 0 <= item.score <= 100
