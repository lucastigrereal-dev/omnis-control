# GLOBAL DRIFT & FRAGMENTATION — Ecosystem Coherence Analysis

**Date:** 2026-05-22
**Mission:** GLOBAL EVALUATION — Wave 3
**Drifts:** 22 | **Fragmentation Points:** 8 | **Conflict Zones:** 4

---

## 1. Structural Drifts (22 total)

### P0 — Structural (6)

| # | Drift | Type | Domains | Impact |
|---|-------|------|---------|--------|
| D1 | KRATOS 100% mock data | MOCK RUNTIME | Dashboard, Health | Operator sees fiction |
| D2 | governance-core hyphen breaks 3 modules | STALE CODE | Governance | 50% dead |
| D3 | 4 test-to-source mismatches (v2 dirs) | BROKEN TESTS | Runtime | Tests import from empty dirs |
| D4 | CURRENT_STATE.md 9 commits stale | STALE DOCS | Documentation | Wrong operational picture |
| D5 | Redis EventBus zero consumers | DEAD INFRA | EventBus, Obs | Write-only bus |
| D6 | ACTIVE_WORKTREES.md missing 3 worktrees | STALE DOCS | Documentation | Git state mismatch |

### P1 — High (8)

| # | Drift | Type | Domains |
|---|-------|------|---------|
| D7 | Dual registry naming (JARVIS vs OMNIS) | NAMING | Registry, Docs |
| D8 | 15 DEAD packages in source tree | DEAD CODE | Runtime |
| D9 | No automated watchdog | MISSING | Recovery |
| D10 | Provider not wired to missions | DISCONNECTED | Provider, Missions |
| D11 | 18 P1/P2 skills declared but unscaffolded | REGISTRY FICTION | Registry |
| D12 | ollama model name hardcoded in 7 places | HARDCODED | Provider |
| D13 | 5 dead litellm imports | DEAD IMPORTS | Provider |
| D14 | configure_logging returns None | MINOR BUG | Observability |

### P2 — Low (8)

| # | Drift | Type | Domains |
|---|-------|------|---------|
| D15 | 40-50% Obsidian duplication | DATA DUP | Memory |
| D16 | 7 stale worktrees | STALE | Infrastructure |
| D17 | 4 dead branches | STALE | Infrastructure |
| D18 | Two separate checkpoint systems | DUPLICATION | Runtime, Recovery |
| D19 | Provider in separate repo (omnis-runtime) | FRAGMENTED | Provider |
| D20 | governance/ vs governance-core/ split | DUPLICATE | Governance |
| D21 | Human Slot not wired to Telegram | DISCONNECTED | Governance |
| D22 | Cost tracking zero data | DEAD FEATURE | Provider |

---

## 2. Fragmentation Map

### Duplication Fragments

| Fragment | Location A | Location B | Severity |
|----------|-----------|-----------|----------|
| Governance modules | `src/governance/` (functional) | `src/governance-core/` (broken) | HIGH |
| Checkpoint systems | `src/missions/runtime.py` | `src/execution_graph/replay.py` | MEDIUM |
| Provider interface | `omnis-runtime/src/` | (not vendored in omnis-control) | MEDIUM |
| Obsidian knowledge | 38,661 files, 40-50% dup | Akasha (20K docs, deduplicated) | MEDIUM |

### Runtime Parallelism (potential)

| Concern | Status |
|---------|--------|
| Is omnis-maintenance executing anything? | NO — frozen legacy |
| Is omnis-server running? | NO — shell experimental only |
| Is any code writing to the same Redis? | NO — aurora_redis :6381 exclusive |
| Are there 2 competing mission models? | NO — single canonical in `src/missions/models.py` |

### Naming Conflicts

| Conflict | Impact |
|----------|--------|
| JARVIS Maestro vs OMNIS Control | Operator confusion, searchability |
| `governance` vs `governance_core` | Import errors, dual authority |
| `omnis_bus` (src) vs `omnis_bus` (tests) | Clean separation, no conflict |

---

## 3. Authority Conflicts

| Conflict | ABAs | Severity |
|----------|------|----------|
| Governance dir split | ABA 4 vs (none) | HIGH |
| Dual checkpoint ownership | ABA 1 vs ABA 7 | MEDIUM |
| Provider external repo | ABA 2 vs (none) | MEDIUM |
| JARVIS/OMNIS naming | TORRE vs (none) | LOW |

---

## 4. Stale Runtime Detection

| Artifact | Staleness | Risk |
|----------|-----------|------|
| CURRENT_STATE.md | 9 commits behind | MEDIUM |
| ACTIVE_WORKTREES.md | 3 worktrees missing | LOW |
| omnis_health.json | >1h old | LOW (no consumers) |
| kratos_health.json | >1h old | LOW (KRATOS mock) |
| governance_audit.jsonl | 1 entry, >1h old | LOW |
| Mission events | 2 events, >1h old | LOW |

---

## 5. Mock Runtime Inventory

| Mock System | What It Fakes | Detection |
|-------------|--------------|-----------|
| KRATOS store.ts | All dashboard data | Source analysis |
| Dashboard collectors | 8/9 return zero | Live test |
| Registry P1/P2 skills | 18 declared as active | File system check |
| Human slot notification | Approval gate escalation | Import blocked anyway |

---

## 6. Dead Code Inventory

| Package | Files | Tests | Consumers |
|---------|-------|-------|-----------|
| kratos_bridge | 11 | 11 | 0 |
| akasha_event_sink | 4 | 0 | 0 |
| akasha_runtime | 3 | 0 | 0 |
| content_factory | 11 | 0 | 0 |
| 11 other DEAD | ~30 | ~10 | 0 |
| governance-core/* | 7 | 0 | 0 (unreachable) |
| **TOTAL** | **~66** | **~21** | **0** |

---

## 7. Dangerous Couplings

| Coupling | Risk | Why |
|----------|------|-----|
| ABA 1 → ABA 3 (EventBus) | LOW | ABA 3 explicitly depends on ABA 1 consumers |
| ABA 1 → ABA 2 (missions) | LOW | ABA 2 depends on mission wiring |
| ABA 3 → ABA 5 (health) | LOW | ABA 5 reads ABA 3's health file |
| ABA 4 → TORRE (rename) | LOW | Single file rename, well-scoped |
| **No dangerous tight couplings detected.** | | |

---

## 8. Fragmentation Score

| Dimension | Score | Detail |
|-----------|-------|--------|
| Code duplication | 0.70 | Two minor overlaps (checkpoint, governance) |
| Runtime coherence | 0.85 | Single canonical runtime, no shadow executors |
| Documentation accuracy | 0.40 | 4 key docs missing, 2 stale |
| Naming consistency | 0.60 | JARVIS/OMNIS split |
| Registry accuracy | 0.65 | 66.9% active, 12.7% dead |
| **OVERALL COHERENCE** | **0.64** | MODERATELY FRAGMENTED |

---

## Summary

OMNIS is **moderately fragmented (0.64)** with 22 known drifts, 4 duplication zones, and 4 authority conflicts. The ecosystem is more coherent than it appears — most fragmentation is well-understood and documented. The main risks are: governance directory split (trivial fix, high impact), KRATOS mock (blocks entire dashboard domain), and documentation staleness (operator reads wrong state).
