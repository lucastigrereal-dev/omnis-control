# P24 — LIVE COCKPIT SUPREME SKELETON

> **Data:** 2026-05-13
> **Status:** SKELETON COMPLETE
> **Tests:** 78+ (targeted), all passing

---

## FILES

```
src/live_cockpit/
├── __init__.py          # Public exports (15 symbols)
├── models.py             # CockpitSnapshot, CockpitModule
├── errors.py             # CockpitError + 4 subclasses
├── collector.py          # CockpitCollector — coleta dados de todos os modulos
├── renderer.py           # CockpitRenderer — 4 formatos (full, compact, json, markdown)
├── alerts.py             # AlertAggregator — coleta, priorizacao, resumo
└── cli.py                # CLI: show, compact, export, watch

tests/live_cockpit/
├── test_models.py        # 22 testes
├── test_collector.py     # 17 testes
├── test_renderer.py      # 16 testes
├── test_alerts.py        # 13 testes
└── test_e2e_cockpit.py   # 12 testes

docs/live_cockpit/
└── P24_LIVE_COCKPIT_SUPREME_SKELETON.md
```

**Total: 7 source + 5 test + 1 doc = 13 arquivos, 80 testes**

---

## CONTRACTS

### CockpitSnapshot
- `snapshot_id` prefix: `ckp_`
- Contem: missoes, pipeline, saude, autonomo, memoria, sistema
- `overall_status`: healthy | degraded | critical
- `is_complete`: True se sem collection_errors
- Never breaks — always returns best available data
- Factory: `CockpitSnapshot.new()`

### CockpitModule
- Status: healthy | degraded | error | unknown
- Properties: is_healthy, is_degraded, is_error
- Factory: `CockpitModule.new(module_name, namespace)`

### CockpitCollector
- `collect_all()` — agrega dados de todos os modulos
- Cada `collect_*()` e independente e nunca quebra
- Modulo indisponivel → status "unknown"
- dry_run=True default

### CockpitRenderer
- `render()` — terminal completo
- `render_compact()` — 1 tela
- `render_json()` — JSON formatado
- `render_markdown()` — Markdown para compartilhar

### AlertAggregator
- Coleta alerts de modules + collection errors/warnings
- Priorizacao: critical > high > medium > low > info
- `summary()` — "2 critical, 1 high, 3 medium"

### CLI
- `cockpit show` — cockpit completo
- `cockpit compact` — versao 1 tela
- `cockpit export [--format json|markdown] [-o file]`
- `cockpit watch [--interval 60]` — modo watch

---

## DEPENDENCIES
- Le de modulos via lazy imports (nao quebra se ausentes)
- Zero toques em modulos existentes
