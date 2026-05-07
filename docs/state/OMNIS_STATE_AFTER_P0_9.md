# OMNIS STATE — AFTER P0.9

**Data:** 2026-05-07
**Branch:** master
**Commit:** 11af560

## Testes

- **606 passed, 1 skipped, 0 failures** (7min08s)
- Cobertura: missions, pipeline, tool_registry, metrics, creative, captions, queue, disk, video, skills

## Módulos existentes

| Módulo | Status | Descrição |
|---|---|---|
| `src/missions/` | P0.5-P0.7 | MissionContract, TaskState, EventEnvelope, JsonlRepository, runtime |
| `src/pipeline_local/` | P0.6 | Mission-aware pipeline orchestrator + PipelineLocalService |
| `src/tool_registry/` | P0.8 | 19 ferramentas catalogadas, discovery read-only, JSONL |
| `src/metrics/` | P0.9 | MetricsRecorder, RunSummary, MetricEvent, JSONL |
| `src/observability/` | Pre-P0 | LocalTracer, record_metric, StructuredFormatter |
| `src/cli_commands/` | — | 9 arquivos CLI modulares (missions, tools, metrics, pipeline, creative, publisher, forge, argos, captions) |
| `src/caption_approval/` | Fase 2C | DraftsManager, ApprovalGate, TemplateLibrary |

## Linha do tempo P0

| Fase | Commit | Entregue |
|---|---|---|
| P0.5 — Mission Contract + TaskState | `cc3b09e` | ✅ |
| P0.6 — Mission-Aware Pipeline | `8bc8e20` | ✅ |
| P0.7 — Durable Mission Runtime | `cbffe14` | ✅ |
| P0.8 — Tool Registry | `444fccb` | ✅ |
| P0.9 — Metrics Spine | `11af560` | ✅ |

## Limitações conhecidas

- OAuth Meta bloqueado — Instagram Graph API sem token
- 2 containers Docker unhealthy (crm-tigre-backend, jarvis_frontend)
- Disco C:\ com 8.6% livre (79GB)
- Qdrant inacessível (porta fechada)
- Publisher OS sem porta 8000 aberta
- Capability Forge ainda proposal-only
- LangGraph não implementado
- JSONL sem locking concorrente

## CLI principal

```bash
python jarvis.py status / doctor / briefing
python jarvis.py mission create / list / show / pause / resume / retry / checkpoint
python jarvis.py pipeline mission-run / mission-status
python jarvis.py tools discover / list / show / status / update-status
python jarvis.py metrics status / today / mission / tools / export
```

## Próxima fase

**NÃO INICIADA.** P0.9.1 Structural Integrity Gate em andamento.
Após: P1.0 DISK-1 seguro → P1.1 OAuth Meta → P1.2 1 post real.
