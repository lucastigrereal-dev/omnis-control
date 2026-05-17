# G17 — Remote Control Summary (W156-W160)

**Date:** 2026-05-17
**Status:** COMPLETE

## Waves Delivered

| Wave | Module | Tests |
|---|---|---|
| W156 | command_dispatcher.py + adapters + security | 95 |
| W157 | webhook_gateway.py | 29 |
| W158 | rate_limiter.py | 19 |
| W159 | audit_log.py | 23 |
| W160 | pipeline.py (E2E) | 19 |

## Total G17 Tests: 185 (remote_control/ module)

## Architecture

```
WebhookPayload (Telegram/WhatsApp/Generic/KRATOS)
    → WebhookGateway (parse, signature verify, source allow-list)
    → RateLimiter (sliding window, burst detection)
    → Risk Gate (HIGH/CRITICAL → requires_approval → BLOCKED)
    → CommandDispatcher (route to handler, dry-run)
    → CommandAuditLog (JSONL-backed trail)
```

## Safety

- dry_run=True enforced at every stage
- HMAC-SHA256 signature verification
- Source allow-list blocks unknown origins
- HIGH-risk commands require human approval before dispatch
- Burst detection prevents rapid-fire abuse
- No real Telegram/WhatsApp API calls
- No external credentials read
