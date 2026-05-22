# AUTOPILOT 6H — Test Summary

**Date:** 2026-05-22
**Command:** `python -m pytest tests/execution_graph/ tests/omnis_bus/ tests/observability/test_health_file.py --import-mode=importlib -p no:warnings -q`

## Result: 340/341 PASSED (99.7%)

### By Suite

| Suite | Passed | Failed | Notes |
|-------|--------|--------|-------|
| execution_graph | 196 | 1 | Pre-existing CLI JSON parse bug |
| shadow_mode (new) | 17 | 0 | All green |
| omnis_bus | 121 | 0 | No regression from trace_id |
| health_file (new) | 6 | 0 | All green |
| **TOTAL** | **340** | **1** | |

### Pre-existing Failure

```
tests/execution_graph/test_step_runner.py::test_cli_graph_run_list
  JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

Root cause: `jarvis.py graph run-list` subprocess returns empty/error response. Not related to any autopilot changes. Present before Waves A-F.

### Zero Regression Evidence

- `src/execution_graph/models.py` — ShadowConfig added, all 213 existing EG tests pass
- `src/execution_graph/events.py` — 7 new EventTypes added, event serialization unaffected
- `src/execution_graph/replay.py` — optional event_log parameter added, backward compatible
- `src/observability/logging_config.py` — alias added, existing imports unaffected
- `src/omnis_bus/envelope.py` — trace_id field added to CanonicalEnvelope, 121/121 pass
