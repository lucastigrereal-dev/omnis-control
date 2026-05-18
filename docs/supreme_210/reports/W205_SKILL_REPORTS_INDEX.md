# W205 — Skill Reports Index
# Status: DONE | 2026-05-17

## Summary
Indexed 17 project skills + 14 CCOS skills. `skill_reports/` directory is in .gitignore but does NOT exist on disk. No skill generates reports to this location.

---

## Skill Reports Directory

```
skill_reports/  → NOT PRESENT (in .gitignore line 26, but never created)
```

---

## Project Skills (skills/) — 17 skills

| Skill | Version | Status | Has Report Output? |
|---|---|---|---|
| `argos-bridge` | 1.0.0 | active | No |
| `create_30_day_content_calendar` | 1.0.0 | active | No |
| `create_instagram_carousel` | 1.0.0 | active | No |
| `create_sales_dm_sequence` | 1.0.0 | active | No |
| `crm-pipeline` | 1.0.0 | active | No |
| `export_content_batch_to_csv` | 1.0.0 | active | No |
| `generate_seogram_caption` | 1.0.0 | active | No |
| `jarvis-brain` | 1.0.0 | active | No |
| `jarvis-decide` | 1.0.0 | active | No |
| `jarvis-delegate` | 1.0.0 | active | No |
| `jarvis-guardrails` | 1.0.0 | active | No |
| `jarvis-memory-write` | 1.0.0 | active | No |
| `jarvis-morning` | 1.0.0 | active | No |
| `jarvis-router` | 1.0.0 | active | No |
| `revenue-tracker` | 1.0.0 | active | No |
| `skill-creator` | 1.0.0 | active | No |
| `video_to_content` | 1.0.0 | active | No |

**Structure per skill:** `SKILL.md` + `manifest.json` + `run.py`

---

## CCOS Skills (.claude/skills/) — 14 skills

| Skill | Purpose |
|---|---|
| `app-factory-api` | API contract builder |
| `app-factory-prd` | PRD generator |
| `app-factory-schema` | DB schema planner |
| `docs-release` | Release documentation |
| `feature-scaffolder` | Feature scaffolding |
| `full-suite-gate` | Full test suite gate |
| `merge-wave` | Wave merge orchestration |
| `qa-merge-gate` | QA merge gate |
| `refactor-guardian` | Refactor safety checks |
| `repo-architect` | Repository architecture |
| `scope-lock` | Scope locking |
| `spawn-worktrees` | Git worktree management |
| `targeted-test` | Targeted test runner |
| `wave-plan` | Wave planning |

**Structure per skill:** `SKILL.md` only

---

## Skill Reports Gap Analysis

| What | Status |
|---|---|
| `skill_reports/` directory | MISSING — in .gitignore but never created |
| Skills with `--report` mode | None (verified all run.py files) |
| Skills writing to `skill_reports/` | None |
| Skills generating JSON/CSV/MD output | Some, but go to `data/exports/` or `data/` |

---

## Recommendations

1. **LOW:** Either create `skill_reports/` with a `.gitkeep` or remove it from .gitignore
2. **LOW:** If skills should generate reports, add `--report` flag pattern to `skill-creator` template
