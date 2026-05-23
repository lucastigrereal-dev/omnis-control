# TOWER BLOCKERS

**Date:** 2026-05-22
**Authority:** TORRE CENTRAL
**Purpose:** Separate real blockers from warnings, classify each, assign owners

---

## Classification

| Status | Definition |
|--------|-----------|
| **BLOCKED** | Cannot proceed — external dependency or human decision required |
| **READY_WITH_WARNINGS** | Can proceed but has known issues |
| **READY** | Clear to execute |

---

## BLOCKED (5)

These require human action before the ABA can start.

| # | Blocker | ABA | What's Blocked | Required Action | Who |
|---|---------|-----|----------------|-----------------|-----|
| B1 | **KRATOS guardrail** | ABA 5 | Dashboard real data sync | Human says "pode mexer no KRATOS" | Lucas |
| B2 | **ANTHROPIC_API_KEY not set** | ABA 2 | Cloud provider fallback | Set env var in system or .env | Lucas |
| B3 | **Worktree deletion auth** | ABA 7 | Cleanup of 7 stale worktrees | Human authorizes `git worktree remove` | Lucas |
| B4 | **Dead branch deletion auth** | ABA 7 | Cleanup of 4 dead branches | Human authorizes `git branch -D` | Lucas |
| B5 | **`governance-core` rename** | ABA 4 | 3 governance modules unreachable | Rename `governance-core/` → `governance_core/` | TORRE (L3 — needs approval) |

---

## READY_WITH_WARNINGS (5)

These can start but have known issues to address during execution.

| # | Warning | ABA | Impact | Mitigation |
|---|---------|-----|--------|------------|
| W1 | **Redis consumers not deployed** | ABA 1 | EventBus write-only, no streaming | Deploy consumer as first task of ABA 1 |
| W2 | **CURRENT_STATE.md stale** | TORRE | Docs reference wrong state | Regenerate at start of each ABA |
| W3 | **15 DEAD packages** | ABA 7 | Code bloat, 12.8% dead weight | Classify before delete, don't block on cleanup |
| W4 | **Obsidian 40-50% duplication** | ABA 6 | Knowledge fragmentation | Document dedup strategy, don't block on execution |
| W5 | **Two checkpoint systems** | ABA 1+7 | Mission vs graph checkpoints not unified | Document split, unify later |

---

## READY (7)

These ABAs can execute immediately with no blockers.

| # | ABA | Status | First Task |
|---|-----|--------|------------|
| R1 | **ABA 1 — Runtime Core** | READY | Deploy Redis consumer, complete mission lifecycle |
| R2 | **ABA 3 — Observability** | READY | Activate EventBus layer, wire dashboard collectors |
| R3 | **ABA 6 — Memory/Akasha** | READY | Document Obsidian dedup strategy |
| R4 | **ABA 7 — Recovery** | READY (partial) | Implement watchdog daemon (cleanup blocked) |
| R5 | **ABA 2 — Provider** | READY_WITH_WARNINGS | Wire provider to missions (fallback blocked by B2) |
| R6 | **ABA 4 — Governance** | BLOCKED (B5) | Fix hyphen import first, then activate 3 modules |
| R7 | **ABA 5 — KRATOS** | BLOCKED (B1) | Cannot start without human authorization |

---

## Blockers vs Warnings — Decision Tree

```
Is human action required?
  YES → BLOCKED (report to operator)
  NO  → Can the ABA start without fixing this?
    YES → READY_WITH_WARNINGS (start, fix in parallel)
    NO  → Is it a P0 drift?
      YES → Fix before ABA start
      NO  → READY (address during ABA execution)
```

---

## Next Blocker to Resolve

**B5 — `governance-core` rename** — This is the only blocker TORRE can resolve directly (L3 — needs human confirmation per authority matrix, but is a safe rename). All other blockers require Lucas explicitly.

Recommendation: Ask Lucas for batch approval of B1-B4 + B5 in a single human-slot message.
