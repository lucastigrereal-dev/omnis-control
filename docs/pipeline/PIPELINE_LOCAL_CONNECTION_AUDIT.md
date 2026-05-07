# Pipeline Local — Connection Audit

**Data:** 2026-05-06
**Objetivo:** Mapear pontos de conexão entre módulos OMNIS para pipeline dry-run local.

---

## Módulos Existentes

| Módulo | Store | Classe/Entry Point | Status |
|--------|-------|-------------------|--------|
| Content Queue | `data/content_queue.jsonl` | `Queue()` / `QueueItem` | Operacional |
| Caption Approval | `data/caption_drafts.jsonl` | `DraftsManager()` / `CaptionDraft` | Operacional |
| Creative Briefs | `data/creative_briefs.jsonl` | `create_brief()` / `CreativeBrief` | Operacional |
| Creative Export | `data/exports/creative_packages/` | `generate_export_package()` | Operacional |
| Publisher Local | `data/publisher_store/` | `PublishPipeline()` / `JsonLStore` | Operacional |
| Observability | `data/traces/` + `data/metrics/` | `LocalTracer` / `record_metric()` | Operacional |
| Workflow Engine | `data/workflow_results.jsonl` | `WorkflowEngine.run()` | Operacional (via CrewAI) |

## Conexões-Chave

### 1. Queue → Caption
- `QueueItem.queue_id` → `CaptionDraft.queue_id` 
- `DraftsManager.get_by_queue_id(queue_id)` já existe
- Precisamos de: `status == "approved"` para prosseguir
- **Store:** `data/caption_drafts.jsonl` (JSONL append-only)

### 2. Caption → Creative Brief
- `creative_production/briefs.py:create_brief()` aceita `caption_draft_id`, `queue_id`, `account_handle`, `format`, `objective`
- Já valida se caption existe e está aprovada
- Gera warnings: `CAPTION_NOT_APPROVED`, `QUEUE_NOT_FOUND`
- **Store:** `data/creative_briefs.jsonl`

### 3. Creative Brief → Export Package
- `creative_production/exporter.py:generate_export_package(brief_id)` 
- Gera até 13 artefatos em `data/exports/creative_packages/`
- Retorna `ExportPackageResult` com `package_path`, `files_generated`, `warnings`
- **Store:** `data/exports/creative_packages/brief_{id}_{ts}/`

### 4. Export → Publisher Local
- `publisher/pipeline.py:PublishPipeline` usa `JsonLStore` em `data/publisher_store/`
- Aceita caption + hashtags + format para `stage_publish()`
- MetaAPIDryRun persiste em `data/dryrun_publishes/`
- **Store:** `data/publisher_store/content_items.jsonl`

### 5. Publisher → Observabilidade
- `observability/tracer_local.py:get_tracer().start_as_current_span()`
- `observability/tracer_local.py:record_metric()`
- Sem dependências externas
- **Store:** `data/traces/` + `data/metrics/`

## Caminho Mínimo para Conectar

```
Queue.get(queue_id)
  → DraftsManager.get_by_queue_id(queue_id) [status=approved]
    → create_brief(queue_id, account_handle, format, objective, caption_draft_id)
      → generate_export_package(brief_id)
        → PublishPipeline.stage_publish(ctx) [via MetaAPIDryRun]
          → LocalTracer span + record_metric
```

## Riscos de Acoplamento

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| QueueItem sem caption aprovada | Pipeline bloqueado | Retornar status=blocked + warning CAPTION_NOT_APPROVED |
| Brief já existe para queue_id | Duplicata | Reutilizar brief existente |
| Export package já existe | Duplicata em disco | Gerar novo package_id sempre (timestamp) |
| Publisher Local espera MetaAPIDryRun | Sempre dry-run (intencional) | MetaAPIDryRun não tem side effects |
| JSONL sem lock concorrente | Race condition | Pipeline sequential local (sem concorrência) |

## Comandos CLI Existentes

| Comando | Módulo |
|---------|--------|
| `omnis queue list` | Content Queue |
| `omnis approvals pending` | Caption Approval |
| `omnis captions create` | Caption Approval |
| `omnis workflow run` | Workflow Engine |
| `omnis publisher create` | Publisher Local |
| `omnis pipeline dry-run` | **NOVO (P0.4)** |

## Decisão

Pipeline local novo em `src/pipeline_local/` — não acoplar ao `WorkflowEngine` existente (que depende de CrewAI/Publisher OS externo). Este novo módulo é **offline-first, dry-run apenas, sem chamadas externas**.
