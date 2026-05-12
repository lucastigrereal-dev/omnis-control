# P13 Analytics/BI Skeleton — Relatório Final

**Frente:** P13 — Analytics & BI Skeleton
**Onda:** 2
**Branch:** `parallel/p13-analytics-skeleton`
**Data:** 2026-05-12
**Modo:** deterministic, dry-run, zero-network, zero-Docker, zero-database

---

## 1. Visão Geral

Skeleton isolado para Analytics/BI seguindo o padrão OMNIS de pacotes determinísticos. Sem integração com CLI, sem banco real, sem rede, sem Docker.

### Escopo Permitido

| Diretório | Status |
|---|---|
| `src/analytics/` | Criado |
| `tests/analytics/` | Criado |
| `docs/analytics/` | Criado |

### Escopo Proibido (não tocado)

`src/mission/`, `src/app_factory/`, `src/automation/`, `src/computer_ops/`, `src/governance/`, `src/output_generator/`, `src/core/`, `src/cli.py`, `pyproject.toml`, `.env`, `data/`, `exports/`, `logs/`

---

## 2. Arquitetura

```
src/analytics/
  __init__.py       — API pública, __all__ com 29 símbolos
  models.py         — 5 dataclasses + 6 conjuntos de constantes
  errors.py         — 8 classes de erro hierárquicas
  service.py        — AnalyticsPlanner + MetricSummary + ValidationResult
  exporters.py      — export_dashboard_json() + export_report_markdown()

tests/analytics/
  __init__.py
  test_models.py    — 34 testes (5 modelos + constantes)
  test_service.py   — 24 testes (planner + summary + validation)
  test_exporters.py — 11 testes (JSON + Markdown exporters)
```

---

## 3. Modelos

### 3.1 MetricDefinition

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `met_` + 8 hex |
| `name` | `str` | Nome legível da métrica |
| `description` | `str` | O que a métrica mede |
| `category` | `str` | Domínio: engagement, revenue, growth, etc. |
| `aggregation` | `str` | Como agregar: sum, avg, count, max, min, p50, p95, p99 |
| `unit` | `str` | Unidade: count, percentage, currency_brl, seconds, etc. |
| `dimensions` | `list[str]` | Dimensões de quebra (profile, date, region, etc.) |
| `filters` | `dict[str, str]` | Filtros padrão |
| `target` | `float \| None` | Meta opcional |
| `created_at` | `str` | ISO 8601 UTC |

**Factory:** `MetricDefinition.new(name, description, category, aggregation, unit, ...)`
**Validação:** Rejeita category/aggregation/unit inválidos via `ValueError`.

### 3.2 MetricEvent

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `evt_` + 8 hex |
| `metric_id` | `str` | Referência à MetricDefinition |
| `value` | `float` | Valor da observação |
| `timestamp` | `str` | ISO 8601 UTC |
| `dimensions` | `dict[str, str]` | Valores dimensionais (ex: `{"profile": "@lucastigrereal"}`) |
| `metadata` | `dict[str, str]` | Metadados extras |
| `dry_run` | `bool` | Default `True` |

**Factory:** `MetricEvent.new(metric_id, value, ...)`

### 3.3 AnalyticsDataset

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `ds_` + 8 hex |
| `name` | `str` | Nome do dataset |
| `description` | `str` | Descrição |
| `metrics` | `list[MetricDefinition]` | Definições registradas |
| `events` | `list[MetricEvent]` | Eventos coletados |
| `period_start` | `str \| None` | Início do período |
| `period_end` | `str \| None` | Fim do período |
| `row_count` | `int` (property) | `len(events)` |
| `created_at` | `str` | ISO 8601 UTC |

### 3.4 DashboardSpec

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `dash_` + 8 hex |
| `title` | `str` | Título do dashboard |
| `description` | `str` | Descrição |
| `layout` | `str` | grid, single_column, two_columns, tabbed, freeform |
| `widgets` | `list[dict]` | Widgets com type, title, metric_id, position, config |
| `refresh_interval_minutes` | `int` | Default 60 |
| `created_at` | `str` | ISO 8601 UTC |

### 3.5 ReportSpec

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | `str` | Prefixo `rpt_` + 8 hex |
| `title` | `str` | Título do relatório |
| `description` | `str` | Descrição |
| `sections` | `list[dict]` | Seções com title, type, content, charts |
| `format` | `str` | markdown, html, pdf |
| `created_at` | `str` | ISO 8601 UTC |

---

## 4. Constantes de Domínio

| Constante | Cardinalidade | Valores |
|---|---|---|
| `VALID_AGGREGATIONS` | 8 | sum, avg, count, max, min, p50, p95, p99 |
| `VALID_CATEGORIES` | 7 | engagement, revenue, growth, content, audience, conversion, retention |
| `VALID_UNITS` | 8 | count, percentage, currency_brl, seconds, minutes, hours, views, interactions |
| `VALID_LAYOUTS` | 5 | grid, single_column, two_columns, tabbed, freeform |
| `VALID_WIDGET_TYPES` | 8 | kpi_card, line_chart, bar_chart, pie_chart, table, heatmap, funnel, gauge |
| `VALID_REPORT_FORMATS` | 3 | markdown, html, pdf |

---

## 5. Serviço

### 5.1 AnalyticsPlanner

Classe principal de planejamento analítico. `dry_run=True` por padrão.

| Método | Retorno | Descrição |
|---|---|---|
| `plan_metric(name, desc, category, agg, unit, ...)` | `MetricDefinition` | Cria e registra métrica |
| `build_dashboard_spec(title, desc, metrics, layout, ...)` | `DashboardSpec` | Gera spec com widgets KPI automáticos |
| `summarize_metrics(events)` | `list[MetricSummary]` | Agrupa e sumariza eventos por metric_id |
| `summarize_single(metric_id, events)` | `MetricSummary` | Sumariza uma métrica específica |
| `validate_dataset(dataset)` | `ValidationResult` | Valida integridade estrutural |
| `plan_report(title, desc, sections, format)` | `ReportSpec` | Cria spec de relatório |
| `list_metrics()` | `list[MetricDefinition]` | Cópia das métricas planejadas |
| `metric_count` | `int` (property) | Total de métricas planejadas |

### 5.2 MetricSummary

| Campo | Tipo | Descrição |
|---|---|---|
| `metric_id` | `str` | Métrica sumarizada |
| `count` | `int` | Número de eventos |
| `sum` | `float` | Soma total |
| `avg` | `float` | Média (statistics.mean) |
| `min` | `float` | Valor mínimo |
| `max` | `float` | Valor máximo |
| `median` | `float` | Mediana (statistics.median) |
| `std_dev` | `float` | Desvio padrão (statistics.stdev, 0 se count < 2) |

### 5.3 ValidationResult

| Campo | Tipo | Descrição |
|---|---|---|
| `valid` | `bool` | Resultado da validação |
| `issues` | `list[str]` | Problemas críticos |
| `warnings` | `list[str]` | Avisos não-bloqueantes |
| `ok` | `bool` (property) | `valid and len(issues) == 0` |

---

## 6. Exportadores

| Função | Entrada | Saída | Descrição |
|---|---|---|---|
| `export_dashboard_json(spec, path)` | `DashboardSpec` | `.json` | JSON com meta + dashboard |
| `export_report_markdown(spec, path)` | `ReportSpec` | `.md` | Markdown com seções e charts |

---

## 7. Hierarquia de Erros

```
AnalyticsError
├── InvalidMetricError
├── InvalidDatasetError
│   ├── DatasetEmptyError
│   └── DatasetSchemaMismatchError
├── DashboardError
├── ReportError
└── ExportError
```

---

## 8. Resumo de Testes

| Arquivo | Testes | O que cobre |
|---|---|---|
| `test_models.py` | 34 | 16 MetricDefinition, 8 MetricEvent, 5 AnalyticsDataset, 8 DashboardSpec, 5 ReportSpec, 6 Constants |
| `test_service.py` | 24 | 4 ValidationResult, 4 MetricSummary, 16 AnalyticsPlanner |
| `test_exporters.py` | 11 | 5 export_dashboard_json, 6 export_report_markdown |
| **Total** | **82** | |

### Cobertura de padrões por modelo:
- Factory `.new()` com validação
- `to_dict()` / `from_dict()` round-trip
- `to_json()` / `from_json()` round-trip (MetricDefinition)
- Valores default
- Unicidade de IDs
- Rejeição de valores inválidos
- Testes parametrizados para todas as constantes válidas

---

## 9. Decisões de Design

1. **Dataclasses, não Pydantic** — Seguindo o padrão dos skeletons automation (P12), app_factory (P11), mission adapter. Performance, zero dependências extras.
2. **`from __future__ import annotations`** — Avaliação lazy de type hints, padrão OMNIS.
3. **`statistics` stdlib** — Para sumarização (mean, median, stdev). Sem pandas.
4. **`frozenset` para constantes** — Imutável, hashable, O(1) lookup.
5. **Prefixos de ID curtos** — `met_`, `evt_`, `ds_`, `dash_`, `rpt_` + 8 hex. Legível e único.
6. **ValidationResult como dataclass** — Retorno composto, não exceções, para validação. Padrão do automation skeleton.
7. **Exporters separados** — Responsabilidade única. JSON e Markdown em módulo dedicado.
8. **`dry_run=True` padrão** — Todo evento é dry-run por default. Consistente com o protocolo do projeto.

---

## 10. Limitações (by Design)

- Sem persistência real (sem banco, sem JSONL store como automation)
- Sem agregações temporais (daily/weekly/monthly rollups)
- Sem execução de queries reais
- Sem integração com CLI (`src/cli.py`)
- Sem dashboard rendering visual
- Sem conectores de dados externos
- Exportadores só cobrem JSON e Markdown (sem HTML/PDF rendering real)

---

## 11. Próximos Passos

1. **P14 Analytics Store** — Adicionar persistência JSONL local (padrão `store.py` dos skeletons)
2. **P16 Analytics CLI** — Integrar com `src/cli.py` para comandos `omnis analytics *`
3. **P20 Analytics Engine** — Agregações temporais, rolling windows, anomaly detection determinística
4. **Conectores** — Pipelines de ingestão de dados reais (Meta API, Google Analytics, etc.)

---

## 12. Verificação Final

```
$ python -m pytest tests/analytics/ -q
........................................................................ [ 87%]
..........                                                               [100%]
82 passed in 0.11s
```

**Status:** 82/82 PASS
**Modo:** Determinístico. Zero LLM. Zero rede. Zero Docker.
**Gerado:** 2026-05-12 — P13 Analytics/BI Skeleton v1.0.0
