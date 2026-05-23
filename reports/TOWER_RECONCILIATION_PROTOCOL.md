# TOWER RECONCILIATION PROTOCOL

**Date:** 2026-05-22
**Authority:** TORRE CENTRAL
**Purpose:** How the Tower receives ABA outputs, detects conflicts, and maintains coherence

---

## 1. ABA Output Format (Standard)

Every ABA must produce a status report at:

```
reports/ABA<N>_<ABA_NAME>_STATUS.md
```

### Required Sections

```markdown
# ABA<N> — <Name> Status Report

**Date:** ISO-8601
**ABA Lead:** <session/agent id>
**Status:** EXECUTING | COMPLETE | BLOCKED | FAILED

## Waves Executed
| # | Wave | Status | Tests | Notes |
|---|------|--------|-------|-------|

## Files Changed
| File | Action | Rationale |
|------|--------|-----------|

## Test Results
| Suite | Passed | Failed | Notes |
|-------|--------|--------|-------|

## New Drifts Detected
| Drift | Severity | Detail |
|-------|----------|--------|

## Blockers Hit
| Blocker | Resolution |
|---------|------------|

## Deliverables Produced
| File | Status |
|------|--------|

## Cross-ABA Impacts
| ABA Affected | Impact | Mitigation |
|-------------|--------|------------|

## Next Steps
1. ...
```

---

## 2. Receipt & Ingestion

When an ABA completes and drops its report:

1. **TORRE reads the report** within the same session or next session
2. **TORRE validates against ABA briefing** — did the ABA deliver what was asked?
3. **TORRE checks for conflicts** — does this ABA's output conflict with another ABA?
4. **TORRE updates master state** — `TOWER_MASTER_STATE.md` updated
5. **TORRE updates drift matrix** — new drifts added, fixed drifts moved to "Recently Fixed"
6. **TORRE updates blockers** — resolved blockers cleared, new ones added
7. **TORRE generates next command** — `TOWER_NEXT_ACTIONS.md` updated

---

## 3. Conflict Detection Rules

TORRE checks these conflicts when ingesting ABA reports:

| Conflict Type | Detection Rule | Example |
|--------------|----------------|---------|
| **File collision** | Two ABAs modified the same file | ABA 1 and ABA 7 both changed `src/missions/runtime.py` |
| **Schema drift** | ABA changed a model that another ABA depends on | ABA 1 changed `CanonicalEnvelope` format, ABA 3 reads it |
| **Authority violation** | ABA touched a domain it doesn't own | ABA 3 modified `src/governance/` |
| **Test regression** | ABA's changes broke another ABA's tests | ABA 2 provider change broke ABA 1 mission tests |
| **Duplicate work** | Two ABAs built the same thing | ABA 3 and ABA 7 both built a watchdog |
| **Contradictory state** | ABA reports conflict with observed reality | ABA claims "all tests pass" but `git status` shows dirty |

---

## 4. Conflict Resolution

```
Conflict detected
  → TORRE logs it in TOWER_DRIFT_MATRIX.md
  → TORRE determines: real or perceived?
    → Perceived: document why it's not a conflict
    → Real: determine severity
      → P2 (cosmetic): note, continue
      → P1 (degraded): pause affected ABA, fix
      → P0 (blocking): pause ALL ABAs, escalate to human
  → TORRE updates TOWER_BLOCKERS.md
  → TORRE generates reconciliation task for next session
```

---

## 5. Multi-ABA Coordination

When two ABAs need to coordinate (e.g., ABA 1 builds consumer, ABA 3 subscribes):

1. **ABA 1 completes first** — drops report with "Cross-ABA Impacts: ABA 3 can now subscribe to channel X"
2. **TORRE reads ABA 1 report** — updates ABA 3 briefing with new information
3. **ABA 3 starts** — reads updated briefing, uses ABA 1's output
4. **No direct ABA-to-ABA handoff** — TORRE is always the intermediary

---

## 6. Reconciliation Cadence

| Trigger | Action |
|---------|--------|
| ABA drops report | TORRE ingests within same session |
| 2+ ABAs complete | TORRE runs full reconciliation |
| Session boundary | TORRE writes RECOVERY_CHECKPOINT with current ABA states |
| Conflict detected | Immediate reconciliation |
| Human decision received | Update blockers, unblock affected ABAs |

---

## 7. State Consistency Checks

Before declaring any phase complete, TORRE verifies:

```
[ ] All ABA reports received match ABA count in briefing
[ ] No file modified by two different ABAs without coordination
[ ] Test suite passes for all changed modules
[ ] Drift matrix updated (new drifts added, fixed drifts archived)
[ ] Blocker list reconciled (resolved vs new)
[ ] Master state reflects current reality (not stale)
[ ] No ABA touched KRATOS without authorization
[ ] No ABA read .env or secrets
[ ] No destructive actions without human approval
```

---

## 8. Reconciliation Report Template

After each reconciliation cycle, TORRE appends to:

```
reports/TOWER_RECONCILIATION_LOG.md
```

```markdown
## Reconciliation Cycle — <date>

### ABAs Completed This Cycle
- ABA<N>: <status> — <key result>

### Conflicts Detected
- None / <list>

### State Changes
- Drifts fixed: <count>
- Drifts added: <count>
- Blockers resolved: <count>
- Blockers added: <count>

### Master State Updated
- Overall score: <old> → <new>
- Last completed phase: <phase>

### Next ABA to Execute
- ABA<N> — <reason>
```
