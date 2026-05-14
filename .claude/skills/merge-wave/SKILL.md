# merge-wave

## When to use
- After all squads have completed and reported
- When Control Tower is closing a wave

## When NOT to use
- Mid-squad (squads don't merge themselves)
- When any squad has failing tests

## Inputs
- Wave identifier
- List of squad branches (in merge order)
- Safety tag name

## Steps
1. Create safety tag on master: `git tag safety-base-<wave>`
2. For each squad branch:
   a. Checkout master
   b. `git merge --ff-only <squad-branch>`
   c. Run full suite
   d. If pass: continue to next squad
   e. If fail: pause, diagnose, report
3. After all merges: final full suite
4. Generate merge report

## Output
- Merge report: `docs/OMNIS_WAVE_XX_MERGE_TO_MASTER_REPORT.md`
- Updated War Room status

## Blocking criteria
- --ff-only fails → stop (no non-ff without authorization)
- Full suite fails after any merge → pause, diagnose
- Working tree dirty → clean first
