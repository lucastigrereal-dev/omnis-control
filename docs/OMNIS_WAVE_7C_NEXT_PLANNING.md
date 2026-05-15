# OMNIS Wave 7C — Next Planning

**Date:** 2026-05-15
**Prerequisite:** Wave 7B complete (5611 tests, 9 modules)

## What Wave 7B delivered
- Runtime bridge: War Room orders → 9-step pipeline → reports
- Approval system: risk matrix, single-use tokens, file-backed store
- Skill routing: catalog, selector, dry-run dispatcher
- CLI layer: 6 commands, smoke tests
- Observability: audit trail, rollback planning, run logger
- E2E safety tests: 30 integration tests across all modules

## Recommended Wave 7C scope

### P47 — Real Skill Execution Bridge
Wire DryRunDispatcher to actual Python skill modules. Replace `_simulate()` with real function imports. Requires skill registry validation.

### P48 — Notification Adapters (Telegram/WhatsApp)
Implement the adapters designed in P41. Start with Telegram bot (mock-first), then WhatsApp template. Use approval tokens for auth.

### P49 — Akasha Real Sink
Wire FileAkashaSink to real Akasha pgvector (port 5432). Batch flush, retry logic, health check against live service.

### P50 — Pipeline Recovery & Retry
Resume failed pipelines from last completed step. Rollback plans → execution. Requires RunLogger + RollbackEngine integration.

### P51 — Multi-ABA Parallel Execution
Run multiple War Room orders concurrently with isolated pipelines. Queue management, priority sorting, ABA conflict detection.

### P52 — Observability Dashboard Data
Export audit trails and run logs as JSON endpoints for KRATOS cockpit. Aggregated stats: pass rate, avg duration, risk distribution.

## Priority order
1. **P47** — unlocks real skill execution (highest value)
2. **P49** — connects to real memory (Akasha)
3. **P48** — enables remote approval via Telegram
4. **P50** — resilience for production use
5. **P51** — throughput for multi-ABA
6. **P52** — visibility for operator

## Dependencies
- P47 needs: skill registry validation (existing SKILL.md files)
- P48 needs: Telegram bot token (requires Lucas to configure)
- P49 needs: Akasha pgvector healthy (currently: unknown status)
- P50-P52: no external dependencies

## Not recommended for Wave 7C
- KRATOS frontend integration (separate repo)
- OAuth Meta flows (blocked — META_APP_ID/SECRET pending)
- Docker container health fixes (separate ops concern)
- Real publish/send/deploy (requires production gate review)

## Decision needed from Lucas
1. Confirm Wave 7C scope (accept/reject/reorder)
2. Provide Telegram bot token if P48 is approved
3. Confirm Akasha pgvector is reachable for P49
4. Authorize Wave 7C start
