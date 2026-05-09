# P4.4 — Approval Center Local

**Status:** COMPLETE  
**Tests:** 26/26 PASS  
**Commit:** pending  

## What was built

Local approval queue for high-risk operations. When `skill_matcher` returns `requires_approval=True`, the operation should be submitted here for human review before execution. No external services, no network — JSONL append-only persistence.

## Files

| File | Role |
|---|---|
| `src/approval_center/__init__.py` | package |
| `src/approval_center/errors.py` | `ApprovalNotFoundError`, `ApprovalAlreadyResolvedError` |
| `src/approval_center/models.py` | `ApprovalRequest`, status constants |
| `src/approval_center/store.py` | `ApprovalStore` — JSONL with deduplication by `request_id` |
| `src/approval_center/service.py` | `request_approval()`, `approve()`, `reject()` |
| `src/cli_commands/approval_center_cmd.py` | CLI: request / list / show / approve / reject |

## Status machine

```
pending → approved  (via approve)
pending → rejected  (via reject)
approved/rejected → ERROR  (ApprovalAlreadyResolvedError)
```

## CLI

```bash
omnis approvals-center request "publish reels hotel" --capability campaign_package
omnis approvals-center list --status pending
omnis approvals-center show req_abc123
omnis approvals-center approve req_abc123 --note "cleared by Lucas"
omnis approvals-center reject req_abc123 --note "too early"
```

## Store design

`update_status()` appends a new record with updated status (same `request_id`). `get()` reads all records and returns the latest version (last write wins). `list_all()` deduplicates by `request_id`, keeping the latest version of each, then returns newest-first.

## Test coverage

| Module | Tests | Notes |
|---|---|---|
| models | 4 | new(), round-trip, constants, description field |
| store | 8 | save+list, empty, get found/not-found, update, newest-first, filter by status, latest-wins |
| service | 7 | request, approve, reject, not-found, double-approve, reject-already-approved |
| cli | 7 | help, request/approve/reject JSON, list empty, show/approve not-found |
