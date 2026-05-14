# P29 — OMNIS OS LAYER SKELETON

> **Data:** 2026-05-14
> **Status:** SKELETON COMPLETE

---

## FILES

```
src/omnis_os/
├── __init__.py          # Public exports (35 symbols)
├── models.py            # ModuleHealth, ModuleInfo, OmnisEvent, KernelConfig, BootstrapResult
├── errors.py            # OsError + 6 subclasses
├── module_contract.py   # OmnisModule ABC (name, namespace, version, dependencies, health_check, get_exports)
├── registry.py          # ModuleRegistry — CRUD, resolve, listing
├── legacy_wrapper.py    # LegacyModuleWrapper — wraps pre-P29 modules
├── dependency.py        # resolve_order, detect_cycles, validate_dependencies
├── event_bus.py         # EventBus — pub/sub with history
├── health_monitor.py    # HealthMonitor — concurrent health checks + aggregation
├── kernel.py            # OmnisKernel — bootstrap, shutdown, status
└── cli.py               # CLI: bootstrap, status, health, events, modules, shutdown

tests/omnis_os/
├── test_models.py       # 22 testes
├── test_module_contract.py # 15 testes
├── test_registry.py     # 18 testes
├── test_legacy_wrapper.py # 15 testes
├── test_dependency.py   # 19 testes
├── test_event_bus.py    # 19 testes
├── test_health_monitor.py # 13 testes
├── test_kernel.py       # 17 testes
├── test_cli.py          # 11 testes
└── test_e2e_omnis_os.py # 8 testes

docs/omnis_os/
└── P29_OMNIS_OS_SKELETON.md
```

---

## CONTRACTS

### ModuleHealth
- Fields: module_name, status, imports_ok, tests_passing, tests_total, version, last_checked, errors, warnings
- Properties: is_healthy, test_pass_rate

### ModuleInfo
- `module_id` prefix: `om_`
- Status flow: registered → active | degraded | inactive
- Legacy modules marked with is_legacy=True, health=HEALTH_UNKNOWN

### OmnisEvent
- `event_id` prefix: `ose_`
- All inter-module communication via OmnisEvents on EventBus

### OmnisModule (ABC)
- Abstract: name, namespace, version, health_check(), get_exports()
- Optional override: dependencies (defaults to [])

### ModuleRegistry
- Dual-index: by module_id + by name
- resolve(): try ID first, fallback to name
- Listing: all, active, by namespace, legacy

### Dependency Resolver
- Kahn's algorithm for topological sort
- DFS-based cycle detection
- validate_dependencies checks all refs exist

### EventBus
- In-process pub/sub with type-based routing
- Handler exceptions swallowed (don't crash the bus)
- Sliding history window (default 1000 events)
- dry_run=True suppresses handler invocation

### HealthMonitor
- ThreadPoolExecutor for concurrent checks
- Aggregation: overall status = max(error, degraded, healthy)
- check_count tracks total runs

### OmnisKernel
- Bootstrap flow: register → detect legacy → detect cycles → validate deps → resolve order → activate → health check
- Dry-run by default — no real module activation
- Emits kernel_bootstrapped / kernel_shutdown events

### CLI
- `omnis-os bootstrap` — dry-run bootstrap (default)
- `omnis-os status` — kernel status JSON
- `omnis-os health [--module]` — health checks
- `omnis-os events [--type] [--limit]` — event history
- `omnis-os modules [--namespace] [--legacy]` — module listing
- `omnis-os shutdown` — graceful shutdown

---

## DEPENDENCIES
- Zero toques em módulos existentes
- Bridges legacy modules via LegacyModuleWrapper
- Uses only Python stdlib (abc, dataclasses, secrets, datetime, json, argparse, pathlib, collections, concurrent.futures, typing)
