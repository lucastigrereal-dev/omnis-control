# Wave F — Cleanup Controlado: Classification Report

## Git Tag
- `archive/omnis-maintenance-execution-graph` created on omnis-maintenance (EG-007 ratified)

## Branch Classification

### DEAD (14+ days, pre-Phase 1)
| Branch | Last Commit | Recommendation |
|--------|-------------|----------------|
| recovery/stash-fase1-creative-production | 2026-05-06 | DELETE |
| fix/cli-creative-status-regression | 2026-05-06 | DELETE |
| fix/bug1-id-prefix-matching | 2026-05-06 | DELETE |
| auto-pilot/janitorial-20260506_234924 | 2026-05-07 | DELETE |

### STALE (7-13 days, parallel phase branches)
| Branch | Last Commit | Worktree? | Recommendation |
|--------|-------------|-----------|----------------|
| parallel/p20-omnis-supreme | May 13 | YES | ARCHIVE → git tag + delete branch |
| parallel/p21-memory-intel | May 13 | NO | ARCHIVE → git tag + delete branch |
| parallel/p22-capability-forge-real | May 13 | NO | ARCHIVE → git tag + delete branch |
| parallel/p23-autonomous-execution | May 14 | YES | ARCHIVE → git tag + delete branch |
| parallel/p24-live-cockpit | May 14 | YES | ARCHIVE → git tag + delete branch |
| parallel/p25-p29-sequential-supreme | May 14 | YES | ARCHIVE → git tag + delete branch |
| feature/omnis-wave-7a-control-tower | May 14 | NO | ARCHIVE |
| feature/omnis-wave-7b-runtime-bridge | May 15 | NO | ARCHIVE |

### SHADOW (merged, kept for reference)
| Branch | Last Commit | Recommendation |
|--------|-------------|----------------|
| feat/p37-runtime-bridge | May 16 | KEEP until Phase 2 merge verified |

### ACTIVE (current work, DO NOT TOUCH)
- feature/omnis-5waves-runtime-supreme (current)
- feature/omnis-g14-app-factory
- feature/omnis-runtime-w186-w195
- feature/omnis-templates-w206-w215
- feature/omnis-maintenance-w201-w205 (now tagged)
- feature/omnis-health-w196-w200
- master

## Worktrees — Safe to Remove (requires auth)
7 worktrees are stale and have corresponding branches that can be archived:
1. omnis-appfactory
2. p23-autonomous-execution
3. p24-live-cockpit
4. p25-p29-sequential-supreme
5. omnis-health
6. omnis-maintenance (tagged)
7. p20-omnis-supreme

## 7 Pycache Directories — Safe to Delete
These are regenerated on next import:
1. src/execution_graph/__pycache__/
2. src/cli_commands/__pycache__/

(Others exist throughout — harmless, not blocking anything)

## Action Blocked
- Worktree removal requires operator authorization per OMNIS rules
- Branch deletion requires operator authorization
- Pycache is benign — no action needed

## Next Step
Operator must authorize: `git worktree remove <name>` for each stale worktree.
