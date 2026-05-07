# P0.7 — DURABLE MISSION RUNTIME

**Data:** 2026-05-07
**Commit base:** `8bc8e20` (P0.6)

## Conceito

Estende o Mission Core existente (`src/missions/`) com capacidades de checkpoint, pausa, resume e retry — o "crachá, GPS e ponto eletrônico" da missão. Sempre soube executar. Agora sabe parar, voltar e recomeçar de onde estava.

## Fluxo

```
MissionContract (P0.5)
    ↓
MissionPipeline (P0.6) — orquestrador
    ↓
Durable Runtime (P0.7) — checkpoint / pause / resume / retry
    ↓
EventEnvelope emitidos em cada operação de runtime
    ↓
TaskState atualizado com evidências + contexto de resume
```

## Estados e transições

```
DRAFT → RUNNING ⇄ PAUSED
  ↓         ↓
  ✕    WAITING_APPROVAL
         ↓
       RUNNING → COMPLETED
         ↓
       FAILED → RUNNING (retry, se max_retries > retry_count)
```

## Arquivos

| Arquivo | Papel | Status |
|---|---|---|
| `src/missions/events.py` | +2 event types (checkpoint_created, evidence_recorded) | MODIFICADO |
| `src/missions/state.py` | +5 campos no TaskState | MODIFICADO |
| `src/missions/repository.py` | +3 métodos de checkpoint no ABC + JsonlRepository | MODIFICADO |
| `src/missions/runtime.py` | 5 funções core (checkpoint, pause, resume, retry, resume-context) | CRIADO |
| `src/pipeline_local/mission_models.py` | +1 block reason (MISSION_PAUSED) | MODIFICADO |
| `src/pipeline_local/mission_pipeline.py` | Integração com runtime (checkpoint + PAUSED handling) | MODIFICADO |
| `src/cli_commands/missions_cmd.py` | 5 novos comandos CLI | MODIFICADO |

## Funções Runtime

### checkpoint_mission(mission_id, repo, label)
Cria snapshot do estado atual. Emite `checkpoint_created` + salva em `data/missions/checkpoints/{mission_id}/{checkpoint_id}.json`.

### pause_mission(mission_id, reason, repo)
Pausa missão em RUNNING/WAITING_APPROVAL. Auto-checkpoint antes de pausar. Emite `mission_paused`.

### resume_mission(mission_id, repo)
Resume de PAUSED → RUNNING. Retorna resume_context do último checkpoint. Emite `mission_resumed`.

### retry_mission(mission_id, repo)
Retenta de FAILED → RUNNING. Bloqueia se `retry_count >= max_retries`. Emite `retry_attempted` + `mission_resumed`.

### get_resume_context(mission_id, repo)
Retorna diagnóstico completo: status, resumable?, current_step, completed_steps, artifacts, budget, erros.

## Comandos CLI

```bash
python jarvis.py mission pause <mission_id> [--reason "..."]
python jarvis.py mission resume <mission_id>
python jarvis.py mission retry <mission_id>
python jarvis.py mission checkpoint <mission_id> [--label "..."]
python jarvis.py mission resume-context <mission_id>
```

Todos aceitam `--json` para output estruturado.

## Idempotência e segurança

| Operação | Guard |
|---|---|
| checkpoint | Sempre permitido (cada chamada = novo checkpoint) |
| pause | `assert_transition(current, PAUSED)` — bloqueia se completed/failed |
| resume | `assert_transition(current, RUNNING)` de PAUSED |
| retry | Só de FAILED + `retry_count < max_retries` |
| mission-run com PAUSED | Bloqueado com MISSION_PAUSED + sugestão de resume |

## Limitações (P0.7)

- **Sem retry automático**: retry é manual via CLI (auto-retry é P0.9+)
- **Sem file lock cross-platform**: TODO, ainda usa append-only como safety
- **max_retries fixo em 3**: não lê do MissionContract (campo não existe no contrato)
- **Sem garbage collection de checkpoints antigos**: MVP acumula todos

## Próximo passo

**P0.8 — Metrics Spine** ou **P0.9 — Auto-Retry + Dead Letter Queue**
