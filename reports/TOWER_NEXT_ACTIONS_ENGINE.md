# TOWER NEXT ACTIONS ENGINE — Automated Command Generation

**Date:** 2026-05-22
**Cycle:** REALTIME #1
**Commands Generated:** 7 (1 per ABA)

---

## Action Generation Engine

| Component | Status |
|-----------|--------|
| Priority calculator | ACTIVE (P0 > P1 > P2 × dependency chain) |
| Dependency resolver | ACTIVE |
| Risk classifier | ACTIVE (L0-L5 per action) |
| Command formatter | ACTIVE |

---

## ABA 1 — Runtime Core

**Status:** READY | **Priority:** P0 | **Risk:** L1

### Command
```
/ABA1:RUNTIME — DEPLOY REDIS CONSUMER + COMPLETE MISSION LIFECYCLE

WAVE 1: Deploy omnis-consumer process
  - Subscribe to omnis:events:missions, omnis:events:telemetry
  - Verify events flow through Redis streams

WAVE 2: Execute full mission lifecycle
  - Create → Start → Step → Checkpoint → Complete → Archive
  - Verify all events persisted to JSONL

WAVE 3: Verify replay
  - Replay real mission events through ReplayBuffer
  - Confirm resumable=True

WAVE 4: Fix P0 drifts
  - D3: Fix 4 test-to-source mismatches (v2 dirs)
  - D5: Consumer deployed (Wave 1)

WAVE 5: Run full test suite
  - pytest tests/execution_graph/ tests/missions/ tests/omnis_bus/

DEPENDENCIES: None
BLOCKERS: None
ESTIMATED: 30-45 min
```

---

## ABA 2 — Provider Fabric

**Status:** READY_WITH_WARNINGS | **Priority:** P1 | **Risk:** L1

### Command
```
/ABA2:PROVIDER — WIRE TO MISSIONS + CENTRALIZE CONFIG

WAVE 1: Wire ProviderInterface to mission execution
  - Mission execution calls get_provider(tier) instead of default
  - Ollama tier fully functional (no API key needed)

WAVE 2: Activate cost tracking
  - Accumulate token counts per request
  - Log cost estimates (ollama=$0)

WAVE 3: Fix P2 drifts
  - D16: Remove 5 dead litellm imports
  - D17: Centralize model name config

WAVE 4: Test fallback chain
  - Simulate ollama failure → verify fallback logic
  - Anthropic fallback mock (key missing)

DEPENDENCIES: ABA 1 (mission execution path)
BLOCKERS: B2 (ANTHROPIC_API_KEY) — partial, ollama-only path works
ESTIMATED: 20-30 min
```

---

## ABA 3 — Observability

**Status:** READY | **Priority:** P1 | **Risk:** L1

### Command
```
/ABA3:OBSERVABILITY — ACTIVATE EVENTBUS LAYER + DASHBOARD COLLECTORS

WAVE 1: Activate EventBus consumers
  - Subscribe to omnis:events:telemetry, omnis:events:health
  - Verify real-time metric flow

WAVE 2: Wire dashboard collectors
  - Replace 8/9 zero-return collectors with real data sources
  - Verify non-zero returns

WAVE 3: Set alert thresholds
  - Health score < 0.7 → warning
  - Health score < 0.5 → critical

WAVE 4: Fix P2 drift
  - D15: Fix configure_logging None return

DEPENDENCIES: ABA 1 (Redis consumers deployed)
BLOCKERS: None
ESTIMATED: 20-30 min
```

---

## ABA 4 — Governance

**Status:** BLOCKED (B5 — TORRE can resolve) | **Priority:** P0 | **Risk:** L3 (directory rename)

### Command
```
/ABA4:GOVERNANCE — FIX HYPHEN IMPORT + ACTIVATE 3 MODULES

WAVE 1: Rename governance-core/ → governance_core/
  - mv src/governance-core src/governance_core
  - Update all internal __init__.py imports
  - Verify no external references broken

WAVE 2: Activate 3 blocked modules
  - Human Slot: from src.governance_core.approvals.human_slot import HumanSlot
  - Decision Log: from src.governance_core.audit.decision_log import DecisionLog
  - Action Classifier: from src.governance_core.permissions.action_classifier import classify_risk

WAVE 3: Wire human slot (mock notification)
  - Connect to notification channel (mock for now)
  - Test: L3+ action triggers human slot

WAVE 4: Write governance tests
  - At least 3 test files for governance modules

VALIDATION:
  python -c "from src.governance_core.approvals.human_slot import HumanSlot; print('OK')"
  python -c "from src.governance_core.audit.decision_log import DecisionLog; print('OK')"
  python -c "from src.governance_core.permissions.action_classifier import classify_risk; print('OK')"

DEPENDENCIES: None
BLOCKERS: B5 — TORRE authorized to resolve
ESTIMATED: 10-15 min
```

---

## ABA 5 — KRATOS Live

**Status:** BLOCKED (B1) | **Priority:** P0 | **Risk:** L3 (KRATOS code change)

### Command
```
/ABA5:KRATOS — WIRE REAL HEALTH DATA TO DASHBOARD

⚠️ BLOCKED — Requires human: "pode mexer no KRATOS"

WAVE 1: Read bridge contract
  - reports/WAVE3_KRATOS_REALDATA.md
  - Format: {status, score, timestamp, components}

WAVE 2: Modify KRATOS store.ts
  - Replace hardcoded mock with fetch from ~/.claude/state/kratos_health.json
  - Bridge file already exists and is updated by ABA 3

WAVE 3: Add fallback
  - If bridge file missing → fall back to mock (graceful degradation)

WAVE 4: Test dashboard
  - Verify components show real health data
  - Health score matches OMNIS health file

DEPENDENCIES: ABA 3 (health bridge writes)
BLOCKERS: B1 — HUMAN AUTHORIZATION REQUIRED
ESTIMATED: 30-45 min (after unblocked)
```

---

## ABA 6 — Memory/Akasha

**Status:** READY | **Priority:** P2 | **Risk:** L1

### Command
```
/ABA6:MEMORY — VERIFY AKASHA + DOCUMENT DEDUP STRATEGY

WAVE 1: Verify Akasha connectivity
  - pgvector :5432, biblioteca_sabedoria DB
  - Test query → response

WAVE 2: Document Obsidian dedup strategy
  - 38,661 files, 40-50% estimated duplication
  - Strategy: detect → classify → merge/archive

WAVE 3: Test memory_lookup
  - src/missions/memory_lookup.py with real Akasha query
  - Verify relevant chunks returned

WAVE 4: Knowledge retrieval validation
  - Query → relevant chunks → mission context

DEPENDENCIES: None
BLOCKERS: None
ESTIMATED: 15-20 min
```

---

## ABA 7 — Recovery/Self-Healing

**Status:** READY (partial) | **Priority:** P1 | **Risk:** L1 (L3 for cleanup waves)

### Command
```
/ABA7:RECOVERY — IMPLEMENT WATCHDOG + CIRCUIT BREAKER

WAVE 1: Implement watchdog daemon
  - Polls omnis_health.json every 60s
  - Triggers alert on score < 0.7
  - Logs incidents to recovery log

WAVE 2: Wire circuit breaker
  - Mission steps that fail 3x trigger circuit breaker
  - Circuit breaker prevents infinite retry loops

WAVE 3: Execute cleanup (NEEDS HUMAN AUTH)
  - Delete 7 stale worktrees
  - Delete 4 dead branches

WAVE 4: Archive DEAD packages (NEEDS HUMAN AUTH)
  - Move 15 DEAD packages to _archived/

WAVE 5: Unify checkpoint docs
  - Document mission vs graph checkpoint split
  - Decision: unify or maintain with clear boundary

DEPENDENCIES: ABA 1 (mission execution for circuit breaker)
BLOCKERS: B3 (worktree auth), B4 (branch auth) — only for Waves 3-4
ESTIMATED: 20-30 min (Waves 1-2, 5), 10 min (Waves 3-4 after auth)
```

---

## Execution Queue (Priority-Ordered)

| Order | ABA | Command | Priority | Blocker? |
|-------|-----|---------|----------|----------|
| **1st** | **ABA 4** | Fix hyphen + activate governance | P0 | TORRE resolves |
| 2nd | ABA 1 | Deploy consumer + mission lifecycle | P0 | None |
| 3rd | ABA 3 | Activate EventBus layer | P1 | After ABA 1 |
| 4th | ABA 2 | Wire provider + centralize config | P1 | After ABA 1 |
| 5th | ABA 7 | Watchdog + circuit breaker | P1 | None (partial) |
| 6th | ABA 6 | Verify Akasha + dedup strategy | P2 | None |
| 7th | ABA 5 | Wire KRATOS real data | P0 | HUMAN |

---

## Dependency Graph

```
ABA 4 (governance) ──→ independent
ABA 1 (runtime)    ──→ independent
ABA 3 (obs)        ──→ depends on ABA 1 (consumers)
ABA 2 (provider)   ──→ depends on ABA 1 (mission wiring)
ABA 7 (recovery)   ──→ depends on ABA 1 (mission execution)
ABA 6 (memory)     ──→ independent
ABA 5 (KRATOS)     ──→ depends on ABA 3 (health bridge) + HUMAN
```
