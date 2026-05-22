# MISSION 3 — Drift Classifier

**Mission ID:** MIS-PHASE3-003
**Date:** 2026-05-22
**Status:** COMPLETE
**Risk Level:** L1 (LOCAL — read-only classification, auto-approved)

---

## Executive Summary

Classified 117 src/ packages, 27+ test directories, and 142 registry entries across 6 categories: CANONICAL, DRIFT, LEGACY, DEAD, SHADOW, MOCK. Found 15 DEAD packages (zero consumers), 18 DEAD registry entries (never scaffolded), 4 CRITICAL test-to-source mismatches, and a dual-registry naming conflict between JARVIS Maestro and OMNIS Control.

---

## 1. Source Code Classification (src/)

### Distribution

| Classification | Count | % |
|----------------|-------|---|
| CANONICAL | 63 | 53.8% |
| LEGACY | 18 | 15.4% |
| DRIFT | 15 | 12.8% |
| DEAD | 15 | 12.8% |
| SHADOW | 4 | 3.4% |
| MOCK | 2 | 1.7% |
| **Total** | **117** | 100% |

### CANONICAL (63 packages)
Active, tested, documented, externally imported. Core operational backbone.
Highlights: `execution_graph`, `governance-core`, `observability` (touched today). `missions` (13 files, 12 tests). `remote_control` (14 files, 14 tests). `cli_commands` (38 files, coverage via e2e).

### DRIFT (15 packages)
Active and imported, but missing docstrings or tests.
- `approval_runtime`, `checkers`, `execution_contracts`, `execution_queue`, `plugin_runtime`, `reports`, `role_registry`, `routers`, `runners`, `sector_registry`, `skill_matcher` — all lack __init__.py docstrings
- `capabilityforge` — legacy name variant, 0 dedicated tests
- `finance` — docs say "dry-run only", never graduated to real
- `pipeline_local` — old commit, 1 test only
- `video_studio` — 20 files, 15 tests, but zero external consumers

### DEAD (15 packages)
Zero external consumers. Code exists but nothing imports it.
- **`kratos_bridge`** — 11 files, 11 tests, **0 imports from anywhere in src/** — largest isolated module
- **Akasha family**: `akasha_event_sink` (6 files), `akasha_runtime` (8 files) — self-referencing only
- **OMNIS runtime family**: `omnis_bus` (7 files), `omnis_control` (2 files), `runtime_bridge`, `runtime_cli`, `runtime_orchestrator` — canonical bus no one subscribes to
- **Others**: `content_factory` (11 files), `local_search`, `output_factory`, `output_versioning`, `parallel_runner`, `preview`, `production_hardening` (9 files, 10 tests), `template_registry`, `war_room_bridge`, `weekly`

### LEGACY (18 packages)
Old patterns still referenced. Minimal tests, old commits (15-19 days).
- `argos_bridge`, `caption_approval`, `content_queue`, `creative_production`, `workflow` — oldest untouched (May 3-7)
- `backlog`, `autonomy`, `campaign_auditor`, `delivery_portal`, `delivery_templates` — skeleton/thin modules

### SHADOW (4 packages)
New code, not yet wired into import graph.
- `runtime_bridge`, `runtime_cli`, `runtime_orchestrator`, `skill_router_bridge`

### MOCK (2 packages)
- `asset_assignment` — has `add_mock_asset`, thin service
- `control_tower` — described as "simulated"

---

## 2. Test-to-Source Mismatches

### CRITICAL — Tests importing from nonexistent modules (4)

| Test File | Imports From | Issue |
|-----------|-------------|-------|
| `tests/caption_approval_v2/test_models.py` | `src.caption_approval_v2.models` | **Source dir is empty** (0 .py files) |
| `tests/caption_approval_v2/test_planner.py` | `src.caption_approval_v2.planner` | **Source dir is empty** |
| `tests/creative_production_v2/test_models.py` | `src.creative_production_v2.models` | **Source dir is empty** |
| `tests/creative_production_v2/test_planner.py` | `src.creative_production_v2.planner` | **Source dir is empty** |

These 4 tests will fail at import time. The v2 source modules were never created.

### Empty Shell Directories (8)

| Directory | Type | .py Files |
|-----------|------|-----------|
| `src/health/` | Source | 0 |
| `src/health_bridge/` | Source | 0 |
| `src/templates/` | Source | 0 |
| `src/caption_approval_v2/` | Source | 0 |
| `src/creative_production_v2/` | Source | 0 |
| `tests/health_bridge/` | Test | 0 |
| `tests/templates/` | Test | 0 |
| `tests/fixtures/` | Test | 0 |

### Source Modules Without Tests (5)

| Module | Files | Risk |
|--------|-------|------|
| `src/omnis_control/pipeline.py` | 1 | Untested pipeline |
| `src/workflow/` | 3 | Untested engine |
| `src/routers/` | 2 | Untested routing |
| `src/governance-core/` | 6 | Tested only indirectly via `tests/governance/` |
| `src/cli_commands/` | 24+ | No dedicated test package |

### Naming Inconsistencies (4)

| Pattern | src/ | tests/ |
|---------|------|--------|
| Hyphen vs none | `governance-core` | `governance` (tests different module) |
| Singular vs plural | `integrations` | `integration` |
| v1 vs v2 split | `caption_approval` has code, `caption_approval_v2` empty | Tests in `caption_approval_v2` import from empty dir |
| v1 vs v2 split | `creative_production` has code, `creative_production_v2` empty | Tests in `creative_production_v2` import from empty dir |

### Missing __init__.py (8 src directories)

`caption_approval_v2`, `creative_production_v2`, `executors`, `health`, `health_bridge`, `intelligence`, `memory`, `templates`

---

## 3. Registry Drift (142 entries)

### Classification

| Classification | Count | % |
|----------------|-------|---|
| ACTIVE | 95 | 66.9% |
| DRIFT | 16 | 11.3% |
| DEAD | 18 | 12.7% |
| LEGACY / DEPRECATED | 9 | 6.3% |
| BLUEPRINT | 4 | 2.8% |

### Critical Drift Patterns

**A. Dual Registry Conflict**
JARVIS Maestro `sectors.yaml` (7 sectors, old naming) and OMNIS Control `config/sectors.yaml` (9 sectors, new naming) coexist with different naming conventions. All 7 JARVIS sectors have drift — referencing deprecated skills as active, listing active skills as "planned".

**B. 18 P1/P2 Skills — Declared Active, Never Scaffolded**
`omnis_skills.yaml` declares 18 skills as "active v1.0.0" with zero files on disk:
- P1 Forge (10): creator, forgelite, forgereal, repo-intake, dependency-audit, adapter-builder, bridge-builder, matcher, composer, decomposer
- P2 Expansion (8): model-orchestration, worldactions, control, scheduler, missions, improvement, observability-local, report

**C. 13 Capability Specs — Blueprint Only**
All 13 `capabilities/*.yaml` files reference Docker images at `registry.local` (nonexistent), git repos at `git.local` (nonexistent), and MCP servers that don't exist. They form a circular dependency graph where every capability depends on others that also have zero runtime code.

**D. Deprecated-but-Referenced**
4 skills correctly marked deprecated in `skills.yaml`, but 3 sectors in `sectors.yaml` and 1 agent in `agents.yaml` still reference them as active.

**E. 3/6 Workflows DORMANT**
`daily_content_production`, `hotel_prospecting`, `fazer_dinheiro_agora` — all status PLANNED, skills exist but workflows were never activated.

---

## 4. Component Health Matrix

### Active Development Frontier (touched today)
| Component | Status | Tests |
|-----------|--------|-------|
| `execution_graph` | CANONICAL | 213/213 |
| `governance-core` | CANONICAL | Indirect only |
| `observability` | CANONICAL | 7+ |

### Largest Orphaned Modules
| Module | Files | Tests | Consumers |
|--------|-------|-------|-----------|
| `kratos_bridge` | 11 | 11 | **0** |
| `content_factory` | 11 | 10 | **0** (internal only) |
| `production_hardening` | 9 | 10 | **0** |
| `akasha_runtime` | 8 | 8 | **0** (self only) |
| `omnis_bus` | 7 | 6 | **0** |

### CLI as Single Point of Integration
`src/cli.py` imports from 25+ packages. Many modules classified as LEGACY or DEAD would be CANONICAL if wired through cli.py. The CLI is the great integrator — and also the single bottleneck.

---

## 5. Recommendations

| # | Action | Priority | Effort |
|---|--------|----------|--------|
| 1 | Delete or archive 15 DEAD packages | P1 | Low |
| 2 | Fix 4 CRITICAL v2 test imports (empty source dirs) | P1 | Low |
| 3 | Remove 8 empty shell directories | P1 | Low |
| 4 | Resolve dual registry naming (JARVIS vs OMNIS) | P1 | Medium |
| 5 | Remove or scaffold 18 P1/P2 dead registry entries | P2 | Medium |
| 6 | Add docstrings to 21 DRIFT packages | P2 | Low |
| 7 | Wire `omnis_bus` to actual consumers | P2 | Medium |
| 8 | Create tests for 5 uncovered src modules | P2 | Medium |
| 9 | Decommission 13 blueprint-only capability specs | P3 | Low |
| 10 | Activate 3 DORMANT workflows or mark as archived | P3 | Low |

---

## Validation

### Provider Routing
- 3 agent dispatches classified L1 (read-only filesystem scan)
- All routed through ollama_cloud correctly

### Mission Persistence
- trace_id propagated through all agent dispatches
- Event log: 6 events (3 agent_started + 3 agent_completed)

### Governance Hooks
- Zero Human Slot triggers (all L1)
- Decision log: 3 entries appended

---

## Next Action
Proceed to Mission 4 — Dashboard Sync
