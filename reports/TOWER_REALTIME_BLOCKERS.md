# TOWER REALTIME BLOCKERS — Centralized Engine

**Date:** 2026-05-22
**Cycle:** REALTIME #1
**Active Blockers:** 5 BLOCKED, 5 WARNINGS

---

## Blocker Classification Engine

| Component | Status |
|-----------|--------|
| Classification algorithm | ACTIVE (BLOCKED/READY_WITH_WARNINGS/READY) |
| Auto-detection | PASSIVE |
| Owner assignment | COMPLETE |
| Dependency mapping | COMPLETE |
| Resolution tracking | ACTIVE |

---

## BLOCKED (5)

### B1 — KRATOS Guardrail
| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Blocks** | ABA 5 (entirely) |
| **Owner** | Lucas |
| **Action Required** | Say "pode mexer no KRATOS" |
| **Impact** | Dashboard stays 100% mock |
| **Detection** | CLAUDE.md guardrail: "NUNCA tocar KRATOS" |
| **Age** | Since project creation |
| **Resolution Path** | Human overrides guardrail for ABA 5 scope only |

### B2 — ANTHROPIC_API_KEY
| Field | Value |
|-------|-------|
| **Priority** | P1 |
| **Blocks** | ABA 2 (cloud fallback) |
| **Owner** | Lucas |
| **Action Required** | Set `ANTHROPIC_API_KEY` in system env |
| **Impact** | Anthropic tier unavailable; ollama-only for all L3+ operations |
| **Detection** | Autopilot 6H Wave E |
| **Age** | Since autopilot |

### B3 — Worktree Deletion Authorization
| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Blocks** | ABA 7 (cleanup wave) |
| **Owner** | Lucas |
| **Action Required** | Authorize `git worktree remove` on 7 worktrees |
| **Impact** | 7 stale worktrees remain |
| **Detection** | Autopilot 6H Wave F |
| **Age** | Since autopilot |

### B4 — Dead Branch Deletion Authorization
| Field | Value |
|-------|-------|
| **Priority** | P2 |
| **Blocks** | ABA 7 (cleanup wave) |
| **Owner** | Lucas |
| **Action Required** | Authorize `git branch -D` on 4 branches |
| **Impact** | 4 dead branches remain |
| **Detection** | Autopilot 6H Wave F |
| **Age** | Since autopilot |

### B5 — governance-core Hyphen Rename
| Field | Value |
|-------|-------|
| **Priority** | P0 |
| **Blocks** | ABA 4 (entirely) |
| **Owner** | TORRE (can resolve directly) |
| **Action Required** | Rename `governance-core/` → `governance_core/` |
| **Impact** | 3/6 governance modules unreachable |
| **Detection** | Phase 4 Wave 7 — `ModuleNotFoundError` |
| **Age** | Autopilot 6H (created with hyphen) |
| **Resolution Path** | TORRE executes rename (safe, reversible, documented) |

---

## READY_WITH_WARNINGS (5)

| # | Warning | ABA | Mitigation |
|---|---------|-----|------------|
| W1 | Redis consumers not deployed | ABA 1, 3 | Deploy as first ABA 1 wave |
| W2 | CURRENT_STATE.md stale | TORRE | Regenerate at ABA start |
| W3 | 15 DEAD packages | ABA 7 | Classify, don't block |
| W4 | Obsidian 40-50% dup | ABA 6 | Document strategy first |
| W5 | Two checkpoint systems | ABA 1, 7 | Document split, unify later |

---

## READY (7 ABA entry points)

| ABA | Entry Point | Dependencies Met? |
|-----|------------|-------------------|
| ABA 1 | Deploy Redis consumer | Yes |
| ABA 2 | Wire provider (ollama tier only) | Yes (partial) |
| ABA 3 | Activate EventBus consumers | Yes |
| ABA 4 | Rename directory | Yes (TORRE authorized) |
| ABA 5 | Read bridge contract | NO (B1) |
| ABA 6 | Verify Akasha connectivity | Yes |
| ABA 7 | Implement watchdog | Yes (cleanup excluded) |

---

## Blocker Dependency Graph

```
B5 (governance hyphen) ──→ ABA 4 blocked
B1 (KRATOS guardrail)  ──→ ABA 5 blocked
B2 (ANTHROPIC_KEY)     ──→ ABA 2 partial
B3 (worktree auth)     ──→ ABA 7 cleanup blocked
B4 (branch auth)       ──→ ABA 7 cleanup blocked

Resolving B5 unblocks ABA 4 immediately.
All other blockers require human action.
```

---

## Blocker Resolution Velocity

| Period | Resolved | Added | Net |
|--------|---------|-------|-----|
| Autopilot 6H | — | B1-B4 identified | +4 |
| Phase 4 | — | B5 discovered | +1 |
| Now | 0 | 0 | 0 |
| **Total open** | | | **5** |

---

## Auto-Detection Rules

```
IF import fails with ModuleNotFoundError AND dir has hyphen → FLAG B5
IF store.ts/js contains hardcoded mock data → FLAG B1
IF os.environ.get('ANTHROPIC_API_KEY') is None → FLAG B2
IF `git worktree list` > ACTIVE_WORKTREES.md count → FLAG B3
IF `git branch --merged` includes branches not in plan → FLAG B4
```
