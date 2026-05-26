"""Testes do ContextEngine — Camada 1 da Aurora.

Cobre: build() sem fontes externas, degradação graciosa, leitura de disco,
timeout, sources_available/failed, e anti-teatro (dado real reflete no resultado).

Não usa unittest.mock — conforme regras de testing do projeto.
Não chama Notion nem Akasha — stubs são os padrões.
"""
from __future__ import annotations

import json
import time

from src.aurora.context_engine import AuroraContext, ContextEngine, ContextResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_state(tmp_path, data: dict):
    state = tmp_path / "state.json"
    state.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return state


def _write_leads(tmp_path, leads: list[dict]):
    leads_path = tmp_path / "leads.jsonl"
    lines = [json.dumps(l, ensure_ascii=False) for l in leads]
    leads_path.write_text("\n".join(lines), encoding="utf-8")
    return leads_path


# ---------------------------------------------------------------------------
# 1. build() sem nenhuma fonte externa → retorna AuroraContext com state_json + leads
# ---------------------------------------------------------------------------

class TestBuildSemFontesExternas:
    def test_retorna_aurora_context(self, tmp_path):
        _write_state(tmp_path, {"branch": "main", "test_count": 42})
        _write_leads(tmp_path, [
            {"nome": "Hotel A", "perfil": "@ha", "temperatura": "quente",
             "valor_potencial": 990, "status": "proposta", "ultimo_contato": "2026-05-20"},
        ])
        engine = ContextEngine(data_dir=tmp_path)
        ctx = engine.build(query="hoteis")

        assert isinstance(ctx, AuroraContext)
        assert ctx.query == "hoteis"
        assert ctx.built_at  # ISO timestamp

    def test_state_json_em_sources_available(self, tmp_path, monkeypatch):
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        monkeypatch.delenv("AKASHA_DB_URL", raising=False)
        _write_state(tmp_path, {"branch": "main"})
        engine = ContextEngine(data_dir=tmp_path)
        ctx = engine.build()

        assert "state_json" in ctx.sources_available

    def test_leads_em_sources_available(self, tmp_path, monkeypatch):
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        monkeypatch.delenv("AKASHA_DB_URL", raising=False)
        _write_leads(tmp_path, [
            {"nome": "Hotel B", "perfil": "@hb", "temperatura": "morno",
             "valor_potencial": 350, "status": "novo", "ultimo_contato": "2026-05-01"},
        ])
        engine = ContextEngine(data_dir=tmp_path)
        ctx = engine.build()

        assert "leads" in ctx.sources_available


# ---------------------------------------------------------------------------
# 2. build() com NOTION_TOKEN ausente → notion em sources_failed, não crasha
# ---------------------------------------------------------------------------

class TestNotionAusente:
    def test_notion_token_ausente_nao_crasha(self, tmp_path, monkeypatch):
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        monkeypatch.delenv("AKASHA_DB_URL", raising=False)
        engine = ContextEngine(data_dir=tmp_path)
        ctx = engine.build(query="teste")

        # notion não deve aparecer em sources_available nem em sources_failed
        # (simplesmente não foi incluído nas fontes)
        assert "notion" not in ctx.sources_available
        assert "notion" not in ctx.sources_failed

    def test_notion_token_presente_ativa_fonte(self, tmp_path, monkeypatch):
        monkeypatch.setenv("NOTION_TOKEN", "fake-token-12345")
        monkeypatch.delenv("AKASHA_DB_URL", raising=False)
        engine = ContextEngine(data_dir=tmp_path)
        ctx = engine.build(query="teste")

        # O stub retorna [] mas não falha — notion deve estar em sources_available
        assert "notion" in ctx.sources_available
        # Nenhum resultado de notion (stub retorna [])
        notion_results = [r for r in ctx.results if r.source == "notion"]
        assert notion_results == []


# ---------------------------------------------------------------------------
# 3. build() com AKASHA_DB_URL ausente → akasha em sources_failed, não crasha
# ---------------------------------------------------------------------------

class TestAkashaAusente:
    def test_akasha_url_ausente_nao_crasha(self, tmp_path, monkeypatch):
        monkeypatch.delenv("AKASHA_DB_URL", raising=False)
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        engine = ContextEngine(data_dir=tmp_path)
        ctx = engine.build(query="teste")

        assert "akasha" not in ctx.sources_available
        assert "akasha" not in ctx.sources_failed

    def test_akasha_url_presente_ativa_fonte(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AKASHA_DB_URL", "postgresql://fake:5432/akasha")
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        engine = ContextEngine(data_dir=tmp_path)
        ctx = engine.build(query="teste")

        # stub retorna [] mas não falha
        assert "akasha" in ctx.sources_available
        akasha_results = [r for r in ctx.results if r.source == "akasha"]
        assert akasha_results == []


# ---------------------------------------------------------------------------
# 4. _fetch_state_json() lê do disco (tmp_path)
# ---------------------------------------------------------------------------

class TestFetchStateJson:
    def test_le_chaves_do_state(self, tmp_path):
        _write_state(tmp_path, {"branch": "feature/x", "test_count": 9999})
        engine = ContextEngine(data_dir=tmp_path)
        results = engine._fetch_state_json(query="")

        assert len(results) == 1
        r = results[0]
        assert r.source == "state_json"
        assert "branch" in r.content
        assert "feature/x" in r.content
        assert r.relevance == 1.0

    def test_state_ausente_retorna_lista_vazia(self, tmp_path):
        engine = ContextEngine(data_dir=tmp_path)
        results = engine._fetch_state_json(query="")

        assert results == []

    def test_state_corrompido_retorna_lista_vazia(self, tmp_path):
        (tmp_path / "state.json").write_text("{json inválido", encoding="utf-8")
        engine = ContextEngine(data_dir=tmp_path)
        results = engine._fetch_state_json(query="")

        assert results == []


# ---------------------------------------------------------------------------
# 5. _fetch_leads() lê JSONL (tmp_path)
# ---------------------------------------------------------------------------

class TestFetchLeads:
    def test_le_leads_do_jsonl(self, tmp_path):
        _write_leads(tmp_path, [
            {"nome": "Hotel Sol", "perfil": "@sol", "temperatura": "quente",
             "valor_potencial": 990, "status": "proposta", "ultimo_contato": "2026-05-20"},
            {"nome": "Pousada Mar", "perfil": "@mar", "temperatura": "frio",
             "valor_potencial": 350, "status": "novo", "ultimo_contato": "2026-04-01"},
        ])
        engine = ContextEngine(data_dir=tmp_path)
        results = engine._fetch_leads(query="")

        assert len(results) == 2
        sources = {r.source for r in results}
        assert sources == {"leads"}

    def test_lead_quente_tem_relevancia_maxima(self, tmp_path):
        _write_leads(tmp_path, [
            {"nome": "Hotel X", "perfil": "@x", "temperatura": "quente",
             "valor_potencial": 1200, "status": "negociando", "ultimo_contato": "2026-05-25"},
        ])
        engine = ContextEngine(data_dir=tmp_path)
        results = engine._fetch_leads(query="")

        assert results[0].relevance == 1.0

    def test_leads_ausente_retorna_lista_vazia(self, tmp_path):
        engine = ContextEngine(data_dir=tmp_path)
        results = engine._fetch_leads(query="")

        assert results == []

    def test_linha_invalida_ignorada_restante_ok(self, tmp_path):
        leads_path = tmp_path / "leads.jsonl"
        leads_path.write_text(
            '{"nome": "Hotel OK", "perfil": "@ok", "temperatura": "morno", '
            '"valor_potencial": 500, "status": "contato", "ultimo_contato": "2026-05-10"}\n'
            'LINHA_INVÁLIDA\n'
            '{"nome": "Hotel 2", "perfil": "@2", "temperatura": "frio", '
            '"valor_potencial": 350, "status": "novo", "ultimo_contato": "2026-04-01"}\n',
            encoding="utf-8",
        )
        engine = ContextEngine(data_dir=tmp_path)
        results = engine._fetch_leads(query="")

        # 2 válidos, 1 inválido ignorado
        assert len(results) == 2


# ---------------------------------------------------------------------------
# 6. Timeout de fonte lenta não trava o build() todo
# ---------------------------------------------------------------------------

class SlowContextEngine(ContextEngine):
    """Subclasse que injeta uma fonte lenta para testar timeout."""

    def _fetch_state_json(self, query: str):
        time.sleep(10)  # lento demais — deve ser abortado pelo timeout
        return super()._fetch_state_json(query)


class TestTimeout:
    def test_fonte_lenta_nao_trava_build(self, tmp_path, monkeypatch):
        """Verifica que o timeout por fonte funciona — sources_failed registra a falha.

        Nota: No Windows, threads já iniciadas não são interrompidas pelo Python;
        o executor.shutdown(wait=False) sinaliza para não esperar novas tarefas na fila,
        mas threads em execução completam naturalmente. O que importa é que:
        1) o Future.result() respeita o timeout e registra a falha corretamente
        2) o build() não bloqueia acima de timeout + margem de overhead razoável
        """
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        monkeypatch.delenv("AKASHA_DB_URL", raising=False)

        engine = SlowContextEngine(data_dir=tmp_path)

        start = time.monotonic()
        ctx = engine.build(query="")
        elapsed = time.monotonic() - start

        # O timeout é 5s. Build deve terminar em no máximo timeout + 3s de overhead
        # (inclui tempo de startup do executor + overhead do Windows scheduler)
        # A thread lenta (10s) deve ser sinalizada como falha dentro do timeout.
        assert elapsed < 9.0, f"build() demorou {elapsed:.1f}s, esperado < 9s"

        # O ponto crítico: state_json foi marcado como failed por timeout
        assert "state_json" in ctx.sources_failed


# ---------------------------------------------------------------------------
# 7. AuroraContext.sources_available lista só as que responderam
# ---------------------------------------------------------------------------

class TestSourcesAvailable:
    def test_apenas_fontes_que_responderam(self, tmp_path, monkeypatch):
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        monkeypatch.delenv("AKASHA_DB_URL", raising=False)
        _write_state(tmp_path, {"branch": "main"})
        # leads ausente — source "leads" deve estar em available (retorna [])
        engine = ContextEngine(data_dir=tmp_path)
        ctx = engine.build()

        # Ambas as fontes foram chamadas e retornaram sem erro
        assert "state_json" in ctx.sources_available
        assert "leads" in ctx.sources_available
        # Fontes opcionais não ativadas
        assert "notion" not in ctx.sources_available
        assert "akasha" not in ctx.sources_available
        # Nada em failed
        assert ctx.sources_failed == []


# ---------------------------------------------------------------------------
# 8. Anti-teatro: mudar state.json → resultados refletem
# ---------------------------------------------------------------------------

class TestAntiTeatro:
    def test_mudanca_no_state_reflete_nos_resultados(self, tmp_path, monkeypatch):
        monkeypatch.delenv("NOTION_TOKEN", raising=False)
        monkeypatch.delenv("AKASHA_DB_URL", raising=False)

        _write_state(tmp_path, {"branch": "feature/A", "test_count": 100})
        engine = ContextEngine(data_dir=tmp_path)

        ctx1 = engine.build(query="")
        state_results1 = [r for r in ctx1.results if r.source == "state_json"]
        assert "feature/A" in state_results1[0].content
        assert "100" in state_results1[0].content

        # Muda o state.json
        _write_state(tmp_path, {"branch": "feature/B", "test_count": 9999})

        ctx2 = engine.build(query="")
        state_results2 = [r for r in ctx2.results if r.source == "state_json"]
        assert "feature/B" in state_results2[0].content
        assert "9999" in state_results2[0].content
        # Não carrega dados velhos
        assert "feature/A" not in state_results2[0].content
