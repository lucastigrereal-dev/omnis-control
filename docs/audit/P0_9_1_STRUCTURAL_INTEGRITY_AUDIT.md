# P0.9.1 STRUCTURAL INTEGRITY AUDIT

**Data:** 2026-05-07
**Objetivo:** Verificar integridade da fundação P0.5-P0.9 antes de avançar para DISK-1/OAuth.

---

## 1. Arquitetura — Duplicações

### Pipeline result models (ATTENTION)

`src/pipeline_local/models.py` e `src/pipeline_local/mission_models.py` definem tipos paralelos:
- `PipelineRunResult` (dataclass) vs `MissionPipelineResult` (Pydantic v2)
- Cada um com seu próprio `*Status` e `*BlockReason`
- `MissionPipelineResult` é um superset funcional — o outro pode ser consolidado

**Recomendação:** Consolidar em P1.0, sem pressa. Não quebra nada agora.

### Dual metric writers (ATTENTION)

`src/observability/tracer_local.py` (record_metric) e `src/metrics/recorder.py` (MetricsRecorder.record_metric) escrevem em `data/metrics/` com schemas diferentes:
- tracer_local → `data/metrics/YYYYMMDD.jsonl` (particionado por data)
- metrics → `data/metrics_spine/metrics.jsonl` (arquivo único)

Na prática, NÃO colidem mais (metrics_spine vs metrics). Mas a confusão de nomes é real.

**Recomendação:** Documentar a distinção. metrics_spine = missão/pipeline. metrics/ = app-level genérico.

### jarvis.py == omnis.py (LOW)

Ambos importam `from src.cli import app` e chamam `app()`. São duplicatas idênticas.

**Recomendação:** Remover `omnis.py` ou documentar como alias.

---

## 2. Acoplamento — Dependency Graph

```
cli.py → cli_commands/* → pipeline_local, missions, metrics, tool_registry
pipeline_local/mission_pipeline.py → missions, tool_registry, metrics
missions/runtime.py → metrics (quick_record_metric)
tool_registry/__init__.py → metrics (lazy import)
observability/ → self-contained (usado só por pipeline_local/service.py)
```

| Dependência | Classificação |
|---|---|
| mission_pipeline → tool_registry | Saudável (verificação leve) |
| mission_pipeline → metrics | Saudável (start_run/finish_run) |
| runtime → metrics | Saudável (quick_record_metric) |
| tool_registry → metrics | Saudável (lazy import, sem ciclo) |
| metrics → qualquer outro | Nenhuma (só importado, nunca importa) |

**Zero circular imports. Grafo limpo e descendente.**

---

## 3. CLI

### src/cli.py: 2.001 linhas, 18 add_typer calls

Bom: 9 apps extraídos para `src/cli_commands/` (missions, tools, metrics, pipeline, creative, publisher, forge, argos, captions).
Ruim: ~10 apps ainda inline (sales, memory, llm, video-assets, accounts, queue, captions, approvals, templates, workflow).

**Tendência:** Crescimento linear com novas fases. Se P1.x+ adicionar mais apps, cli.py passa de 3.000 linhas.

### Comandos novos (P0.5-P0.9)

| Comando | Arquivo | OK? |
|---|---|---|
| mission * | missions_cmd.py | ✅ |
| pipeline mission-* | pipeline_cmd.py | ✅ |
| tools * | tools_cmd.py | ✅ |
| metrics * | metrics_cmd.py | ✅ |

### Error handling

```bash
python jarvis.py pipeline mission-status nonexistent_id  # → "Mission nao encontrada" ✅
python jarvis.py mission resume nonexistent_id           # → exit 1, sem traceback ✅
python jarvis.py metrics mission nonexistent_id           # → "Nenhuma run encontrada" ✅
```

Todos os edge cases tratados com graceful errors.

---

## 4. Storage

### JSONL stores mapeadas (17)

| Local | Arquivos | Gitignored? |
|---|---|---|
| data/ root | accounts, content_queue, approval_log, caption_drafts, workflow_results, creative_briefs, pipeline_runs | ✅ data/*.jsonl |
| data/metrics_spine/ | metrics.jsonl, runs.jsonl | ✅ explícito |
| data/missions/ | index.jsonl | ✅ explícito |
| data/metrics/ | YYYYMMDD.jsonl | ✅ data/metrics/ |
| data/traces/ | YYYYMMDD.jsonl | ✅ data/traces/ |
| data/publisher_store/ | content_items.jsonl | ✅ data/publisher_store/ |
| logs/ | health_scores, tool_runs, missions | ✅ logs/*.jsonl |

**Nenhum .jsonl de runtime commitado.** Só .gitkeep files estão no git.

### .gitkeep preservados

6 arquivos: metrics_spine, missions/contracts, missions/events, pipeline_runs, tool_registry, inbox/videos. Todos OK.

---

## 5. Eventos e Métricas

### EventEnvelope — Consistente

27 EventTypes no Literal. 13 efetivamente emitidos por runtime.py + mission_pipeline.py. Todos batem com o tipo declarado. Os 14 restantes são forward-looking (tool_invoked, skill_invoked, plan_drafted, etc.) — design intencional.

### Métricas — Sem duplicação de eventos críticos

MetricsRecorder emite eventos SEPARADOS dos eventos de missão. EventEnvelope é o source of truth da missão. MetricEvent é observação passiva. Não competem.

### Métricas — Orphan runs (LOW)

Testes chamam `start_run()` (cria run status=running) mas early returns do pipeline (MISSION_NOT_FOUND, MISSION_PAUSED, CAPTION_NOT_SUBMITTED, etc.) não chamam `finish_run()`. Resultado: 20 runs "running" órfãs nos dados de hoje.

**Recomendação:** Adicionar `finish_run()` nos early returns em P1.0. Não quebra nada agora.

---

## 6. Segurança

| Check | Resultado |
|---|---|
| Segredos hardcoded em src/ | ✅ Nenhum |
| .env lido por módulos novos | ✅ Nenhum |
| API externa chamada por P0.5-P0.9 | ✅ Nenhuma |
| Docker alterado | ✅ Não |
| OAuth executado | ✅ Não |
| Secret detection ativo no ToolRegistry | ✅ Ativo (6 regex patterns) |

---

## Veredito

| Área | Nota |
|---|---|
| Duplicações | ATTENTION — 2 issues não-críticos |
| Acoplamento | HEALTHY — zero ciclos |
| CLI | ATTENTION — crescimento monitorado |
| Storage | HEALTHY — tudo gitignored |
| Eventos | HEALTHY — consistentes |
| Segurança | HEALTHY — zero violações |

**Conclusão:** Nenhum erro estrutural crítico. Issues encontrados são de organização/consolidação, não de integridade. Sistema apto para avançar.
