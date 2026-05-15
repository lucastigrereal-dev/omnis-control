# OMNIS W12B1 — Governance Policy

**Date:** 2026-05-15

## Principles
1. **dry_run default** — All execution defaults to dry_run=True. Real execution requires explicit opt-in.
2. **Human in the loop** — CRITICAL and HIGH-risk actions require human approval. No bypass.
3. **Zero secrets access** — No module reads .env, secrets/, *.key, or *.pem files.
4. **No destructive without approval** — rm, delete, drop, force-push require explicit token.
5. **Mock-first** — External adapters are mocked by default. Real connections are opt-in.
6. **Audit trail** — Every execution, approval, rejection is logged as an event.

## Risk matrix

| Risk | Auto-Execute | Requires Token | Requires Human |
|---|---|---|---|
| LOW | Yes | No | No |
| MEDIUM | Dry-run only | Optional | No |
| HIGH | No | Yes | Yes |
| CRITICAL | Never | Yes | Yes |

## Approval flow
1. Action requested → risk assessed
2. If HIGH/CRITICAL → approval challenge issued (token generated)
3. Challenge sent to authorized approver (CLI, KRATOS, Telegram, WhatsApp)
4. Approver responds with token
5. Token validated → action executed or rejected

## Merge policy
- Feature branches only (no direct master commits)
- Full test suite must pass before merge
- Security review must pass
- Import guard scan must be clean
- No merge with dirty working tree

## Push policy
- Explicit authorization required
- Full suite must have passed within the session
- No force-push without emergency declaration
