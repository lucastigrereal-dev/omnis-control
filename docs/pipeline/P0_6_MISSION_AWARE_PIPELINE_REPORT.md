# P0.6 MISSION-AWARE PIPELINE — RELATÓRIO DE IMPLEMENTAÇÃO

**Data:** 2026-05-07
**Autor:** Claude Opus 4.7

## Resultado

| Métrica | Valor |
|---|---|
| Testes totais | 487 passed, 1 skipped, 0 warnings |
| Testes novos (P0.6) | 17 |
| Regressões | 0 |
| Arquivos criados | 5 |
| Arquivos modificados | 2 |
| Linhas novas | ~650 |

## Arquivos criados

| Arquivo | Linhas | Descrição |
|---|---|---|
| `src/pipeline_local/mission_models.py` | 100 | MissionPipelineResult + status/block constants |
| `src/pipeline_local/mission_pipeline.py` | 260 | Orquestrador magro + status helper |
| `tests/pipeline/__init__.py` | 0 | Package init |
| `tests/pipeline/test_mission_aware_pipeline.py` | 195 | 17 testes |

## Arquivos modificados

| Arquivo | Mudança |
|---|---|
| `src/cli_commands/pipeline_cmd.py` | +140 linhas — mission-run e mission-status |
| `.gitignore` | +2 linhas — data/pipeline_runs |

## Padrões implementados

- Orquestrador magro (delega, não reimplementa)
- Pydantic para modelos de fronteira
- Rich + --json consistente
- Injeção de repositório com default
- Eventos append-only imediatos
- Idempotência por TaskState
- Prefix matching nos comandos mission-status

## Decisões aplicadas

- `error_logged` (não `error_raised`) — consistente com EventType
- `QUEUE_CONTEXT_REQUIRED` para ausência de queue/caption
- Caption `rejected` → BLOCKED (não mission_cancelled)
- Caption `revised` → mesmo tratamento que `needs_review`
- Warnings não bloqueiam pipeline
- Disco crítico não bloqueia P0.6
