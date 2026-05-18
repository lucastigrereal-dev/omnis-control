# Memory Reuse Stress Test Report

**Date:** 2026-05-18
**Branch:** feature/omnis-5waves-runtime-supreme
**Task:** F07

## Objective
Validate that OMNIS can load learnings from previous missions, find relevant learnings for a new mission via keyword search, and produce a structured reuse report — without relying on embeddings or external vector databases.

## New Modules

| Module | Purpose |
|---|---|
| `src/memory/learning_reuse.py` | Load JSONL learnings, keyword search, build reuse report |
| `src/memory/learning_sources.py` | Cite and validate provenance of learning records |

## Test Coverage

| Test | Result |
|---|---|
| load_learnings on real _learnings.jsonl | PASS |
| find_relevant returns list | PASS |
| find_relevant filters by keyword | PASS |
| find_relevant with empty topic | PASS |
| unproven source detected | PASS |
| validate_source with mission_id | PASS |
| validate_source with source_file | PASS |
| reuse_report has required keys | PASS |
| A/B comparison Águas → Brotas | PASS |
| cite() formatting | PASS |
| cite() unknown source | PASS |

Total: 11 tests, all pass.

## Simulation: Águas de São Pedro → Brotas

Mission A (Águas de São Pedro) had 5 learnings about hotéis, CTAs, carrosséis, and CPM.
4 of those 5 learnings (80%) were directly applicable to Mission B (Brotas) with no or minor modification.

Key reused learnings:
- CTAs "responde essa DM" → 3x more conversion
- Carrosséis com dados → 40% more saves
- CPM comparativo (R$0,15 vs R$15) → closes hotel deals faster

## Gaps & Next Steps
See `missions/memory_reuse_stress_test/improvement_report.md` for full gap analysis.

Top priority: add recency weighting and optional embedding-based fallback.

## Files
- `src/memory/learning_reuse.py`
- `src/memory/learning_sources.py`
- `tests/memory/test_learning_reuse.py`
- `missions/memory_reuse_stress_test/reused_context.md`
- `missions/memory_reuse_stress_test/learning_sources.json`
- `missions/memory_reuse_stress_test/decision_log.md`
- `missions/memory_reuse_stress_test/improvement_report.md`
