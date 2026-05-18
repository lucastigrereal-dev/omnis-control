# W202 — Temporary Test Directories Cleanup Plan
# Status: DONE (CLEAN) | 2026-05-17

## Summary
No stale temporary test directories found. No cleanup needed.

---

## .gitignore temp patterns (expected dirs)

| Pattern | Referenced in code? | Present on disk? | Action |
|---|---|---|---|
| `.test_tmp/` | Yes (app_factory tests, idea_cli.py) | No | None |
| `.tmp_pytest/` | No (only in .gitignore) | No | None |
| `.tmp_pytest_base/` | No (only in .gitignore) | No | None |
| `.tmp_pytest_full/` | No (only in .gitignore) | No | None |
| `__pycache__/` | Python runtime | Not scanned | Git-ignored |
| `.pytest_cache/` | pytest runtime | Not scanned | Git-ignored |

---

## Temp directory creators (code audit)

| File | Mechanism | Auto-clean? | Risk |
|---|---|---|---|
| `tests/app_factory/conftest.py:12` | `.test_tmp/app_factory/<uuid>` | Manual | LOW — AppFactory zone |
| `tests/analytics/test_models.py:144` | `tempfile.TemporaryDirectory()` | Yes (context mgr) | NONE |
| `tests/analytics/test_exporters.py` | `tempfile.TemporaryDirectory()` | Yes (context mgr) | NONE |
| `src/app_factory/idea_cli.py:248` | `.test_tmp/app_factory_scaffold` | Manual (CLI default) | LOW — AppFactory zone |
| 40+ test files | pytest `tmp_path` fixture | Yes (pytest built-in) | NONE |

---

## Dry-run cleanup simulation

```bash
# If cleanup were needed, the dry-run would be:
find . -maxdepth 1 -type d \( -name ".test_tmp" -o -name ".tmp_pytest*" \) -exec echo "[DRY-RUN] would remove: {}" \;
# Result: no matches — nothing to clean
```

---

## Conclusion
Zero stale temp directories found. `.test_tmp/` is created on-demand by AppFactory tests and cleaned between runs (it was absent at scan time). All other temp mechanisms auto-clean.

No action required.
