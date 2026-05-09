# P8.2 — Replay / Resume Report

**Data:** 2026-05-09 | **Bloco:** P8.2 | **Status:** ✅ done

---

## Scope

Replay and Resume for Execution Graph runs. After a dry-run fails or completes, the operator can:
- **Resume** — re-run only non-DONE steps (skip already completed)
- **Replay** — re-execute ALL steps from scratch (fresh run)

## Files

| File | Action | Lines |
|---|---|---|
| `src/execution_graph/replay.py` | created | 65 |
| `src/execution_graph/runner.py` | updated | +3 params |
| `src/execution_graph/models.py` | updated | graph_snapshot field |
| `src/cli_commands/execution_graph_cmd.py` | updated | +2 commands |
| `tests/execution_graph/test_replay_resume.py` | created | 250 |

## Resume

```python
resume_graph_run(run_id: str) -> StepRun | None
```

1. Reads manifest from `exports/graph_runs/{run_id}/manifest.json`
2. Extracts `graph_snapshot` → reconstructs `ExecutionGraph` via `from_dict()`
3. Collects all step_ids with `status == "done"` → `skip_done` set
4. Calls `run_graph_dry(graph, skip_done=skip_done, include_snapshot=True)`
5. Runner skips DONE steps, re-executes FAILED/PENDING

## Replay

```python
replay_graph_run(run_id: str) -> StepRun | None
```

1. Same manifest + snapshot load
2. Calls `run_graph_dry(graph, include_snapshot=True)` — NO skip
3. All steps executed fresh, new `graph_run_id` generated

## CLI Commands

```
jarvis.py graph run-resume <run_id> [--json]
jarvis.py graph run-replay <run_id> [--json]
```

## Tests — 15/15 PASS

| Test | Category |
|---|---|
| `test_step_node_from_dict_roundtrip` | unit |
| `test_execution_graph_from_dict_roundtrip` | unit |
| `test_graph_snapshot_in_manifest` | integration |
| `test_resume_all_done_produces_same_result` | resume |
| `test_resume_preserves_done_steps` | resume |
| `test_resume_with_nonexistent_run_returns_none` | resume |
| `test_resume_without_snapshot_returns_none` | resume |
| `test_resume_skips_steps_that_were_done_before_failure` | resume |
| `test_replay_runs_all_steps_fresh` | replay |
| `test_replay_after_failure_succeeds` | replay |
| `test_replay_with_nonexistent_run_returns_none` | replay |
| `test_replay_without_snapshot_returns_none` | replay |
| `test_cli_graph_run_resume` | CLI smoke |
| `test_cli_graph_run_replay` | CLI smoke |
| `test_graph_snapshot_survives_roundtrip` | integration |

## Cumulative

```
P8.0 execution_graph:      16/10 PASS
P8.1 step_runner:          21/15 PASS
P8.2 replay_resume:        15/12 PASS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL P8:                   52/37
```
