# TOWER DRIFT MATRIX

**Date:** 2026-05-22
**Authority:** TORRE CENTRAL
**Purpose:** Catalog all known drifts with severity classification and owner assignment

---

## Drift Classification

| Priority | Definition | Action Window |
|----------|-----------|---------------|
| **P0** | Blocks operational readiness or causes incorrect state | Fix immediately |
| **P1** | Degrades quality but doesn't block operations | Fix this week |
| **P2** | Cosmetic, cleanup, or optimization | Fix when convenient |

---

## Active Drifts

### P0 — Critical (5)

| # | Drift | Owner | Evidence | Fix |
|---|-------|-------|----------|-----|
| D1 | **KRATOS 100% mock data** | ABA 5 | `store.ts` hardcoded, dashboard shows fiction | Wire health bridge → KRATOS (needs human auth) |
| D2 | **`governance-core` hyphen breaks Python imports** | ABA 4 | `ModuleNotFoundError: No module named 'src.governance_core'` | Rename directory to `governance_core` |
| D3 | **4 CRITICAL test-to-source mismatches** | ABA 1 | Test files import from `v2/` dirs that are empty shells | Fix import paths or populate v2 modules |
| D4 | **CURRENT_STATE.md 9 commits behind HEAD** | TORRE | Claims state from 9 commits ago | Regenerate from current git log |
| D5 | **Redis EventBus has no consumers** | ABA 1 | 10 channels, 0 subscribers | Deploy omnis-consumer process |

### P1 — High (5)

| # | Drift | Owner | Evidence | Fix |
|---|-------|-------|----------|-----|
| D6 | **ACTIVE_WORKTREES.md missing 3 worktrees** | TORRE | `git worktree list` shows 3 more than doc | Update doc |
| D7 | **Dual registry naming (JARVIS vs OMNIS)** | TORRE | `~/.claude/registry/` JARVIS naming vs OMNIS runtime | Standardize naming |
| D8 | **15 DEAD packages in source tree** | ABA 7 | Phase 3 drift classifier: 12.8% DEAD | Archive or delete (with auth) |
| D9 | **No automated watchdog** | ABA 7 | Self-healing 5/5 manual but no daemon | Implement watchdog daemon |
| D10 | **Provider not wired to missions** | ABA 2 | Missions use default, not tier routing | Wire ProviderInterface to mission execution |

### P2 — Low (8)

| # | Drift | Owner | Evidence | Fix |
|---|-------|-------|----------|-----|
| D11 | **40-50% Obsidian duplication** | ABA 6 | 38,661 files, high duplication | Dedup strategy |
| D12 | **18 P1/P2 skills declared but unscaffolded** | TORRE | Registry claims active, no files on disk | Scaffold or remove from registry |
| D13 | **7 stale worktrees** | ABA 7 | Classified in Wave F, not deleted | Delete (with human auth) |
| D14 | **4 dead branches** | ABA 7 | Classified in Wave F | Delete (with human auth) |
| D15 | **`configure_logging` returns None** | ABA 3 | Known bug, non-blocking | Fix return path |
| D16 | **5 dead `from litellm import completion`** | ABA 2 | Autopilot finding | Remove dead imports |
| D17 | **ollama model name hardcoded in 7 places** | ABA 2 | `qwen2.5:7b` vs `qwen2.5-coder:7b` | Centralize model config |
| D18 | **Two separate checkpoint systems** | ABA 1 + 7 | Mission-level vs graph-level, not unified | Unify or document split |

---

## Drift by ABA

| ABA | P0 | P1 | P2 | Total |
|-----|----|----|----|-------|
| ABA 1 (Runtime) | D3, D5 | — | D18 | 3 |
| ABA 2 (Provider) | — | D10 | D16, D17 | 3 |
| ABA 3 (Observability) | — | — | D15 | 1 |
| ABA 4 (Governance) | D2 | — | — | 1 |
| ABA 5 (KRATOS) | D1 | — | — | 1 |
| ABA 6 (Memory) | — | — | D11 | 1 |
| ABA 7 (Recovery) | — | D8, D9 | D13, D14 | 4 |
| TORRE | D4 | D6, D7 | D12 | 4 |
| **TOTAL** | **5** | **5** | **8** | **18** |

---

## Drift Detection Cadence

| Frequency | Method | Owner |
|-----------|--------|-------|
| Every session start | Read CURRENT_STATE.md vs git log | TORRE |
| Every phase end | Run drift classifier (`MISSION3_DRIFT_CLASSIFIER.md` method) | ABA 1 |
| Weekly | Full registry audit | TORRE |
| On ABA completion | ABA self-report via `ABA<N>_*_STATUS.md` | ABA lead |

---

## Recently Fixed Drifts

| Drift | When | How |
|-------|------|-----|
| Redis EventBus dormant | Phase 4 Wave 1 | Validated Redis :6381, 121/121 tests |
| Health bridge never written | Phase 4 Wave 2 | `omnis_health.json` created, 7 components |
| Zero mission events on disk | Phase 4 Wave 4 | First event log + checkpoint written |
| Zero governance audit entries | Phase 4 Wave 7 | First `governance_audit.jsonl` entry |
| Provider interface not importable | Phase 4 Wave 8 | Verified import + fallback chain |
