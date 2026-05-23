# GLOBAL KRATOS TRUTH — Cockpit Reality Check

**Date:** 2026-05-22
**Mission:** GLOBAL EVALUATION — Wave 6
**Verdict:** KRATOS IS THEATER — 0% real data, 100% mock, bridge exists but unused

---

## 1. KRATOS Reality Matrix

| Widget / Feed | Data Source | Currently Shows | REAL? |
|---------------|------------|-----------------|-------|
| Dashboard health | `store.ts` hardcoded | Fake health status | 🔴 MOCK |
| Component status | `store.ts` hardcoded | Fake component list | 🔴 MOCK |
| Mission list | `store.ts` hardcoded | Fake mission data | 🔴 MOCK |
| Event stream | Not connected | Empty | 🔴 MOCK |
| Health score | `store.ts` hardcoded | Fake number | 🔴 MOCK |
| Runtime metrics | Not connected | Zero | 🔴 MOCK |
| Audit trail | Not connected | Empty | 🔴 MOCK |
| Checkpoint status | Not connected | Empty | 🔴 MOCK |
| **TOTAL** | | | **0/8 real** |

---

## 2. Bridge Status

| Component | Status | Detail |
|-----------|--------|--------|
| Bridge contract documented | ✅ YES | WAVE3_KRATOS_REALDATA.md |
| OMNIS-side writer | ✅ YES | wave2_kratos_bridge.py |
| Bridge file exists | ✅ YES | `~/.claude/state/kratos_health.json` |
| Bridge file format valid | ✅ YES | `{status, score, timestamp, components}` |
| KRATOS-side reader | 🔴 NO | store.ts still uses hardcoded data |
| Fallback to mock | 🔴 NO | Designed but not implemented |
| **Bridge readiness** | **60%** | OMNIS side complete, KRATOS side blocked |

---

## 3. What KRATOS Shows vs What's Real

```
KRATOS DASHBOARD          |  ACTUAL RUNTIME STATE
─────────────────────────|─────────────────────────
Health: ??? (mock)       |  Health: 0.67 (real)
Components: ??? (mock)   |  7 components (real)
Missions: ??? (mock)     |  1 mission + 1 checkpoint (real)
Events: ??? (mock)       |  10 channels, 0 consumers
Audit: ??? (mock)        |  1 entry in JSONL (real)
Metrics: ??? (mock)      |  12,394 entries (real)
```

**Every widget on KRATOS is a lie.** The real data exists and is verified. It's just not connected.

---

## 4. Why KRATOS Is Still Mock

| Blocker | Detail |
|---------|--------|
| Guardrail: "NUNCA tocar KRATOS" | CLAUDE.md absolute prohibition |
| Scope: external repo | `kratos-mission-control/` is a separate repo |
| Human decision pending | Lucas has not authorized the change |
| Bridge ready on OMNIS side | Data feed exists, format agreed, file written |

---

## 5. What Would Make KRATOS Real

### Step 1: Modify store.ts (30 min)
```typescript
// Current (mock):
const health = { status: 'healthy', score: 0.95, components: [...] };

// Target (real):
import { readFile } from 'fs/promises';
const data = JSON.parse(await readFile('~/.claude/state/kratos_health.json', 'utf-8'));
```

### Step 2: Add fallback (10 min)
```typescript
try {
  const data = await fetchRealHealth();
} catch {
  return mockFallback(); // Graceful degradation
}
```

### Step 3: Wire event stream (30 min)
Connect to Redis :6381 for real-time events.

### Step 4: Test (15 min)
Verify dashboard shows real data matching OMNIS health file.

**Total: ~1.5h. Blocker: human says "pode mexer no KRATOS."**

---

## 6. KRATOS Health Score

| Dimension | Score | Weight |
|-----------|-------|--------|
| Code quality | 0.80 | 0.20 |
| OMNIS-side bridge | 0.90 | 0.30 |
| KRATOS-side integration | 0.00 | 0.40 |
| Fallback robustness | 0.00 | 0.10 |
| **OVERALL** | **0.20** | |

---

## 7. Impact of Mock Dashboard

| Stakeholder | Impact |
|-------------|--------|
| Operator (Lucas) | Sees fiction — cannot trust dashboard |
| Developer (Claude) | Has real data but cannot display it |
| Auditor | No audit trail visible |
| Decision maker | Making decisions on fake data |

**This is the single highest-impact gap in the entire OMNIS ecosystem.**

---

## 8. Recommendation

**Priority: P0.** KRATOS is the operator's window into OMNIS. Every other ABA's work is invisible until KRATOS shows real data. The fix is simple (read a JSON file instead of hardcoded values) but requires breaking the "NUNCA tocar KRATOS" guardrail with explicit human authorization.

**Request:** Lucas, say "pode mexer no KRATOS" to unblock ABA 5.
