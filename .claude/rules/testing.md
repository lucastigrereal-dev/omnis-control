# Testing Rules

## Commands
- Targeted: `python -m pytest tests/<module>/ --import-mode=importlib -p no:warnings -v`
- Full suite: `python -m pytest tests/ --import-mode=importlib -p no:warnings -q`

## When to run
- Targeted test: before committing any src/ change
- Full suite: after merge, before push, or when changing shared models

## Conventions
- pytest-native: fixtures, tmp_path, monkeypatch
- No unittest.mock
- Mock-first for external adapters
- to_dict()/from_dict() round-trip on all models
- Every module has at least 3 test files
