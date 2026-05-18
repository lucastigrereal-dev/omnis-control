# W201 — Runtime Paths Audit
# Status: DONE | 2026-05-17

## Summary
Audit complete. 3 classes of issues identified. No deletions performed.

---

## Finding 1: SYSTEMIC — `~/omnis-control` vs `~/omnis-maintenance` mismatch

**Severity:** HIGH
**Impact:** All runtime paths reference old project name.

The project was renamed/moved from `omnis-control` to `omnis-maintenance`, but **42+ files** still reference `~/omnis-control`:

| Module | Files Affected | Example |
|---|---|---|
| `src/cli.py` | 10 refs | `PATHS_YAML = os.path.expanduser("~/omnis-control/config/paths.yaml")` |
| `src/content_queue/` | 3 refs | `QUEUE_PATH = os.path.expanduser("~/omnis-control/data/content_queue.jsonl")` |
| `src/caption_approval/` | 3 refs | `TEMPLATES_PATH = os.path.expanduser("~/omnis-control/data/caption_templates.json")` |
| `src/checkers/` | 17 refs | `CONFIG_PATH = os.path.expanduser("~/omnis-control/config/paths.yaml")` |
| `src/metrics/store.py` | 1 ref | `base_dir = os.path.expanduser("~/omnis-control/data/metrics_spine")` |
| `src/missions/repository.py` | 1 ref | `base_dir = os.path.expanduser("~/omnis-control/data/missions")` |
| `config/paths.yaml` | 6 refs | `claude_skills_path: ~/omnis-control/skills` |
| `tests/` | 18+ refs | `CONTROL_DIR = os.path.expanduser("~/omnis-control")` |

**Root cause:** `config/paths.yaml` has no `control_root` key. Every module hardcodes its own path.

---

## Finding 2: HARDCODED — Windows absolute paths in security guards

**Severity:** LOW (security-by-design, but user-specific)

| File | Line | Path | Purpose |
|---|---|---|---|
| `src/control_tower/risk.py` | 36 | `C:\\Users\\lucas\\.kratos` | Block KRATOS interference |
| `src/skill_execution/permission_gate.py` | 26 | `C:\\Windows\\` | Block system dir access |

These are legitimate security features but are **Lucas-specific** and won't transfer to other operators.

---

## Finding 3: MISSING — `control_root` not centralized

**Severity:** MEDIUM

`config/paths.yaml` exists but contains no `control_root` key. Every module independently resolves `~/omnis-control`. This makes renaming/moving the project impossible without touching 42+ files.

Recommended: add `control_root: ~/omnis-maintenance` to `paths.yaml` and centralize all path resolution through one helper.

---

## Top-level directory inventory

```
omnis-maintenance/
  .claude/          — agents, hooks, rules, scopes, skills (CCOS infra)
  config/           — YAML configs (paths, sectors, roles, connectors...)
  data/             — runtime data (app_factory, missions, metrics_spine...)
  docs/             — documentation + supreme_210 reports
  migrations/       — DB migrations
  reports/          — runtime logs (ccos/*.log)
  schemas/          — JSON/YAML schemas
  scripts/          — utility scripts + archive
  skills/           — 17 Jarvis skills
  src/              — 70+ source modules
  tests/            — 80+ test modules
  workflows/        — n8n workflows
```

No directories with suspicious/broken Unicode characters found at scan time.
No `.test_tmp/`, `.tmp_pytest/` directories present on disk.

---

## No-touch zones verified (untouched)

- Runtime Missions (`src/missions/`, `data/missions/`)
- AppFactory (`src/app_factory/`, `data/app_factory/`)
- Health checks
- Templates (`docs/templates/`, `src/delivery_templates/`)
- KRATOS (`.kratos/`)
