# HANDOFF D1 — mission_graph scaffold mínimo

**Branch:** feature/omnis-5waves-runtime-supreme  
**Commit:** 84b25d6  
**Data:** 2026-05-26  

---

## Versão LangGraph

- **langgraph:** 1.2.0  
- **langchain-core:** 1.4.0  

---

## Arquivos criados

| Arquivo | Descrição |
|---|---|
| `src/mission_graph/__init__.py` | Marcador do módulo D1 |
| `src/mission_graph/mission_state.py` | `MissionGraphState` TypedDict + helpers |
| `src/mission_graph/mission_graph.py` | StateGraph skeleton com 4 nós + arestas condicionais |
| `src/mission_graph/runner.py` | API pública opt-in (`use_langgraph=False` por default) |
| `tests/mission_graph/__init__.py` | Package marker |
| `tests/mission_graph/conftest.py` | Stub `sys.modules` para `langchain_core.messages.utils` |
| `tests/mission_graph/test_mission_state.py` | 6 testes de estado |
| `tests/mission_graph/test_retry_flow.py` | 4 testes de fluxo/retry |
| `tests/mission_graph/test_checkpoint_resume.py` | 3 testes de checkpoint/resume |

---

## Testes passando

```
tests/mission_graph/ — 13/13 passed (0.30s)
tests/agencia/ + tests/publisher/ — 296/296 passed (non-regression)
```

---

## Desvios do spec + justificativas

### 1. `checkpoint_id` → `run_checkpoint_id`
**Motivo:** `checkpoint_id` é canal reservado em LangGraph 1.2.0 (`RESERVED` set em `langgraph.pregel._validate`). Usar o nome original causava `ValueError: Channel name 'checkpoint_id' is reserved` ao compilar o grafo.  
**Ação:** Campo renomeado para `run_checkpoint_id` em `MissionGraphState`, `_checkpoint_node`, `runner.py` e testes.

### 2. `validate` usa aresta condicional, não direta
**Motivo:** Com aresta direta `validate → execute`, um `mission_id=""` entrava em loop infinito (execute retorna imediatamente sem erro, sempre vai para checkpoint). O `_validate_node` retorna `error` no estado, mas o fluxo não checava isso antes de executar.  
**Ação:** Adicionado `_route_after_validate()` — se `state["error"]` existe após validate, rota para `finalize` diretamente.

### 3. Imports LangGraph são lazy (call-time)
**Motivo:** `langgraph.graph.__init__` importa `MessageGraph` de `langgraph.graph.message`, que por sua vez importa `AnyMessage` etc. via lazy `__getattr__` de `langchain_core.messages.__init__`. Esse `__getattr__` tenta carregar `langchain_core.messages.utils` — módulo que **não existe** em langchain-core 1.4.0.  
**Ação:** `from langgraph.graph import StateGraph, END` movido para dentro de `build_mission_graph()` e das funções de `runner.py`. O `conftest.py` injeta um stub em `sys.modules['langchain_core.messages.utils']` antes da coleta dos testes, resolvendo o problema sem modificar pacotes instalados.

---

## Próximos passos (D1.2+)

1. **`src/mission_graph/nodes/`** — nós reais (validate, execute, checkpoint, finalize) extraídos para módulos separados com injeção de dependências
2. **`src/mission_graph/checkpoint_store.py`** — integração real com `JsonlRepository.save_checkpoint()` e `get_latest_checkpoint()` em `_checkpoint_node`
3. **`src/mission_graph/retry_policy.py`** — `RetryPolicy` configurável (backoff, max_retries por nó, jitter)
4. **Thread-safe LangGraph checkpointer** — `MemorySaver` ou `AsyncSqliteSaver` para `graph.compile(checkpointer=...)`
5. **Evento emit** — `_checkpoint_node` deve chamar `JsonlRepository.append_event(EventEnvelope(...))` para integração com o pipeline de eventos existente
