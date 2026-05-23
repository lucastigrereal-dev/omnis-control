# TOWER ABA BRIEFINGS

**Date:** 2026-05-22
**Authority:** TORRE CENTRAL
**Purpose:** Execution briefings for each ABA — what to build, rules, and deliverables

---

## ABA 1 — Runtime Core

**Status:** READY
**Priority:** P0 (foundational — all other ABAs depend on it)

### Objective
Activate the full mission lifecycle through OMNIS runtime: create → execute → checkpoint → complete → archive. Deploy EventBus consumers so streaming works end-to-end.

### Skills Required
- `OMNIS:orchestrator`, `OMNIS:builder`, `OMNIS:qa`
- `systematic-debugging` (if errors)
- `dispatching-parallel-agents` (for parallel test execution)

### Waves
1. **Deploy Redis consumer** — Process that reads from `omnis:events:*` streams
2. **Complete mission lifecycle** — Execute a full mission: create, start, step, complete, archive
3. **Verify replay** — Replay real mission events through ReplayBuffer
4. **Fix P0 drifts** — D3 (test-to-source mismatches), D5 (consumers)
5. **Run full test suite** — Verify 357+ tests still pass

### Prohibitions
- Do NOT touch KRATOS or kratos-mission-control
- Do NOT modify governance, providers, or observability modules
- Do NOT change the canonical envelope schema without TORRE approval
- Do NOT delete files

### Deliverables
- `reports/ABA1_RUNTIME_CORE_STATUS.md`
- Redis consumer process (script or daemon)
- At least 1 completed mission lifecycle on disk
- Test results: all suites green

### Validation
- `python -m pytest tests/execution_graph/ tests/missions/ tests/omnis_bus/ --import-mode=importlib -q`
- Mission events file has `mission_created`, `mission_started`, `mission_completed`
- Redis consumer has processed at least 1 real event

---

## ABA 2 — Provider Fabric

**Status:** READY_WITH_WARNINGS (B2: ANTHROPIC_API_KEY)
**Priority:** P1

### Objective
Wire the provider interface to mission execution so tier-based routing actually controls which LLM is called. Track real costs.

### Skills Required
- `OMNIS:builder`, `OMNIS:qa`
- `architecture-review`

### Waves
1. **Wire ProviderInterface to missions** — Mission execution calls `get_provider(tier)` instead of default
2. **Activate cost tracking** — Accumulate real token costs per request
3. **Fix P2 drifts** — D16 (dead litellm imports), D17 (model name centralization)
4. **Test fallback chain** — Simulate ollama failure → anthropic fallback

### Prohibitions
- Do NOT read .env or secrets
- Do NOT hardcode API keys
- Do NOT modify KRATOS or governance

### Deliverables
- `reports/ABA2_PROVIDER_FABRIC_STATUS.md`
- Provider wired to at least 1 mission execution path
- Cost tracking accumulation verified
- Model config centralized

### Validation
- Provider routing test: L1 mission uses ollama, L3 uses anthropic (mocked if key missing)
- Cost tracker shows > 0 accumulated cost

---

## ABA 3 — Observability

**Status:** READY
**Priority:** P1

### Objective
Activate the EventBus layer so metrics, traces, and health data stream in real-time instead of being polled. Wire live dashboard collectors.

### Skills Required
- `OMNIS:builder`, `OMNIS:qa`
- `operational-truth-engineer`

### Waves
1. **Activate EventBus consumers** — Subscribe to `omnis:events:telemetry`, `omnis:events:health`
2. **Wire dashboard collectors** — Replace 8/9 zero-return collectors with real data sources
3. **Set alert thresholds** — Health score < 0.7 triggers warning
4. **Fix P2 drift** — D15 (configure_logging None return)

### Prohibitions
- Do NOT touch KRATOS dashboard code (ABA 5 domain)
- Do NOT modify metrics schema without TORRE approval

### Deliverables
- `reports/ABA3_OBSERVABILITY_STATUS.md`
- At least 1 EventBus consumer processing real telemetry
- Dashboard collectors returning non-zero data
- Alert threshold config

### Validation
- `python scripts/wave4_checkpoint.py` (health probe) triggers observable events
- Metrics spine shows new entries from EventBus (not just static file)

---

## ABA 4 — Governance

**Status:** BLOCKED (B5 — hyphen rename required first)
**Priority:** P0 (3/6 modules unreachable)

### Objective
Fix the `governance-core` hyphen import, activate all 6 governance modules, and wire the human slot to a notification channel (Telegram).

### Skills Required
- `OMNIS:builder`, `OMNIS:qa`
- `governance-review`
- `systematic-debugging` (for import issues)

### Waves
1. **Fix hyphen import** — Rename `governance-core/` → `governance_core/`, update all imports
2. **Activate 3 blocked modules** — Human slot, decision log, action classifier
3. **Wire human slot** — Connect to Telegram notification for L3+ decisions
4. **Write governance tests** — At least 3 test files for governance modules

### Prohibitions
- Do NOT change governance decision logic without TORRE approval
- Do NOT wire to production Telegram without human auth

### Deliverables
- `reports/ABA4_GOVERNANCE_STATUS.md`
- All 6 governance modules importable
- Human slot functional (even if notification channel is mock)
- Governance test suite (3+ files)

### Validation
- `python -c "from src.governance_core.approvals.human_slot import HumanSlot; print('OK')"`
- `python -c "from src.governance_core.audit.decision_log import DecisionLog; print('OK')"`
- `python -c "from src.governance_core.permissions.action_classifier import classify_risk; print('OK')"`

---

## ABA 5 — KRATOS Live

**Status:** BLOCKED (B1 — human authorization required)
**Priority:** P0 (dashboard is the operator's window into OMNIS)

### Objective
Replace KRATOS mock data with real OMNIS health bridge data. The bridge file already exists at `~/.claude/state/kratos_health.json`.

### Skills Required
- `OMNIS:builder` (if authorized)
- `mission-control-product-owner`

### Waves
1. **Read bridge contract** — `reports/WAVE3_KRATOS_REALDATA.md` documents the format
2. **Modify KRATOS store.ts** — Replace hardcoded mock with fetch from bridge file
3. **Add fallback** — If bridge file missing, fall back to mock (graceful degradation)
4. **Test dashboard** — Verify components show real health data

### Prohibitions
- Do NOT start without explicit human: "pode mexer no KRATOS"
- Do NOT modify OMNIS runtime
- Do NOT remove mock fallback

### Deliverables
- `reports/ABA5_KRATOS_LIVE_STATUS.md`
- KRATOS PR with bridge integration
- Dashboard screenshot showing real data

### Validation
- KRATOS dashboard shows real component status from `omnis_health.json`
- Health score matches OMNIS health file
- Graceful fallback if bridge file deleted

---

## ABA 6 — Memory / Akasha

**Status:** READY
**Priority:** P2

### Objective
Document Obsidian dedup strategy, verify Akasha connectivity, and wire memory_lookup to actual retrieval.

### Skills Required
- `OMNIS:builder`
- `context-engineering`

### Waves
1. **Verify Akasha connectivity** — pgvector :5432, biblioteca_sabedoria DB
2. **Document Obsidian dedup** — Strategy for 38,661 files with 40-50% duplication
3. **Test memory_lookup** — `src/missions/memory_lookup.py` with real Akasha query
4. **Knowledge retrieval validation** — Query → relevant chunks → mission context

### Prohibitions
- Do NOT modify Obsidian vault
- Do NOT modify Akasha schema

### Deliverables
- `reports/ABA6_MEMORY_AKASHA_STATUS.md`
- Obsidian dedup strategy document
- memory_lookup validation results

### Validation
- `python -c "from src.missions.memory_lookup import lookup; print(lookup('test'))"` returns results
- Akasha responds to queries

---

## ABA 7 — Recovery / Self-Healing

**Status:** READY (partial — cleanup blocked by B3, B4)
**Priority:** P1

### Objective
Implement automated watchdog daemon, wire circuit breaker to mission execution, execute authorized cleanup (worktrees, branches, DEAD packages).

### Skills Required
- `OMNIS:builder`, `OMNIS:qa`
- `systematic-debugging`
- `operational-truth-engineer`

### Waves
1. **Implement watchdog daemon** — Polls health file every 60s, triggers self-healing on degrade
2. **Wire circuit breaker** — Mission steps that fail 3x trigger circuit breaker
3. **Execute cleanup** — Delete 7 stale worktrees, 4 dead branches (WITH HUMAN AUTH)
4. **Archive DEAD packages** — Move 15 DEAD packages to `_archived/` (WITH HUMAN AUTH)
5. **Unify checkpoint docs** — Document mission vs graph checkpoint split

### Prohibitions
- Do NOT delete worktrees without explicit authorization
- Do NOT delete branches without explicit authorization
- Do NOT modify recovery logic that passes 271 tests

### Deliverables
- `reports/ABA7_RECOVERY_STATUS.md`
- Watchdog daemon script
- Circuit breaker wired to at least 1 mission path
- Cleanup report (what was deleted/archived)

### Validation
- Watchdog detects health file change within 60s
- Circuit breaker trips after 3 simulated failures
- All 271 recovery tests still pass

---

## ABA Execution Order

```
Phase 5 kickoff:
  Day 1: ABA 4 (fix governance hyphen — unblocks immediately)
  Day 1: ABA 1 (runtime core — foundational)
  Day 2: ABA 3 (observability — depends on ABA 1 consumers)
  Day 2: ABA 2 (provider — can run parallel)
  Day 3: ABA 7 (recovery — cleanup needs auth)
  Day 3: ABA 6 (memory — lowest priority)
  Blocked: ABA 5 (KRATOS — waiting for human)
```
