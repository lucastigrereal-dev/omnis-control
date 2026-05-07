# Pipeline Local Dry-Run — OMNIS P0.4

**Data:** 2026-05-06
**Objetivo:** Conectar módulos existentes em pipeline local rastreável, sem publicar nada.

---

## Fluxo Ponta a Ponta

```
Queue Item (Content Queue)
  │
  ▼
Caption Aprovada? (Caption Approval)
  │  └─ BLOCKED se não existir ou não aprovada
  ▼
Creative Brief (Creative Production)
  │  └─ Reusa brief existente ou cria novo
  ▼
Export Package (Creative Exporter)
  │  └─ Gera 13 artefatos em data/exports/creative_packages/
  ▼
Publisher Local Entry (Publisher Local Dry-Run)
  │  └─ Cria content_item no JsonLStore
  ▼
Métrica + Trace (Observabilidade Local)
  │  └─ data/traces/ + data/metrics/
  ▼
Relatório (PipelineRunResult)
```

## Módulos Conectados

| Módulo | Store | Papel |
|--------|-------|-------|
| `src/content_queue/` | `data/content_queue.jsonl` | Fonte do item |
| `src/caption_approval/` | `data/caption_drafts.jsonl` | Caption aprovada |
| `src/creative_production/` | `data/creative_briefs.jsonl` | Brief + Export |
| `src/publisher/` | `data/publisher_store/` | Publisher local |
| `src/observability/` | `data/traces/` + `data/metrics/` | Span + métrica |
| `src/pipeline_local/` | `data/pipeline_runs.jsonl` | Resultado do run |

## Comandos

```bash
# Executar pipeline dry-run para um queue item
python omnis.py pipeline dry-run <queue-id>

# Ver histórico de execuções
python omnis.py pipeline status
```

## Artefatos Gerados

Após `pipeline dry-run`:
- `data/pipeline_runs.jsonl` — resultado estruturado de cada run
- `data/exports/creative_packages/brief_{id}_{ts}/` — até 13 arquivos de export
- `data/publisher_store/content_items.jsonl` — entrada no publisher local
- `data/traces/<YYYYMMDD>.jsonl` — span do tracer
- `data/metrics/<YYYYMMDD>.jsonl` — métrica de duração

## Bloqueios Conhecidos

| Condição | Status | Ação |
|----------|--------|------|
| Queue item não existe | BLOCKED | Verificar ID na fila |
| Caption não aprovada | BLOCKED | `omnis approvals pending` + approve |
| Export package com warnings | SUCCESS_WITH_WARNINGS | Revisar WARNINGS.md |
| Nenhum dos módulos falha | SUCCESS | Pipeline completo |

## O que NÃO foi feito (intencionalmente)

- Nenhuma chamada a API externa (Meta, Google, Instagram)
- Nenhum OAuth
- Nenhuma publicação real
- Nenhuma alteração em Docker
- Nenhuma dependência nova
- Nenhum push para git
- Nenhum LangGraph, OpenHands, build_skill()
- Nenhuma migração de JSONL para Postgres
- Nenhuma refatoração do cli.py existente

## Próximo Passo Recomendado

1. Popular a Content Queue com `omnis queue generate --apply`
2. Criar captions com `omnis captions create`
3. Aprovar com `omnis approvals approve`
4. Executar `omnis pipeline dry-run <queue-id>`
5. Verificar artefatos em `data/exports/creative_packages/`
