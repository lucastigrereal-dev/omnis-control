# P5.1 — Approval Enforcement Hook

**Tests:** 9 new (54 total in module)  
**Status:** COMPLETE  

## What was built

`src/mission_orchestrator/approval_gate.py` — gate checker + auto-request creator.

`executor.py` updated to enforce the gate before executing s01/s02.

## Gate states

| `check_approval_gate()` | Condition |
|---|---|
| `not_required` | `run.approval_required == False` |
| `blocked` | `approval_required` but no `approval_id` set, or req still pending |
| `approved` | `approval_id` points to an approved request |
| `rejected` | `approval_id` points to a rejected request |

## Execution flow with enforcement

```
execute(run)
  → check_approval_gate()
    → not_required → continue execution
    → rejected     → status=blocked, add blocker
    → blocked      → auto-create approval request, status=blocked_pending_approval
    → approved     → continue execution → status=dry_run
```

## Auto-creation

When the gate is blocked and `run.approval_id is None`, the executor automatically creates an approval request via `approval_center.service.request_approval()` and sets `run.approval_id`. The blockers list includes the exact command to approve it.

## No real execution when blocked

When `status == "blocked_pending_approval"`, steps s01 and s02 never run. `run.mission_id` stays `None`.
