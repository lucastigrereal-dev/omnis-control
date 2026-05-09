# P8.6 — E2E Mission → Squad → Graph → Approval Report

**Data:** 2026-05-09 | **Bloco:** P8.6 | **Status:** ✅ done

---

## Scope

Full lifecycle E2E tests: request text → orchestrator plan → squad composition → graph build → approval gate → dry-run execution → verify all IDs linked.

## Fixes Applied

### 1. `mission_bridge.py` — approval_id forwarding
When `approval_id` is provided to `run_full_pipeline()`, it now calls `orch_svc.run_with_approval()` instead of `orch_svc.run()`. This ensures the orchestrator doesn't re-block when an existing approved request is passed.

### 2. `test_e2e_pipeline.py` — parameter name fixes
`approve()`/`reject()` accept `note=` not `resolution_note=` — fixed in 4 test locations.

### 3. `test_e2e_pipeline.py` — risk level isolation
Tests expecting medium risk used requests containing "crm" keyword, which triggers `_OUTPUT_HINTS` → `app_architect` (high risk role). Changed to "proposta de vendas e collab" to stay medium risk.

### 4. `test_e2e_pipeline.py` — CLI invocation
CLI tests changed from `-m src.cli_commands.mission_orchestrator_cmd` to `jarvis.py orchestrator run-full` with proper `cwd`.

### 5. `test_e2e_pipeline.py` — blocked CLI test
`test_cli_run_full_blocked` now expects returncode=0 (the `--json` path doesn't raise `typer.Exit`) and validates `blocked_pending_approval` status + blockers from JSON.

## Tests — 14/10 PASS

| Category | Tests |
|---|---|
| Low risk full flow (no approval) | 1 |
| Medium risk approval lifecycle (block → approve → run) | 1 |
| Medium risk rejection (block → reject → stays blocked) | 1 |
| Orchestrator approval flow (detect → create → block) | 1 |
| Orchestrator approve then run | 1 |
| Full pipeline with approval bridge | 1 |
| Multi-account scenarios | 1 |
| High risk full lifecycle | 1 |
| Serialization / JSON round-trip | 1 |
| Event log bridge in E2E | 1 |
| Dry-run safety (no side effects) | 1 |
| Unknown intent edge case | 1 |
| CLI run-full works | 1 |
| CLI run-full blocked | 1 |

## Cumulative

```
P8.0 execution_graph:      16/10 PASS
P8.1 step_runner:          21/15 PASS
P8.2 replay_resume:        15/12 PASS
P8.3 approval_graph:       20/12 PASS
P8.4 event_log_metrics:    25/10 PASS
P8.5 mission_squad_graph:  26/10 PASS
P8.6 e2e graph flow:       14/10 PASS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL P8:                  137/79
```
