# P25 — MULTI-MODEL ORCHESTRATION SKELETON

> **Data:** 2026-05-14
> **Status:** SKELETON COMPLETE
> **Tests:** P25 targeted passing

---

## FILES

```
src/multi_model_orchestration/
├── __init__.py            # Public exports (30+ symbols)
├── models.py              # ModelConfig, TaskClass, RoutingRequest, RoutingDecision
├── errors.py              # MultiModelError + 6 subclasses
├── classifier.py          # TaskClassifier — deterministic intent → TaskClass mapping
├── registry.py            # ModelRegistry — register, find, enable/disable
├── router.py              # ModelRouter — select_model(), execute()
├── fallback.py            # FallbackChain — try A → B → C
├── cost_tracker.py        # CostTracker — estimate, record, daily limit
├── cli.py                 # CLI: models, route, cost, classify
└── adapters/
    ├── __init__.py        # ModelAdapter protocol + ADAPTER_REGISTRY
    └── mock_adapter.py    # MockAdapter — zero API calls

tests/multi_model_orchestration/
├── test_models.py         # 30+ testes
├── test_classifier.py     # 16 testes
├── test_registry.py       # 28 testes
├── test_router.py         # 10+ testes
├── test_fallback.py       # 7+ testes
├── test_cost_tracker.py   # 10+ testes
└── test_e2e_multimodel.py # 12+ testes

docs/multi_model_orchestration/
└── P25_MULTI_MODEL_ORCHESTRATION_SKELETON.md
```

---

## CONTRACTS

### ModelConfig
- `model_id` prefix: `mm_`
- Properties: `is_cheap` (cost <= 0.005), `is_fast` (latency <= 500ms)
- Valid providers: anthropic, openai, groq, mock
- Factory: `ModelConfig.new(name, provider)`

### TaskClass
- `task_id` prefix: `tc_`
- Complexity: low | medium | high | critical
- Factory: `TaskClass.new(task_type, complexity, risk_level)`

### RoutingRequest
- `request_id` prefix: `mrr_`
- `dry_run` default: True
- Factory: `RoutingRequest.new(task)`

### RoutingDecision
- `decision_id` prefix: `mrd_`
- `is_dry_run` default: True
- `has_fallback` property
- Factory: `RoutingDecision.new(request_id, selected_model)`

### CostTracker
- `daily_limit_usd` default: 5.0
- `dry_run` default: True
- Dry-run always returns True from check_limit

### CLI
- `multi-model models` — list models
- `multi-model route <task>` — simulate routing
- `multi-model cost` — cost report
- `multi-model classify <intent>` — classify intent

---

## DEPENDENCIES
- Zero toques em módulos existentes
- stdlib-only: dataclasses, uuid, datetime, argparse, json
