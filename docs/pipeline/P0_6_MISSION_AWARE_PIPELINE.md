# P0.6 — MISSION-AWARE LOCAL PIPELINE

**Data:** 2026-05-07
**Commit base:** `cc3b09e` (P0.5)

## Conceito

Conecta o Mission Core (P0.5) ao pipeline local existente.
O pipeline já executava. Agora ele emite eventos de missão enquanto executa.

## Fluxo

```
MissionContract (P0.5)
    ↓
mission_pipeline.py (orquestrador magro)
    ↓
PipelineLocalService (existente, não alterado)
    ↓
Content Queue → Caption → Creative → Publisher Dry-Run
    ↓
EventEnvelope emitidos em cada etapa
    ↓
MissionPipelineResult + TaskState atualizado
```

## Arquivos

| Arquivo | Papel |
|---|---|
| `src/pipeline_local/mission_models.py` | MissionPipelineResult (Pydantic), status/block constants |
| `src/pipeline_local/mission_pipeline.py` | Orquestrador: run_mission_content_pipeline(), get_mission_pipeline_status() |
| `src/cli_commands/pipeline_cmd.py` | Comandos: pipeline mission-run, pipeline mission-status |

## Comandos CLI

```bash
python jarvis.py pipeline mission-run <mission_id>
python jarvis.py pipeline mission-run <mission_id> --queue-id <queue_id>
python jarvis.py pipeline mission-run <mission_id> --caption-draft-id <draft_id>
python jarvis.py pipeline mission-status <mission_id> [--json]
```

## Estados e eventos

### Fluxo bloqueado por aprovação
```
mission_started → approval_requested → waiting_approval
```

### Fluxo feliz
```
mission_started → step_started → artifact_produced → step_completed → mission_completed
```

### Fluxo de erro
```
error_logged → (mission_failed se irrecuperável)
```

## Idempotência

| Estado atual | Comportamento |
|---|---|
| `draft` | Inicia pipeline |
| `running` | Continua (delega ao PipelineLocalService) |
| `waiting_approval` | Reavalia se bloqueio foi resolvido |
| `completed` | No-op (MISSION_ALREADY_COMPLETED) |
| `failed` | Bloqueia reexecução |
| `cancelled` | Bloqueia reexecução |

## Limitações (P0.6)

- **Sem listener**: `waiting_approval` exige reexecução manual após aprovação
- **Sem criação automática de queue**: Precisa de queue_item ou caption_draft existente
- **Sem chamada de API externa**: Publisher é sempre dry-run
- **Sem medição de custo real**: delta_tokens/delta_cost_usd = 0 (módulos não informam)
- **Sem mission tree**: parent_mission_id é campo passivo
- **Sem file lock cross-platform**: TODO P0.7

## Próximo passo

**P0.7 — Tool Registry** ou **P0.8 — Metrics Spine**
