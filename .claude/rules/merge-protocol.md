# Merge Protocol

## Pre-merge checklist
1. Working tree clean (no unrelated changes)
2. Targeted tests pass for the module
3. Import guard scan clean
4. No conflicts with active worktrees

## Merge sequence (parallel squads)
1. Merge squad A → full suite
2. Merge squad B → full suite
3. Merge squad C → full suite
4. If any merge fails: pause, diagnose, do NOT rollback prior merges unless they caused the failure

## Post-merge
1. Full suite must pass
2. Generate merge report
3. Update War Room status
4. Await push authorization

## Safety
- Always use `--ff-only` when possible
- Create safety tag before starting merge wave
- Never merge with dirty working tree
