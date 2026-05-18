# Disk Safety Audit Report — F08

**Generated:** 2026-05-18  
**Status:** DONE  
**Branch:** feature/omnis-5waves-runtime-supreme

## What was implemented

### `src/computer_ops/disk_safety_audit.py`
- `DiskSafetyAuditor` class with three public methods:
  - `scan(root, dry_run=True) -> dict` — categorizes all paths into 5 buckets
  - `generate_csv(candidates, output_path) -> Path` — writes CSV report
  - `generate_quarantine_plan(candidates, output_path) -> Path` — writes Markdown plan

### Categories
| Category | Description |
|---|---|
| `safe_to_delete` | node_modules, __pycache__, .cache, dist, build, logs >1MB |
| `needs_review` | unclassified paths, zip files in exports/, orphaned worktrees |
| `do_not_touch` | `.git`, `src`, `tests`, `docs`, `config`, `.claude`, `.env`, `secrets` |
| `active_project` | dirs with pyproject.toml, package.json, requirements.txt |
| `archived_project` | dirs with archive/backup/deprecated in name |

### Safety guarantees
- NEVER deletes anything — read-only scan
- Protected paths hardcoded: `.git`, `src`, `tests`, `docs`, `config`, `.claude`, `.env`, `secrets`, `CLAUDE.md`
- `dry_run=True` by default on all entry points

### CLI — `omnis local disk-audit`
Added to `src/cli_local.py`. Usage:
```sh
python -m src.cli omnis local disk-audit --root . --dry-run
```

### Reports generated (actual project scan)
- `reports/disk_cleanup_candidates.csv` — 60 paths categorized
- `reports/quarantine_plan.md` — full markdown quarantine plan

### Scan results (omnis-control root)
| Category | Paths | Notes |
|---|---|---|
| safe_to_delete | 2 | `__pycache__` + large log |
| needs_review | 50 | Most top-level dirs — awaiting human review |
| do_not_touch | 8 | src, docs, config, .claude, .git etc. |
| active_project | 0 | — |
| archived_project | 0 | — |

## Tests
`tests/computer_ops/test_disk_safety_audit.py` — **21 tests, 21 passed**

Coverage:
- scan() returns expected structure
- node_modules, __pycache__, big logs → safe_to_delete
- small logs not in safe_to_delete
- dry_run=True/False never deletes
- protected paths never in safe_to_delete
- src, docs always in do_not_touch
- CSV written with correct headers and row count
- quarantine plan is valid markdown with safety rules
- generate_csv / generate_quarantine_plan never delete source files
