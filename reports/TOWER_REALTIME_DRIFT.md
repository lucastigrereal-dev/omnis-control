# TOWER REALTIME DRIFT — Detection Engine

**Date:** 2026-05-22
**Cycle:** REALTIME #1
**Active Drifts:** 18 (5 P0, 5 P1, 8 P2)
**New Since Last Cycle:** 0

---

## Drift Detection Engine Status

| Component | Status |
|-----------|--------|
| Detection algorithm | ACTIVE |
| Classification engine | ACTIVE (P0/P1/P2) |
| Auto-detection | PASSIVE (manual scan this cycle) |
| Cross-ABA drift check | CLEAR |
| Source of truth validation | PARTIAL (4 canonical files missing) |

---

## P0 — Critical Drifts (5)

| # | Drift | ABAs Affected | Detection Method | Age |
|---|-------|--------------|-----------------|-----|
| D1 | KRATOS 100% mock data | ABA 5 | Phase 3 M4 — store.ts analysis | Since creation |
| D2 | `governance-core` hyphen breaks Python imports | ABA 4 | Phase 4 Wave 7 — ModuleNotFoundError | Autopilot 6H |
| D3 | 4 test-to-source mismatches (v2 dirs empty) | ABA 1 | Phase 3 M3 — drift classifier scan | Unknown |
| D4 | CURRENT_STATE.md 9 commits behind HEAD | TORRE | Phase 3 M4 — git log vs doc diff | 9 commits |
| D5 | Redis EventBus has no consumers | ABA 1, 3 | Phase 4 Wave 1 — Redis XREAD check | Always |

---

## P1 — High Drifts (5)

| # | Drift | ABAs Affected | Detection Method | Age |
|---|-------|--------------|-----------------|-----|
| D6 | ACTIVE_WORKTREES.md missing 3 worktrees | TORRE | Phase 3 M4 — `git worktree list` vs doc | Unknown |
| D7 | Dual registry naming (JARVIS vs OMNIS) | TORRE | Phase 3 M2, M3 — registry audit | Always |
| D8 | 15 DEAD packages in source tree | ABA 7 | Phase 3 M3 — import graph analysis | Months |
| D9 | No automated watchdog | ABA 7 | Phase 4 Wave 9 — self-healing 5/5 manual | Since design |
| D10 | Provider not wired to missions | ABA 2 | Phase 4 Wave 8 — routing not connected | Since creation |

---

## P2 — Low Drifts (8)

| # | Drift | ABAs Affected |
|---|-------|--------------|
| D11 | 40-50% Obsidian duplication | ABA 6 |
| D12 | 18 P1/P2 skills declared but unscaffolded | TORRE |
| D13 | 7 stale worktrees | ABA 7 |
| D14 | 4 dead branches | ABA 7 |
| D15 | `configure_logging` returns None | ABA 3 |
| D16 | 5 dead `from litellm import completion` | ABA 2 |
| D17 | ollama model name hardcoded in 7 places | ABA 2 |
| D18 | Two separate checkpoint systems | ABA 1, 7 |

---

## Cross-ABA Drift Analysis

| ABA Pair | Drift Risk | Status |
|----------|-----------|--------|
| ABA 1 ↔ ABA 3 | Shared Redis dependency — both need consumers | ALIGNED |
| ABA 1 ↔ ABA 7 | Two checkpoint systems may diverge (D18) | MONITOR |
| ABA 2 ↔ ABA 1 | Provider routing not wired to mission execution | DRIFT (D10) |
| ABA 4 ↔ TORRE | governance vs governance-core split | DRIFT (D2) |
| ABA 5 ↔ ABA 3 | Health bridge format agreed (WAVE3) | ALIGNED |
| ABA 6 ↔ ABA 1 | memory_lookup owned by ABA 1, integrated by ABA 6 | MONITOR |

---

## Duplicated Runtime Detection

| Check | Result |
|-------|--------|
| Duplicated execution graphs? | NO — single source in `src/execution_graph/` |
| Duplicated mission models? | NO — single source in `src/missions/models.py` |
| Duplicated event bus? | NO — single source in `src/omnis_bus/` |
| Duplicated health bridge? | NO — single source in `src/observability/health_file.py` |
| Duplicated governance? | PARTIAL — two dirs (governance/ + governance-core/) but one functional |

---

## Mock Residual Detection

| Component | Mock Status | Detection |
|-----------|------------|-----------|
| KRATOS dashboard | 100% mock | `kratos-mission-control/backend/app/store.ts` hardcoded |
| Live cockpit collectors | 8/9 return zero | Phase 3 M4 |
| Provider fallback | Mock when API key missing | Designed, not implemented |
| Human slot notification | Not wired | Mock only |

---

## Drift Velocity

| Period | New Drifts | Fixed Drifts | Net |
|--------|-----------|-------------|-----|
| Phase 3 → Phase 4 | +5 (D1-D5 classified) | -3 (Redis, Health, Audit activated) | +2 |
| Phase 4 → Now | 0 | 0 | 0 |
| **Trend** | **STABLE** | | |

---

## Auto-Detection Rules (for future cycles)

```
IF git log HEAD != CURRENT_STATE.md HEAD → FLAG P0 drift
IF module import fails → FLAG P0 drift (check hyphen/underscore)
IF test file imports from non-existent module → FLAG P0 drift
IF docker ps shows no Redis consumer → FLAG P1 drift
IF `git worktree list` count != ACTIVE_WORKTREES.md count → FLAG P1 drift
IF KRATOS store.ts contains hardcoded values → FLAG P0 drift
IF health_file shows score < 0.7 → FLAG P1 drift
IF two modules export same class name → FLAG P1 drift (duplication)
```
