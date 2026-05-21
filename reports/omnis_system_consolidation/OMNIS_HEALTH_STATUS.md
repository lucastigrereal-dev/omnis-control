# OMNIS Health Status

**Date:** 2026-05-21  
**Endpoint:** `http://localhost:8700/health`  
**Status:** ✅ **ALIVE**

---

## Summary

| Metric | Value |
|---|---|
| Total Skills | 48 |
| Healthy | 47 (97.9%) |
| Stale | 0 |
| Missing Metadata | 0 |
| Empty Dir (_archived) | 1 |
| Unused >30 days | 8 Jarvis skills (last used 2026-04-29) |

## Healthy Skills (47)

All 47 registered skills report `healthy` status. Most recently used between 2026-05-19 and 2026-05-20.

### Most Active (2026-05-20)
architect-omnis, auditor, brainstorming, banner-design, brand, builder, design, design-system, execution-runner, guardian, humanizer, merge-gate, orchestrator, qa, refactor, registry, scaffolder, schema-planner, slides, systematic-debugging, ui-styling, ui-ux-pro-max, using-superpowers, qmd

### Last Used 2026-05-19
architect, cost-analyst, git_guardian, integration-architect, memory-architect, mission-control-mapper, qa-guard, reviewer, roadmap-planner, skill-router, tester, webhook-guardian, workflow-auto-fixer, workflow-validator, workflow-versioning

### Stale / Unused >30 days (8 skills — Jarvis core + skill-creator)
| Skill | Last Used | Note |
|---|---|---|
| jarvis-brain | 2026-04-29 | 22 days idle — Jarvis v1 pipeline |
| jarvis-decide | 2026-04-29 | 22 days idle — Jarvis v1 pipeline |
| jarvis-delegate | 2026-04-29 | 22 days idle — Jarvis v1 pipeline |
| jarvis-guardrails | 2026-04-29 | 22 days idle — Jarvis v1 pipeline |
| jarvis-memory-write | 2026-04-29 | 22 days idle — Jarvis v1 pipeline |
| jarvis-morning | 2026-04-29 | 22 days idle — Jarvis v1 pipeline |
| jarvis-router | 2026-04-29 | 22 days idle — Jarvis v1 pipeline |
| skill-creator | 2026-04-29 | 22 days idle |

## Empty Directory
- `_archived` — placeholder for archived skills. No impact.

## Health Service Info
- Endpoint: `GET http://localhost:8700/health`
- Format: JSON with `status`, `total_skills`, `healthy`, `stale`, `missing_metadata`, `empty_dir`, and per-skill array
- No `POST`, `PUT`, or `DELETE` endpoints observed on port 8700
- No `/metrics` or `/info` endpoints detected

## Gaps
1. No `/metrics` endpoint for detailed observability
2. No `/info` endpoint for version/metadata
3. No `/ready` (readiness) endpoint separate from `/health` (liveness)
4. Health service does not track KRATOS or external service status
5. 8 skills idle for 22+ days — potential dead code

## Verdict
**OMNIS health service is operational.** 47/48 skills healthy, 0 stale, 0 missing metadata. The Jarvis v1 skills are preserved but idle since the OMNIS pipeline replaced them.
