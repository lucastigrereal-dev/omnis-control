# TOWER GLOBAL DRIFTS — Consolidated Drift Registry

**Date:** 2026-05-22
**Source:** TOWER_DRIFT_MATRIX.md + TOWER_REALTIME_DRIFT.md
**Total:** 18 drifts (5 P0, 5 P1, 8 P2)

---

## P0 — Must Fix Now

| ID | Drift | Owner | Age | Detection |
|----|-------|-------|-----|-----------|
| D1 | KRATOS 100% mock data | ABA 5 | Since creation | store.ts analysis |
| D2 | governance-core hyphen breaks imports | ABA 4 | Autopilot 6H | ModuleNotFoundError |
| D3 | 4 test-to-source mismatches (v2 empty) | ABA 1 | Unknown | M3 drift classifier |
| D4 | CURRENT_STATE.md 9 commits behind | TORRE | 9 commits | git log vs doc |
| D5 | Redis EventBus has no consumers | ABA 1, 3 | Always | Redis XREAD |

---

## P1 — Fix This Week

| ID | Drift | Owner |
|----|-------|-------|
| D6 | ACTIVE_WORKTREES.md missing 3 worktrees | TORRE |
| D7 | Dual registry naming (JARVIS vs OMNIS) | TORRE |
| D8 | 15 DEAD packages in source tree | ABA 7 |
| D9 | No automated watchdog | ABA 7 |
| D10 | Provider not wired to missions | ABA 2 |

---

## P2 — Fix When Convenient

| ID | Drift | Owner |
|----|-------|-------|
| D11 | 40-50% Obsidian duplication | ABA 6 |
| D12 | 18 P1/P2 skills declared but unscaffolded | TORRE |
| D13 | 7 stale worktrees | ABA 7 |
| D14 | 4 dead branches | ABA 7 |
| D15 | configure_logging returns None | ABA 3 |
| D16 | 5 dead litellm imports | ABA 2 |
| D17 | ollama model hardcoded in 7 places | ABA 2 |
| D18 | Two separate checkpoint systems | ABA 1, 7 |

---

## Drift Resolution Progress

| Fixed | When | How |
|-------|------|-----|
| Redis EventBus dormant | Phase 4 W1 | Validated :6381, 121/121 tests |
| Health bridge never written | Phase 4 W2 | omnis_health.json created |
| Zero mission events | Phase 4 W4 | First event log + checkpoint |
| Zero governance audit | Phase 4 W7 | First audit entry written |
| Provider not importable | Phase 4 W8 | Verified import + fallback |

---

## Drift by ABA

| ABA | P0 | P1 | P2 | Total |
|-----|----|----|----|-------|
| ABA 1 | D3, D5 | — | D18 | 3 |
| ABA 2 | — | D10 | D16, D17 | 3 |
| ABA 3 | — | — | D15 | 1 |
| ABA 4 | D2 | — | — | 1 |
| ABA 5 | D1 | — | — | 1 |
| ABA 6 | — | — | D11 | 1 |
| ABA 7 | — | D8, D9 | D13, D14 | 4 |
| TORRE | D4 | D6, D7 | D12 | 4 |
