# TOWER GLOBAL BLOCKERS — Consolidated Blocker Registry

**Date:** 2026-05-22
**Source:** TOWER_BLOCKERS.md + TOWER_REALTIME_BLOCKERS.md
**Total:** 5 BLOCKED, 5 WARNINGS, 7 READY

---

## BLOCKED (5)

| ID | Blocker | ABA | Owner | Action |
|----|---------|-----|-------|--------|
| B1 | KRATOS guardrail | ABA 5 | Lucas | "Pode mexer no KRATOS" |
| B2 | ANTHROPIC_API_KEY | ABA 2 | Lucas | Set env var |
| B3 | Worktree deletion auth | ABA 7 | Lucas | Authorize cleanup |
| B4 | Dead branch deletion auth | ABA 7 | Lucas | Authorize deletion |
| B5 | governance-core rename | ABA 4 | TORRE | Rename directory |

---

## READY_WITH_WARNINGS (5)

| ID | Warning | ABA | Mitigation |
|----|---------|-----|------------|
| W1 | Redis consumers not deployed | 1, 3 | Deploy as ABA 1 Wave 1 |
| W2 | CURRENT_STATE.md stale | TORRE | Regenerate each cycle |
| W3 | 15 DEAD packages | 7 | Classify, don't block |
| W4 | Obsidian 40-50% dup | 6 | Document strategy |
| W5 | Two checkpoint systems | 1, 7 | Document split |

---

## READY (7)

| ABA | Entry Point | Dependencies Met? |
|-----|------------|-------------------|
| ABA 1 | Deploy Redis consumer | YES |
| ABA 2 | Wire provider (ollama) | YES |
| ABA 3 | Activate EventBus consumers | After ABA 1 |
| ABA 4 | Rename directory | TORRE authorized |
| ABA 5 | Read bridge contract | NO (B1) |
| ABA 6 | Verify Akasha | YES |
| ABA 7 | Implement watchdog | YES (partial) |

---

## Blocker Resolution Queue

| Order | Blocker | Resolved By | Unblocks |
|-------|---------|------------|----------|
| 1 | B5 (hyphen rename) | TORRE action | ABA 4 |
| 2 | B1 (KRATOS auth) | Lucas decision | ABA 5 |
| 3 | B2 (API key) | Lucas action | ABA 2 (full) |
| 4 | B3 (worktrees) | Lucas decision | ABA 7 (cleanup) |
| 5 | B4 (branches) | Lucas decision | ABA 7 (cleanup) |

---

## Blocker Age

| Blocker | Discovered | Age |
|---------|-----------|-----|
| B1 | Project creation | Permanent (by design) |
| B2 | Autopilot 6H | ~1 day |
| B3 | Autopilot 6H | ~1 day |
| B4 | Autopilot 6H | ~1 day |
| B5 | Phase 4 Wave 7 | ~hours |
