# WAVE 036 — Error Taxonomy — REPORT
**Date:** 2026-05-15 | **Status:** COMPLETE | **Skills:** sc:implement, sc:test

## Blocos: 10/10 PASS
`ErrorClassifier` with 9 categories (VALIDATION, RUNTIME, CONFIGURATION, IO, SECURITY, TIMEOUT, DEPENDENCY, STATE_MACHINE, UNKNOWN) + 4 severity levels (FATAL, ERROR, WARNING, INFO). Pattern-based classification with exception type fallback. `is_retryable()` and `is_fatal()` predicates. `ClassifiedError` dataclass. `CATEGORY_SEVERITY_MAP` for default severity mapping. 16 tests.
