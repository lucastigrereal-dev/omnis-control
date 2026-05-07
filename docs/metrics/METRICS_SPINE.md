# METRICS SPINE — P0.9

**Data:** 2026-05-07
**Objetivo:** Medir a operacao do OMNIS antes de publicar de verdade.

## Por que depois de Tool Registry?

P0.8 catalogou 19 ferramentas com status honestos. Mas nao havia como saber:

- Quais ferramentas foram realmente usadas?
- Quanto tempo cada missao levou?
- Quantas missoes falharam vs concluiram?
- Quantos checkpoints/retries aconteceram?

A Metrics Spine responde essas perguntas localmente, sem API externa.

## Modelo de dados

**MetricEvent** — evento atomico de metrica:
- metric_id, timestamp, name, value, unit, status
- mission_id, run_id, tool_id, event_type
- duration_ms, tokens_in/out, cost_usd
- tags, metadata

**RunSummary** — agregado de uma execucao:
- run_id, mission_id, started_at, finished_at, status
- duration_ms, events_count, tools_used
- warnings_count, retries_count, checkpoints_count
- total_tokens, total_cost_usd

## Storage

```
data/metrics_spine/
  metrics.jsonl    — MetricEvent (append-only)
  runs.jsonl       — RunSummary (upsert por run_id)
```

## Comandos CLI

```bash
python jarvis.py metrics status              # resumo de hoje
python jarvis.py metrics today               # detalhe das runs de hoje
python jarvis.py metrics mission <id>        # metricas de uma missao
python jarvis.py metrics tools               # uso por ferramenta
python jarvis.py metrics export --format json  # export completo
python jarvis.py metrics export --format csv   # export CSV
```

Todos aceitam `--json` para output estruturado.

## Integracao

- **mission_pipeline.py**: start_run/finish_run em cada execucao
- **missions/runtime.py**: quick_record_metric em checkpoint/pause/resume/retry
- **tool_registry/__init__.py**: quick_record_metric em get_tool_availability()

## Limitacoes

- Sem OAuth, sem API externa, sem .env
- Sem custo real de LLM se nao informado
- Sem dashboard (Grafana/Streamlit)
- Sem Postgres (JSONL apenas para MVP)
- Sem auto-discovery de metricas
- Metricas sao locais — sem export para servico externo

## Proxima fase

**P1.0 DISK-1** — 1 post real controlado em conta teste, ou **OAuth Meta** para destravar Instagram Graph API.
