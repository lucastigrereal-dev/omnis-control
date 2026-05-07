# P0.7 DURABLE MISSION RUNTIME — RELATÓRIO DE IMPLEMENTAÇÃO

**Data:** 2026-05-07
**Autor:** Claude Opus 4.7

## Resultado

| Métrica | Valor |
|---|---|
| Testes totais | 505 passed, 1 skipped, 0 warnings |
| Testes novos (P0.7) | 18 |
| Regressões | 0 |
| Arquivos criados | 3 |
| Arquivos modificados | 5 |
| Linhas novas | ~380 |

## Arquivos criados

| Arquivo | Linhas | Descrição |
|---|---|---|
| `src/missions/runtime.py` | 220 | 5 funções core do durable runtime |
| `tests/missions/test_durable_runtime.py` | 180 | 18 testes |
| `docs/pipeline/P0_7_DURABLE_MISSION_RUNTIME.md` | 90 | Documentação de arquitetura |

## Arquivos modificados

| Arquivo | Mudança |
|---|---|
| `src/missions/events.py` | +2 EventTypes (checkpoint_created, evidence_recorded) |
| `src/missions/state.py` | +5 campos TaskState + 2 match/case |
| `src/missions/repository.py` | +3 métodos abstratos + checkpoints_dir + 3 implementações |
| `src/pipeline_local/mission_models.py` | +1 block reason (MISSION_PAUSED) |
| `src/pipeline_local/mission_pipeline.py` | +checkpoint calls + PAUSED state handling |
| `src/cli_commands/missions_cmd.py` | +5 comandos CLI (~120 linhas) |

## Padrões implementados

- Estende existente (não cria módulo paralelo)
- Pydantic frozen para TaskState
- Repository pattern com ABC + JsonlRepository
- Event sourcing: toda operação runtime emite evento
- Auto-checkpoint antes de pause (snapshot safety net)
- Transition assertion antes de mudar estado
- Composite sort (created_at + checkpoint_id) para determinismo
- Rich + --json consistente nos 5 novos comandos
- Prefix matching via _resolve_id em todos os comandos

## Decisões aplicadas

- `src/missions/runtime.py` (não `src/task_state/`) — estende, não duplica
- `checkpoint_created` e `evidence_recorded` como EventTypes oficiais
- `max_retries` default 3 (não no contrato — P0.7 MVP)
- `get_latest_checkpoint` por `created_at` + `checkpoint_id` (não mtime — instável)
- PAUSED state bloqueia pipeline com sugestão explícita de resume
- `retry_count >= max_retries` → bloqueio irreversível (criar nova missão)
