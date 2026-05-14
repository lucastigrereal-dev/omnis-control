# CCOS Apply to Wave 7B — Plan

**Status:** Ready (awaiting Wave 7B execution authorization)  
**Date:** 2026-05-14

## Goal
Use CCOS minimal infrastructure to execute Wave 7B P37-P42 faster and safer.

## Approach
Execute Wave 7B SEQUENTIALLY (not parallel — first run with CCOS should be single-squad).

### Why sequential first
- P37-P42 have dependencies (P40 depends on P35, P42 depends on P35+P34+P37)
- Validating CCOS on 1 track before going parallel is safer
- First execution is the CCOS pilot — measure, then scale

## Phase execution plan

### P37 — War Room Runtime Bridge (CCOS pilot)
- **Skills used:** targeted-test, full-suite-gate
- **Before code:** scope-lock (define allowed paths)
- **After code:** targeted-test, import-guard
- **After commit:** full-suite-gate
- **Subagents:** architecture-auditor (before), test-guardian (after), documentation-scribe (report)

### P38 — Skill Router Real Bridge
- **Skills used:** targeted-test, full-suite-gate
- **Subagents:** security-guardian (catalog access), test-guardian
- **Note:** No real ks execution — catalog-only, dry-run

### P39 — Approval Runtime
- **Skills used:** targeted-test, full-suite-gate
- **Subagents:** architecture-auditor, security-guardian, test-guardian
- **Risk:** Medium — approval logic must be correct

### P40 — Akasha Event Sink
- **Skills used:** targeted-test, full-suite-gate
- **Subagents:** architecture-auditor, security-guardian
- **Note:** File-backed + mock only, no pgvector connection

### P41 — Telegram/WA Control Planning
- **Skills used:** none (docs only)
- **Subagents:** documentation-scribe, security-guardian
- **Note:** Zero code — design docs only

### P42 — Observability, Rollback & Audit
- **Skills used:** targeted-test, full-suite-gate, merge-wave
- **Subagents:** all 4
- **Note:** Consolidation phase — touches the most modules

## What CCOS should prevent
- Editing files outside scope
- Skipping tests before commit
- Push without authorization
- Secret leakage
- Working tree contamination

## Metrics to track
- Time per phase (P37-P42)
- Test failures caught by hooks vs. caught later
- Scope violations prevented
- Handoff quality (did next squad understand context?)

## When to expand CCOS
After Wave 7B is complete and merged:
- If CCOS prevented at least 2 issues → expand to CCOS-02 (more skills, parallel ready)
- If CCOS was friction without benefit → simplify, remove hooks that didn't help
- If Wave 7B went smoothly → CCOS-02 enables first parallel wave (Onda 8A)
