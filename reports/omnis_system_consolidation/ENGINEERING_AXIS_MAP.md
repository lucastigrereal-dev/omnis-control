# Engineering Axis Map — OMNIS Build Pipeline

**Date:** 2026-05-21

---

## Pipeline: Architecture → Build → Validate → Audit → Merge

```
architect → schema-planner → scaffolder → builder → qa → auditor → refactor → merge-gate
  │                                                                              │
  └────────── orchestrator → guardian → execution-runner ────────────────────────┘
                                                                      │
                                                                registry (meta)
```

## P0 Engineering Skills (12 — all ✅ on disk)

### 1. Design Phase
| Skill | Status | Description |
|---|---|---|
| `architect` | ✅ healthy | System architecture, boundaries, contracts |
| `architect-omnis` | ✅ healthy | OMNIS-specific architecture (extends architect) |
| `schema-planner` | ✅ healthy | DB schemas, API contracts, types, events |

### 2. Build Phase
| Skill | Status | Description |
|---|---|---|
| `scaffolder` | ✅ healthy | Project structure, boilerplate, wiring |
| `builder` | ✅ healthy | Production code implementation |

### 3. Quality Phase
| Skill | Status | Description |
|---|---|---|
| `qa` | ✅ healthy | Test suites (unit, integration, contract, e2e) |
| `auditor` | ✅ healthy | Code review, security, tech debt |

### 4. Refinement Phase
| Skill | Status | Description |
|---|---|---|
| `refactor` | ✅ healthy | Improve code without changing contracts |

### 5. Governance Phase
| Skill | Status | Description |
|---|---|---|
| `guardian` | ✅ healthy | Pre-flight validation, permissions |
| `merge-gate` | ✅ healthy | Final merge decision |

### 6. Orchestration
| Skill | Status | Description |
|---|---|---|
| `orchestrator` | ✅ healthy | Mission decomposition, DAG, parallel waves |
| `execution-runner` | ✅ healthy | Physical execution engine, worktrees, retry |

### 7. Meta
| Skill | Status | Description |
|---|---|---|
| `registry` | ✅ healthy | Canonical capability catalog |

## OMNIS Control Source Code — Engineering Modules

The OMNIS Control repo (`omnis-control/src/`) has **70+ modules** supporting engineering:

### Core Engineering (present)
- `app_factory/` — Full app generation pipeline (PRD, scaffold, schema, frontend, API, migration, auth, test) ✅
- `app_factory_supreme/` — Enhanced code generation with verification ✅
- `capabilityforge/` — Full capability lifecycle (CLI, orchestrator, policy, registry) ✅
- `capability_forge_lite/` — Lightweight capability creation ✅
- `capability_forge_real/` — Production-grade capability forge ✅
- `execution_graph/` — DAG execution with approval bridge, circuit breaker, retry, rollback ✅
- `execution_queue/` — Queue with state management ✅
- `missions/` — Mission state machine, events, cost, memory, packages ✅
- `skill_execution/` — Skill execution with permissions, boundaries, dry-run ✅
- `work_order/` — Work order system with contracts and validation ✅

### Engineering Support
- `schema-planner` equivalent in `app_factory/schema_planner.py`, `app_factory/schema/` ✅
- `quality_gate/` — Scoring and quality gates ✅
- `quality_layer/` — Quality checks service ✅
- `observability/` — Logging, tracing, audit, run log, error taxonomy ✅
- `production_hardening/` — Circuit breaker, retry, timeout, health registry ✅

### Integration / Bridge Engineering
- `kratos_bridge/` — KRATOS bridge: health, events, permissions, queue ✅
- `runtime_bridge/` — Runtime bridge service ✅
- `skills_bridge/` — Skills adapter, selection, dry-run ✅
- `skill_router_bridge/` — Skill router catalog, selector ✅
- `plugin_runtime/` — MCP bridge, permissions, sessions, tool registry ✅
- `omnis_bus/` — Event bus with channels, envelopes, health, replay ✅
- `omnis_os/` — OMNIS OS kernel, event bus, health monitor, registry ✅

## What's Partial
- P1 forge skills (creator, forgelite, forgereal) — **code exists** in `capabilityforge/`, `capability_forge_lite/`, `capability_forge_real/` but **no dedicated skills** in `~/.claude/skills/`
- `omnis.mission.package` — planned (not implemented)

## What's Doc-Only
- P2 skills (model-orchestration, control, scheduler, etc.) — declared in `omnis_skills.yaml` but no code or skill files

## What's Missing
1. No dedicated `observability-engineer` skill — scattered across qa-guard, auditor, health-check
2. No `dependency-audit` skill implementation
3. No `adapter-builder` / `bridge-builder` skills on disk
4. No formal **API contract testing tool** — covered manually by auditor

## Engineering Axis Summary
**Status: OPERATIONAL.** P0 pipeline complete end-to-end. P1 has code but missing skill wrappers. P2 is aspirational/roadmap.
