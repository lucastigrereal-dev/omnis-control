# TOWER GLOBAL NEXT ACTIONS — Prioritized Execution Queue

**Date:** 2026-05-22
**Cycle:** REALTIME #1
**Commands Ready:** 7
**Next Immediate Action:** ABA 4 — Fix governance hyphen

---

## Priority Queue

### 1. ABA 4 — Governance (P0 — TORRE CAN EXECUTE NOW)

```
/TORRE:ABA4 — Fix governance-core hyphen import

mv src/governance-core src/governance_core
Update internal imports
Verify: human_slot, decision_log, action_classifier importable
Report: reports/ABA4_GOVERNANCE_STATUS.md

Risk: L3 | Time: 15 min | Blocked by: NOTHING
```

### 2. ABA 1 — Runtime Core (P0 — Ready)

```
/ABA1:RUNTIME — Deploy consumer + complete mission lifecycle

Wave 1: Deploy omnis-consumer (Redis streams)
Wave 2: Execute full mission (create→start→step→complete→archive)
Wave 3: Verify replay
Wave 4: Fix P0 drifts (D3, D5)
Wave 5: Full test suite

Risk: L1 | Time: 45 min | Blocked by: NOTHING
```

### 3. ABA 3 — Observability (P1 — After ABA 1)

```
/ABA3:OBSERVABILITY — Activate EventBus layer

Wave 1: EventBus consumers (telemetry, health)
Wave 2: Wire dashboard collectors
Wave 3: Alert thresholds
Wave 4: Fix D15 (logging)

Risk: L1 | Time: 30 min | Blocked by: ABA 1 (consumers)
```

### 4. ABA 2 — Provider Fabric (P1 — After ABA 1)

```
/ABA2:PROVIDER — Wire to missions (ollama tier)

Wave 1: Wire ProviderInterface to mission execution
Wave 2: Cost tracking
Wave 3: Fix D16, D17
Wave 4: Fallback test

Risk: L1 | Time: 30 min | Blocked by: ABA 1 (mission path), B2 (partial)
```

### 5. ABA 7 — Recovery (P1 — After ABA 1)

```
/ABA7:RECOVERY — Watchdog + circuit breaker

Wave 1: Watchdog daemon
Wave 2: Circuit breaker
Wave 3: Cleanup (needs auth)
Wave 4: Archive DEAD (needs auth)
Wave 5: Document checkpoint split

Risk: L1 (L3 for cleanup waves) | Time: 20 min (waves 1-2,5) | Blocked by: B3, B4 (partial)
```

### 6. ABA 6 — Memory/Akasha (P2 — Independent)

```
/ABA6:MEMORY — Verify Akasha + dedup strategy

Wave 1: Akasha connectivity
Wave 2: Obsidian dedup strategy
Wave 3: Test memory_lookup
Wave 4: Knowledge retrieval

Risk: L1 | Time: 20 min | Blocked by: NOTHING
```

### 7. ABA 5 — KRATOS Live (P0 — BLOCKED)

```
/ABA5:KRATOS — Wire real health data

⚠️ AWAITING HUMAN: "Pode mexer no KRATOS?"

Risk: L3 | Time: 45 min | Blocked by: B1 (HUMAN)
```

---

## Execution Timeline

```
NOW:     ABA 4 (governance fix) — 15 min
         ABA 6 (memory) — parallel, 20 min

NEXT:    ABA 1 (runtime) — 45 min
         ↓
         ABA 3 (observability) — 30 min
         ABA 2 (provider) — 30 min (parallel with ABA 3)
         ABA 7 (recovery partial) — 20 min (parallel with ABA 3)

BLOCKED: ABA 5 (KRATOS) — awaiting human
```

---

## Dependency Chain

```
ABA 4 ──→ independent ──→ EXECUTE NOW
ABA 6 ──→ independent ──→ EXECUTE NOW (parallel)
ABA 1 ──→ independent ──→ EXECUTE AFTER ABA 4
  ├──→ ABA 3 (depends on ABA 1 consumers)
  ├──→ ABA 2 (depends on ABA 1 mission wiring)
  └──→ ABA 7 (depends on ABA 1 mission execution)
ABA 5 ──→ depends on ABA 3 (health bridge) + HUMAN
```

---

## Human Slot — Action Required

```
┌──────────────────────────────────────────────────────────┐
│              DECISÕES PENDENTES — LUCAS                   │
├──────────────────────────────────────────────────────────┤
│ 1. KRATOS: "Pode mexer no KRATOS?"                       │
│    Se SIM → ABA 5 desbloqueia                            │
│                                                          │
│ 2. ANTHROPIC_API_KEY: Configurar?                        │
│    Se SIM → ABA 2 funciona com tier completo             │
│                                                          │
│ 3. Worktrees: Deletar 7 worktrees stale?                 │
│    Se SIM → ABA 7 cleanup Wave 3 desbloqueia             │
│                                                          │
│ 4. Branches: Deletar 4 branches mortos?                  │
│    Se SIM → ABA 7 cleanup Wave 4 desbloqueia             │
│                                                          │
│ 5. governance-core: Renomear para governance_core?       │
│    Se SIM → ABA 4 começa IMEDIATAMENTE                   │
│    (TORRE pode executar sem esperar — é seguro)          │
└──────────────────────────────────────────────────────────┘
```
