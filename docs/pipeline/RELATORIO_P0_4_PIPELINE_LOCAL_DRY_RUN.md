# P0.4 — Pipeline Local Dry-Run

**Data:** 2026-05-06
**Branch:** master
**Commit:** Pendente
**Testes Novos:** 12/12 PASS ✅
**Testes Total:** 358/358 ✅ (12 novos, 0 regressões)

---

## Resumo

Conexão offline-first entre 5 módulos existentes em um pipeline local rastreável:
**Content Queue → Caption Approval → Creative Production → Publisher Local → Observabilidade**

Sem chamadas externas, sem OAuth, sem publicação real.

## Arquivos Criados (7)

| Arquivo | Linhas | Propósito |
|---------|--------|-----------|
| `src/pipeline_local/__init__.py` | 2 | Package |
| `src/pipeline_local/models.py` | 83 | PipelineRunResult, status, block reasons |
| `src/pipeline_local/service.py` | 227 | Serviço principal com 5 stages |
| `src/pipeline_local/dry_run.py` | 30 | Wrapper de atalho |
| `src/cli_commands/pipeline_cmd.py` | 90 | CLI `pipeline dry-run` + `pipeline status` |
| `tests/test_pipeline_local_dry_run.py` | 231 | 12 testes |
| `docs/pipeline/PIPELINE_LOCAL_CONNECTION_AUDIT.md` | — | Auditoria de conexão |
| `docs/pipeline/PIPELINE_LOCAL_DRY_RUN.md` | — | Documentação do pipeline |
| `docs/pipeline/RELATORIO_P0_4_PIPELINE_LOCAL_DRY_RUN.md` | — | Este relatório |

## Arquivos Modificados (1)

| Arquivo | Mudança |
|---------|---------|
| `src/cli.py` | +1 import, +1 app.add_typer |

## Fluxo Implementado

```
PipelineLocalService.run_local_content_pipeline(queue_item_id)
  │
  ├── Stage 1: Load Queue Item (Content Queue)
  │   └── BLOCKED se não existir
  │
  ├── Stage 2: Find Approved Caption (Caption Approval)
  │   └── BLOCKED se não aprovada
  │
  ├── Stage 3: Create/Reuse Creative Brief (Creative Production)
  │
  ├── Stage 4: Generate Export Package (Creative Exporter)
  │   └─ 13 artefatos em data/exports/creative_packages/
  │
  ├── Stage 5: Publisher Local Entry (Publisher Local Dry-Run)
  │   └─ content_item em data/publisher_store/
  │
  ├── Observabilidade: span + métrica
  │
  └── Resultado estruturado (PipelineRunResult)
```

## Status: 3 níveis

| Status | Significado |
|--------|-------------|
| `success` | Pipeline completo sem warnings |
| `success_with_warnings` | Pipeline completo com warnings (ex: export parcial) |
| `blocked` | Impedido (queue não existe / caption não aprovada) |
| `failed` | Erro não esperado |

## Testes (12)

- `test_defaults` — PipelineRunResult com valores padrão
- `test_to_dict_roundtrip` — Serialização/deserialização
- `test_timestamps_auto` — Timestamps gerados automaticamente
- `test_blocked_when_queue_item_not_found` — BLOCKED se queue não existe
- `test_blocked_when_caption_not_approved` — BLOCKED se caption não aprovada
- `test_full_dry_run_with_approved_caption` — Pipeline completo com dados mínimos
- `test_registers_metric_and_trace` — Métrica + trace registrados
- `test_persists_run_result` — Resultado salvo em JSONL
- `test_dry_run_does_not_crash` — Wrapper não quebra com ID inexistente
- `test_dry_run_returns_result_object` — Wrapper sempre retorna objeto
- `test_cli_dry_run_help` — Comandos CLI registrados
- `test_integration_via_cli_no_external_api` — Zero chamadas de rede

## Comandos

```bash
python omnis.py pipeline dry-run <queue-id>    # Executa pipeline completo
python omnis.py pipeline status                 # Histórico de execuções
```

## O que NÃO foi feito (regras seguidas)

- Nenhum push para git
- Nenhum OAuth
- Nenhuma chamada Instagram/Meta
- Nenhuma chamada Google Drive
- Nenhuma alteração no Publisher OS real
- Nenhum docker prune ou restart
- Nenhuma leitura de .env
- Nenhum LangGraph, OpenHands, build_skill()
- Nenhuma migração JSONL → Postgres
- Nenhuma refatoração do cli.py inteiro
