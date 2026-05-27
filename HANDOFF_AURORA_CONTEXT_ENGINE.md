# HANDOFF — Aurora ContextEngine (Camada 1)

**Frente 3 concluída.** Branch: `feature/omnis-5waves-runtime-supreme`
Commit: `b090399` — `feat(aurora): Camada 1 — ContextEngine unifica state.json + leads + stubs Notion/Akasha`

---

## O que foi construído

### `src/aurora/context_engine.py`
Módulo de unificação de contexto da Aurora. Expõe:

| Classe | Responsabilidade |
|--------|-----------------|
| `ContextResult` | Resultado de uma fonte: `source`, `content`, `relevance`, `metadata` |
| `AuroraContext` | Agregado: `results`, `sources_available`, `sources_failed`, `query`, `built_at` |
| `ContextEngine` | Orquestrador — chama todas as fontes em paralelo, degrada graciosamente |

**Comportamento:**
- `build(query, max_results_per_source)` → ThreadPoolExecutor, timeout 5s por fonte
- Fontes sempre ativas: `state_json` (data/state.json) e `leads` (data/leads.jsonl)
- Fontes opcionais: `notion` (só se `NOTION_TOKEN` no env), `akasha` (só se `AKASHA_DB_URL` no env)
- Falha de fonte → entra em `sources_failed`, nunca crasha o `build()`
- `executor.shutdown(wait=False, cancel_futures=True)` — não bloqueia o caller em threads lentas

### `src/aurora/thinker.py` (modificado)
- Import de `ContextEngine` adicionado
- `_load_data()` tem nova fonte 5:
  ```python
  engine = ContextEngine(data_dir=self.data_dir)
  ctx = engine.build(query="leads hoteis publicidade receita")
  snapshot["context_results"] = ctx.results
  snapshot["context_sources"] = ctx.sources_available
  snapshot["context_failed"] = ctx.sources_failed
  ```
- `_build_prompt()` adiciona seção "CONTEXTO EXTERNO (Notion/Akasha)" quando há resultados de fontes além de `state_json`/`leads` — máximo 5 itens, 200 chars cada

### `tests/aurora/test_context_engine.py`
17 testes cobrindo todos os cenários exigidos.

---

## Saída crua dos testes

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.2, pluggy-1.6.0
collected 26 items

tests/aurora/test_context_engine.py::TestBuildSemFontesExternas::test_retorna_aurora_context PASSED [  3%]
tests/aurora/test_context_engine.py::TestBuildSemFontesExternas::test_state_json_em_sources_available PASSED [  7%]
tests/aurora/test_context_engine.py::TestBuildSemFontesExternas::test_leads_em_sources_available PASSED [ 11%]
tests/aurora/test_context_engine.py::TestNotionAusente::test_notion_token_ausente_nao_crasha PASSED [ 15%]
tests/aurora/test_context_engine.py::TestNotionAusente::test_notion_token_presente_ativa_fonte PASSED [ 19%]
tests/aurora/test_context_engine.py::TestAkashaAusente::test_akasha_url_ausente_nao_crasha PASSED [ 23%]
tests/aurora/test_context_engine.py::TestAkashaAusente::test_akasha_url_presente_ativa_fonte PASSED [ 26%]
tests/aurora/test_context_engine.py::TestFetchStateJson::test_le_chaves_do_state PASSED [ 30%]
tests/aurora/test_context_engine.py::TestFetchStateJson::test_state_ausente_retorna_lista_vazia PASSED [ 34%]
tests/aurora/test_context_engine.py::TestFetchStateJson::test_state_corrompido_retorna_lista_vazia PASSED [ 38%]
tests/aurora/test_context_engine.py::TestFetchLeads::test_le_leads_do_jsonl PASSED [ 42%]
tests/aurora/test_context_engine.py::TestFetchLeads::test_lead_quente_tem_relevancia_maxima PASSED [ 46%]
tests/aurora/test_context_engine.py::TestFetchLeads::test_leads_ausente_retorna_lista_vazia PASSED [ 50%]
tests/aurora/test_context_engine.py::TestFetchLeads::test_linha_invalida_ignorada_restante_ok PASSED [ 53%]
tests/aurora/test_context_engine.py::TestTimeout::test_fonte_lenta_nao_trava_build PASSED [ 57%]
tests/aurora/test_context_engine.py::TestSourcesAvailable::test_apenas_fontes_que_responderam PASSED [ 61%]
tests/aurora/test_context_engine.py::TestAntiTeatro::test_mudanca_no_state_reflete_nos_resultados PASSED [ 65%]
tests/aurora/test_thinker.py::TestWriteInsightToState::test_cria_state_se_ausente PASSED [ 69%]
tests/aurora/test_thinker.py::TestWriteInsightToState::test_merge_preserva_chaves_existentes PASSED [ 73%]
tests/aurora/test_thinker.py::TestWriteInsightToState::test_sobrescreve_apenas_chaves_aurora PASSED [ 76%]
tests/aurora/test_thinker.py::TestWriteInsightToState::test_state_corrompido_nao_quebra PASSED [ 80%]
tests/aurora/test_thinker.py::TestNoiseFilter::test_blocked_pending_approval_filtrado_no_sistema PASSED [ 84%]
tests/aurora/test_thinker.py::TestNoiseFilter::test_status_real_nao_e_filtrado PASSED [ 88%]
tests/aurora/test_thinker.py::TestLeadsSummary::test_sem_leads PASSED    [ 92%]
tests/aurora/test_thinker.py::TestLeadsSummary::test_com_leads_quentes PASSED [ 96%]
tests/aurora/test_thinker.py::TestLeadsSummary::test_leads_aparecem_no_prompt PASSED [100%]

============================= 26 passed in 5.15s ==============================
```

---

## Interface que Frente 1 (Notion) precisa implementar

**Arquivo:** `src/aurora/context_engine.py`
**Método:** `ContextEngine._fetch_notion(self, query: str, max_results: int) -> list[ContextResult]`

**Contrato:**
```python
def _fetch_notion(self, query: str, max_results: int) -> list[ContextResult]:
    import os
    # NOTION_TOKEN já está garantido no env (checado antes de chamar)
    token = os.environ["NOTION_TOKEN"]
    # ... chamar notion-client ou requests ...
    # Para cada resultado retornar:
    return [
        ContextResult(
            source="notion",
            content="<texto da página/bloco>",
            relevance=0.8,  # ou score da busca
            metadata={"page_id": "...", "url": "..."},
        )
    ]
    # Em caso de erro: retornar [] (nunca levantar exceção)
```

**Ativação:** basta setar `NOTION_TOKEN=<token>` no ambiente — o `build()` detecta automaticamente.

---

## Interface que Frente 2 (Akasha) precisa implementar

**Arquivo:** `src/aurora/context_engine.py`
**Método:** `ContextEngine._fetch_akasha(self, query: str, max_results: int) -> list[ContextResult]`

**Contrato:**
```python
def _fetch_akasha(self, query: str, max_results: int) -> list[ContextResult]:
    import os
    # AKASHA_DB_URL já está garantido no env (checado antes de chamar)
    db_url = os.environ["AKASHA_DB_URL"]
    # ... psycopg2 + pgvector embedding query ...
    # SELECT content, 1-(embedding <=> %s::vector) AS score
    #   FROM documents ORDER BY score DESC LIMIT %s
    # Para cada linha retornar:
    return [
        ContextResult(
            source="akasha",
            content=row["content"],
            relevance=float(row["score"]),
            metadata={"doc_id": row["id"], "chunk": row["chunk_index"]},
        )
    ]
    # Em caso de erro: retornar [] (nunca levantar exceção)
```

**Ativação:** basta setar `AKASHA_DB_URL=postgresql://...` no ambiente.

---

## Próximo passo por frente

| Frente | Ação |
|--------|------|
| Frente 1 (Notion) | Implementar `_fetch_notion()` com `notion-client` ou `requests`. Setar `NOTION_TOKEN`. Testes: `tests/aurora/test_notion_source.py` |
| Frente 2 (Akasha) | Implementar `_fetch_akasha()` com `psycopg2` + embedding do query via Ollama. Setar `AKASHA_DB_URL`. Testes: `tests/aurora/test_akasha_source.py` |
| Orquestrador | Após Frentes 1 e 2: nenhuma mudança na interface `build()` — só setar as vars de ambiente |
