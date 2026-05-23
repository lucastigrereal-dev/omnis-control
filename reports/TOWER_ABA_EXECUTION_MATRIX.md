# TOWER ABA EXECUTION MATRIX

**Date:** 2026-05-22
**Authority:** TORRE CENTRAL
**Purpose:** Define scope, permissions, and deliverables for each ABA

---

## ABA 1 — Runtime Core

| Dimension | Value |
|-----------|-------|
| **Scope** | Execution graph, mission state machine, event bus, CLI commands, checkpoint/resume |
| **CAN touch** | `src/execution_graph/`, `src/missions/`, `src/omnis_bus/`, `src/cli_commands/` |
| **CANNOT touch** | KRATOS, providers, observability, governance, memory, .env |
| **Source of Truth** | `src/execution_graph/models.py`, `src/missions/models.py`, `src/omnis_bus/envelope.py` |
| **Expected Reports** | `reports/ABA1_RUNTIME_CORE_STATUS.md` |
| **Tests** | `tests/execution_graph/`, `tests/missions/`, `tests/omnis_bus/` |
| **Key Deliverables** | Full mission lifecycle (create→execute→checkpoint→complete), EventBus consumers, replay verified |

---

## ABA 2 — Provider Fabric

| Dimension | Value |
|-----------|-------|
| **Scope** | Provider interface, tier routing, fallback chain, cost tracking, model selection |
| **CAN touch** | `omnis-runtime/src/provider_interface.py`, provider config |
| **CANNOT touch** | KRATOS, missions, governance, .env, secrets |
| **Source of Truth** | `omnis-runtime/src/provider_interface.py` |
| **Expected Reports** | `reports/ABA2_PROVIDER_FABRIC_STATUS.md` |
| **Tests** | Provider routing tests (TBD) |
| **Key Deliverables** | Provider wired to missions, cost tracking active, ANTHROPIC_API_KEY configured |

---

## ABA 3 — Observability

| Dimension | Value |
|-----------|-------|
| **Scope** | Metrics spine, tracer, logging, health file, error taxonomy, event schemas |
| **CAN touch** | `src/observability/`, `data/metrics_spine/`, `~/.claude/state/omnis_health.json` |
| **CANNOT touch** | KRATOS, missions, governance, providers, .env |
| **Source of Truth** | `src/observability/health_file.py`, `src/observability/metrics/collector.py` |
| **Expected Reports** | `reports/ABA3_OBSERVABILITY_STATUS.md` |
| **Tests** | `tests/observability/` |
| **Key Deliverables** | EventBus-layer activated (Redis consumers), live dashboard collectors, alert thresholds |

---

## ABA 4 — Governance

| Dimension | Value |
|-----------|-------|
| **Scope** | Audit log, risk classifier, approval gate, human slot, decision log, action classifier, policies |
| **CAN touch** | `src/governance/`, `src/governance-core/`, `~/.claude/logs/governance_audit.jsonl` |
| **CANNOT touch** | KRATOS, missions, providers, .env, secrets |
| **Source of Truth** | `src/governance/service.py`, `src/governance-core/approvals/approval_gate.py` |
| **Expected Reports** | `reports/ABA4_GOVERNANCE_STATUS.md` |
| **Tests** | Governance tests (TBD) |
| **Key Deliverables** | Fix `governance-core` hyphen import, activate all 6 modules, wire human slot to Telegram |

---

## ABA 5 — KRATOS Live

| Dimension | Value |
|-----------|-------|
| **Scope** | KRATOS dashboard, health data feed, mission visibility, cockpit sync |
| **CAN touch** | `kratos-mission-control/` (WITH HUMAN AUTHORIZATION), `~/.claude/state/kratos_health.json` |
| **CANNOT touch** | OMNIS runtime, governance, providers, .env, secrets |
| **Source of Truth** | `kratos-mission-control/backend/app/store.ts` (currently mock) |
| **Expected Reports** | `reports/ABA5_KRATOS_LIVE_STATUS.md` |
| **Tests** | KRATOS frontend tests |
| **Key Deliverables** | Replace mock data with real health bridge, wire event stream, dashboard shows live state |
| **BLOCKER** | Human authorization required — "NUNCA tocar KRATOS" guardrail |

---

## ABA 6 — Memory / Akasha

| Dimension | Value |
|-----------|-------|
| **Scope** | Knowledge index, embeddings, retrieval, Akasha bridge, Obsidian dedup |
| **CAN touch** | Akasha (pgvector :5432), `src/missions/memory_lookup.py`, Obsidian vault |
| **CANNOT touch** | KRATOS, governance, providers, .env, secrets |
| **Source of Truth** | Akasha PostgreSQL DB, Obsidian vault (~38,661 files) |
| **Expected Reports** | `reports/ABA6_MEMORY_AKASHA_STATUS.md` |
| **Tests** | Akasha bridge tests (TBD) |
| **Key Deliverables** | Obsidian dedup strategy, Akasha wired to mission memory_lookup, knowledge retrieval validated |

---

## ABA 7 — Recovery / Self-Healing

| Dimension | Value |
|-----------|-------|
| **Scope** | Checkpoint/resume, replay, circuit breaker, watchdog, config drift, worktree cleanup |
| **CAN touch** | `src/missions/runtime.py`, `src/omnis_bus/replay.py`, `src/execution_graph/replay.py` |
| **CANNOT touch** | KRATOS, governance, providers, .env, secrets |
| **Source of Truth** | `src/missions/runtime.py` (checkpoint_mission, get_resume_context) |
| **Expected Reports** | `reports/ABA7_RECOVERY_STATUS.md` |
| **Tests** | Recovery tests (271 pass baseline) |
| **Key Deliverables** | Automated watchdog daemon, circuit breaker wired, worktree cleanup (with auth), dead branch removal |

---

## Cross-ABA Rules

1. **No ABA touches another ABA's source of truth without coordination**
2. **All ABAs report to TORRE via `reports/ABA<N>_*_STATUS.md`**
3. **TORRE reconciles conflicts — ABAs do NOT negotiate directly**
4. **If two ABAs need the same file, TORRE arbitrates**
5. **KRATOS (ABA 5) requires HUMAN AUTHORIZATION before any code change**
