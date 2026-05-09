# P8.5 — Mission → Squad → Graph Integration Report

**Data:** 2026-05-09 | **Bloco:** P8.5 | **Status:** ✅ done

---

## Scope

Connect P3 (Mission Orchestrator) + P7 (Squad Composer) + P8 (Execution Graph) into a single unified pipeline.

## Files

| File | Action | Lines |
|---|---|---|
| `src/mission_orchestrator/models.py` | updated | +2 fields |
| `src/mission_orchestrator/planner.py` | updated | +2 steps |
| `src/execution_graph/mission_bridge.py` | created | 130 |
| `src/cli_commands/mission_orchestrator_cmd.py` | updated | +70 |
| `tests/execution_graph/test_mission_bridge.py` | created | 230 |

## Models Changes

### OrchestratorRun — 2 new fields

| Field | Type | Description |
|---|---|---|
| `squad_id` | `Optional[str]` | SquadPlan ID from squad composer |
| `graph_run_id` | `Optional[str]` | StepRun ID from graph execution |

Both fields survive `to_dict()`/`from_dict()` round-trip.

## Planner Changes — Steps s06, s07

| Step | Module | Description |
|---|---|---|
| s06 | `squad_composer` | Compose squad from request (roles, risk, approval flag) |
| s07 | `execution_graph` | Build + execute graph of steps |

Total steps: 5 → 7.

## Mission Bridge (`mission_bridge.py`)

### `build_graph_from_orchestrator(orch_run) → ExecutionGraph`

Chains: `compose_squad → decompose_squad → build_graph`. Sets `orch_run.squad_id`.

### `run_graph_from_orchestrator(orch_run, fail_at, approval_id) → StepRun`

Full chain including execution. Sets `orch_run.graph_run_id`.

### `run_full_pipeline(request, ...) → (OrchestratorRun, StepRun)`

Single entry point for the complete P3+P7+P8 flow:
1. Orchestrator plan + execute (s01-s05)
2. Guard: if blocked/failed, return early with step_run=None
3. Squad composition (s06)
4. Graph build + dry-run (s07)
5. Persist graph run to store

## CLI — `orchestrator run-full`

```bash
jarvis orchestrator run-full "criar post de viagem em natal"
jarvis orchestrator run-full "criar post de viagem" --json
```

Rich output shows orchestrator steps + graph step states in a table.

## Tests — 26/10 PASS

| Category | Tests |
|---|---|
| Planner s06/s07 presence | 4 |
| Models: squad_id + graph_run_id | 4 |
| build_graph_from_orchestrator | 2 |
| run_graph_from_orchestrator | 2 |
| run_full_pipeline core | 7 |
| Integration (multi-run, round-trip) | 3 |
| Dry-run safety | 1 |
| Intent detection in full pipeline | 2 |
| Approval flows | 2 |

## Cumulative

```
P8.0 execution_graph:      16/10 PASS
P8.1 step_runner:          21/15 PASS
P8.2 replay_resume:        15/12 PASS
P8.3 approval_graph:       20/12 PASS
P8.4 event_log_metrics:    25/10 PASS
P8.5 mission_squad_graph:  26/10 PASS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL P8:                  123/69
```
