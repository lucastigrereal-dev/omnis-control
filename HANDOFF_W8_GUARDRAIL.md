# HANDOFF W8 — Guardrail no Grafo

**Wave:** D1-W8  
**Commit:** 22a9f80  
**Branch:** feature/omnis-5waves-runtime-supreme  
**Status:** COMPLETO ✅

## O que foi feito

### Arquivos modificados
- `src/mission_graph/mission_state.py` — campo `action: str` (default `"execute_step"`) adicionado ao `MissionGraphState` e ao `initial_state()`
- `src/mission_graph/nodes/execute_node.py` — guardrail check antes da execução; `route_after_execute` passa direto para `fail` quando `status=failed` (evita loop de retry)
- `src/mission_graph/runner.py` — parâmetro `action: str = "execute_step"` em `run_mission_graph()`

### Arquivo criado
- `tests/mission_graph/test_guardrail.py` — 16 testes divididos em 3 classes

## Comportamento implementado

`execute_node` chama `AuroraGuardrail().check(action)` antes de executar:

| Ação | Veredicto | Motivo |
|------|-----------|--------|
| `execute_step` | ALLOWED | Nenhuma regra dispara |
| `publicar` | BLOCKED | Regra `external_publish` |
| `deploy` | BLOCKED | Regra `git_push_deploy` |
| `git push` | BLOCKED | Regra `git_push_deploy` |
| `deletar` | ALLOWED | Sem regra específica no guardrail atual |
| GuardrailError | Passa | Graceful degradation |

## Testes

```
86 passed, 0 failed (mission_graph/)
296 passed, 0 failed (agencia/ + publisher/)
```

## Próxima wave sugerida
- W9: Persist guardrail audit log (registrar bloqueios em JSONL)
- W9: Adicionar regra `deletar` no guardrail se necessário
