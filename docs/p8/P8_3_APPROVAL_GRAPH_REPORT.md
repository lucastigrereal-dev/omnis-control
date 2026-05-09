# P8.3 — Approval-Integrated Graph Run Report

**Data:** 2026-05-09 | **Bloco:** P8.3 | **Status:** ✅ done

---

## Scope

Bridge the Execution Graph with the Approval Center. Graph runs that require approval (medium/high risk squads) are blocked until the operator explicitly approves the request via CLI.

## Files

| File | Action | Lines |
|---|---|---|
| `src/execution_graph/approval_bridge.py` | created | 105 |
| `src/execution_graph/models.py` | updated | +approval_id, +approval_required, +blocked() factory |
| `src/execution_graph/runner.py` | updated | +2 params (approval_id, approval_required) |
| `src/cli_commands/execution_graph_cmd.py` | updated | +run-gated command |
| `tests/execution_graph/test_approval_graph.py` | created | 260 |

## Architecture

### `check_approval_gate(approval_required, approval_id, approvals_log) → str`

Evaluates whether a graph run can proceed. Returns one of:
- `"not_required"` — low risk, no approval needed
- `"approved"` — approval request resolved favorably
- `"rejected"` — approval request denied
- `"blocked_pending_approval"` — approval missing or still pending

### `request_graph_approval(graph, risk_level, approvals_log) → str`

Creates an `ApprovalRequest` in the approval center. Subject includes graph.request, description includes graph_id + squad_id + step list. Returns the request_id.

### `run_graph_with_approval_gate(graph, squad_plan, approval_id, approvals_log, fail_at) → StepRun`

Full gate-enforced flow:
1. If not_required or approved → calls `run_graph_dry()` normally
2. If rejected → returns blocked StepRun with reason
3. If blocked → auto-creates approval request, returns blocked StepRun with CLI command hint

### `StepRun.blocked(graph, reason, approval_id, approval_required)` factory

Creates a StepRun in "blocked_pending_approval" status with a single log entry and graph snapshot.

## CLI

```
jarvis.py graph run-gated <request> [--approval-id <id>] [--json]
```

## Risk Flow

| Risk | Sector | Keywords | Gate |
|---|---|---|---|
| Low | marketing | post, campanha, conteudo, instagram | Bypass (run directly) |
| Medium | sales | vendas, lead, proposta, collab, hotel | Block until approved |
| High | apps | dashboard, api, sistema, software | Block until approved |

## Tests — 20/12 PASS

| Category | Tests |
|---|---|
| Gate status checks | 6 |
| Approval request creation | 1 |
| StepRun.blocked factory | 2 |
| Serialization with approval fields | 2 |
| Integration: low risk bypass | 1 |
| Integration: medium risk blocks | 1 |
| Integration: approved request runs | 1 |
| Integration: rejected request blocks | 1 |
| Integration: high risk auto-create | 1 |
| Integration: failure injection post-gate | 1 |
| CLI smoke | 3 |

## Cumulative

```
P8.0 execution_graph:      16/10 PASS
P8.1 step_runner:          21/15 PASS
P8.2 replay_resume:        15/12 PASS
P8.3 approval_graph:       20/12 PASS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL P8:                   72/49
```
