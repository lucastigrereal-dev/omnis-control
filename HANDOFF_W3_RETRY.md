# HANDOFF Wave 3 — retry_policy configurável por nó

**Commit:** `3e3ac1a`
**Branch:** `feature/omnis-5waves-runtime-supreme`
**Data:** 2026-05-26
**Status:** VERDE ✅

---

## O que foi feito

### Arquivos criados
- `src/mission_graph/retry_policy.py` — `NodeRetryConfig` + `RetryPolicy` com suporte a config por nó, `default_policy()` e `strict()`
- `tests/mission_graph/test_retry_policy.py` — 5 testes cobrindo default, strict, node-specific, within-limit, at-limit

### Arquivos modificados
- `src/mission_graph/mission_state.py` — `should_retry()` aceita `policy: Optional[RetryPolicy]` (backward-compat total)
- `src/mission_graph/nodes/execute_node.py` — `execute_node()` registra tentativa via `record_attempt()` quando `state["error"]` está setado
- `tests/mission_graph/test_retry_flow.py` — adicionado `test_nodo_falha_duas_vezes_passa_na_terceira`

## Gates passados
- `tests/mission_graph/` → **39/39 passed**
- `tests/agencia/ tests/publisher/` → **296 passed**

## Decisões de design
- `RetryPolicy` é agnóstico ao estado — recebe apenas `(node, attempts)`, sem dependência circular
- `should_retry()` em `mission_state.py` permanece backward-compat: sem `policy` usa `state["max_retries"]`
- `execute_node` usa import local para evitar ciclo de importação
- Extensibilidade futura: `NodeRetryConfig` tem slot para `backoff_s`, `jitter`, `retry_on_exceptions`

## Próxima wave sugerida
Wave 4 — `write-tests` + `fix-tests`: ampliar cobertura de `execute_node` com cenários de retry ponta a ponta via grafo.
