# Quarantine Plan — OMNIS Disk Safety Audit

**Generated:** 2026-05-18T20:57:21Z
**Status:** READ-ONLY — no files have been modified

## Summary

| Category | Count | Size |
|----------|-------|------|
| safe_to_delete | 2 | 790.7 KB |
| needs_review | 50 | 273.6 MB |
| do_not_touch | 8 | — |
| active_project | 0 | — |
| archived_project | 0 | — |

## Safety Rules

1. **NEVER delete** without explicit operator approval
2. Move to quarantine dir first, keep for 14 days before permanent removal
3. `do_not_touch` paths are immutable — any action requires human override
4. `needs_review` paths require human decision before any action

## Safe to Delete

> These paths match known safe patterns (caches, build artifacts, large logs). Quarantine first, delete only after operator approval.

| Path | Size | Reason |
|------|------|--------|
| `C:\Users\lucas\omnis-control\.pytest_cache` | 736.1 KB | matches safe pattern: .pytest_cache |
| `C:\Users\lucas\omnis-control\scripts\__pycache__` | 54.6 KB | matches safe pattern: __pycache__ |

## Needs Review

> These paths could not be auto-classified. Human review required before any action.

| Path | Size | Reason |
|------|------|--------|
| `C:\Users\lucas\omnis-control\.gitignore` | 934 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\.test_tmp` | 758.2 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\.tmp_pytest` | 7 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\.tmp_pytest_base` | 0 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\.tmp_pytest_full` | 537 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\.venv` | 129.2 MB | no specific rule matched |
| `C:\Users\lucas\omnis-control\AGENTS.md` | 3.5 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\BLUEPRINT.md` | 775 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\bootstrap-omnis-ccos.ps1` | 24.5 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\bundles` | 2.8 MB | no specific rule matched |
| `C:\Users\lucas\omnis-control\cockpit` | 54.9 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\CUserslucasomnis-controldatamissionscontracts` | 0 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\CUserslucasomnis-controldatamissionsevents` | 0 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\CUserslucasomnis-controldatapipeline_runs` | 0 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\CUserslucasomnis-controldocsmissions` | 0 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\CUserslucasomnis-controldocspipeline` | 0 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\CUserslucasomnis-controlsrcmissions` | 0 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\CUserslucasomnis-controltestsmissions` | 0 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\CUserslucasomnis-controltestspipeline` | 0 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\data` | 76.9 MB | no specific rule matched |
| `C:\Users\lucas\omnis-control\diagnose_e2e.json` | 14.5 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\diagnose_omnis.json` | 14.5 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\exports` | 50.3 MB | no specific rule matched |
| `C:\Users\lucas\omnis-control\jarvis.py` | 551 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\jarvis_control.egg-info` | 1.4 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\logs` | 2.3 MB | no specific rule matched |
| `C:\Users\lucas\omnis-control\migrations` | 2.0 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\missions` | 551.8 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\omnis-control` | 0 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\omnis-skill-setup.sh` | 9.4 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\omnis.project.yaml` | 1.2 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\omnis.py` | 514 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\omnis_agent_tasks.yaml` | 1.3 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\omnis_blocked_items.yaml` | 2.1 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\omnis_guardrails.yaml` | 942 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\omnis_state.yaml` | 2.3 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\omnis_wave_registry.yaml` | 2.7 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\omnis_worktrees.yaml` | 1.4 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\PROMPT_MESTRE_OMNIS_SUPREME.md` | 1.1 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\pyproject.toml` | 672 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\README.md` | 2.4 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\reports` | 10.4 MB | no specific rule matched |
| `C:\Users\lucas\omnis-control\schemas` | 5.5 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\scripts` | 170.4 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\skill_reports` | 474 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\skills` | 154.2 KB | no specific rule matched |
| `C:\Users\lucas\omnis-control\srcexecutors` | 0 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\testsexecutors` | 0 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\testsreports` | 0 B | no specific rule matched |
| `C:\Users\lucas\omnis-control\workflows` | 3.0 KB | no specific rule matched |

## Do Not Touch

> Protected system paths. No action permitted.

| Path | Size | Reason |
|------|------|--------|
| `C:\Users\lucas\omnis-control\.claude` | 57.5 MB | protected system path |
| `C:\Users\lucas\omnis-control\.env` | 186 B | protected system path |
| `C:\Users\lucas\omnis-control\.git` | 10.5 MB | protected system path |
| `C:\Users\lucas\omnis-control\CLAUDE.md` | 1.8 KB | protected system path |
| `C:\Users\lucas\omnis-control\config` | 30.4 KB | protected system path |
| `C:\Users\lucas\omnis-control\docs` | 2.0 MB | protected system path |
| `C:\Users\lucas\omnis-control\src` | 7.6 MB | protected system path |
| `C:\Users\lucas\omnis-control\tests` | 17.1 MB | protected system path |

## Active Projects

> Detected active project roots. Keep unless explicitly archiving.

_(none)_

## Archived Projects

> Possible archived/backup content. Verify before removal.

_(none)_
