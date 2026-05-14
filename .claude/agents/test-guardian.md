# test-guardian

## When to use
- After implementing any src/ change
- Before committing
- When targeted test count doesn't match module size

## Checks
1. Targeted tests pass for the module
2. No regression in existing tests
3. New code has corresponding test coverage
4. Fixtures use tmp_path (never real paths)
5. No test uses real API/network calls

## Commands
```sh
# Targeted
python -m pytest tests/<module>/ --import-mode=importlib -p no:warnings -v

# Full (before merge)
python -m pytest tests/ --import-mode=importlib -p no:warnings -q
```

## Output
- PASS: all tests pass, coverage reasonable
- WARNING: tests pass but coverage is thin
- FAIL: tests fail or missing

## Checklist
- [ ] Targeted tests pass
- [ ] No regression in other modules
- [ ] At least 3 test files per module
- [ ] All fixtures use tmp_path
- [ ] Zero real network/API calls
