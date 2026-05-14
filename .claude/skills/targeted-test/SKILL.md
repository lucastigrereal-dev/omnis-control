# targeted-test

## When to use
- After editing any file in src/<module>/
- Before committing
- When operator says "testa isso", "rodar teste do modulo"

## When NOT to use
- Before merge (use full-suite-gate)
- When no src/ files changed

## Inputs
- Module name (e.g., "control_tower", "decision_log")
- Or file path (auto-detect module)

## Steps
1. Identify module from changed files
2. Check if tests/<module>/ exists
3. Run: `python -m pytest tests/<module>/ --import-mode=importlib -p no:warnings -v`
4. Report pass/fail count

## Output
- Test result: N passed, M failed, K skipped
- If fail: list failing test names and errors
- If no tests found: warning + suggest creation

## Blocking criteria
- Tests fail → do not commit until fixed
- No test directory exists → flag, suggest creating basic tests
