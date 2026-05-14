# scope-lock

## When to use
- Before a squad starts coding
- After wave-plan, before execution

## When NOT to use
- During planning (use wave-plan)
- After squad finished (scope is frozen)

## Inputs
- Squad name
- Wave identifier
- Allowed directories
- Forbidden directories
- Actions permitted

## Steps
1. Read wave plan for squad assignments
2. Create `.claude/scopes/<wave>-<squad>.md`
3. List all allowed src/, tests/, docs/ paths
4. List all forbidden paths (.env, secrets, other squads, etc.)
5. Define allowed actions (read, write, edit, test)
6. Define forbidden actions (push, merge, API calls)

## Output
- `.claude/scopes/<wave>-<squad>.md`

## Blocking criteria
- Scope overlaps with another active squad → resolve first
- Forbidden paths list doesn't include .env/secrets → add
- Allowed paths include .kratos/ → remove
