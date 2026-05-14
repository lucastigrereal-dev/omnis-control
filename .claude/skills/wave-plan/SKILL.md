# wave-plan

## When to use
- Before starting any new wave (sequential or parallel)
- When the operator says "planejar onda", "wave plan", "prepare wave"

## When NOT to use
- During active execution (use scope-lock instead)
- For single-file fixes (too heavy)

## Inputs
- Wave objective (from operator)
- Phases to include
- Number of parallel squads (1-3)
- Constraints (no OAuth, no push, etc.)

## Steps
1. Read current git state (branch, log, working tree)
2. Read relevant existing docs from docs/architecture/ and docs/implementation/
3. Assign phases to squads, checking no file overlap
4. Generate plan document

## Output
- `docs/implementation/<WAVE>_PLAN.md` containing:
  - Summary
  - Squad assignments with phases
  - Worktree paths and branch names
  - Scope per squad (allowed/forbidden paths)
  - Merge order
  - Test strategy
  - Risk assessment
  - Handoff prompts per squad

## Blocking criteria
- Working tree dirty with code changes → pause
- Phase numbers conflict with existing → flag
- File overlap between squads → reassign
