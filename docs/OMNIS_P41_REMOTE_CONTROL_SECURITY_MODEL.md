# OMNIS P41 — Remote Control Security Model

**Status:** PLANNING ONLY
**Date:** 2026-05-14

## 1. Threat Model

| Threat | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Token leak | Medium | Critical | Env var only, never in code/git |
| Chat ID spoofing | Low | High | Hardcoded whitelist |
| Command injection | Medium | Critical | Allowlist, no shell passthrough |
| Replay attack | Low | Medium | Nonce/timestamp per command |
| Rate abuse | Medium | Medium | 10 cmd/min hard limit |
| Unauthorized approve | Low | Critical | Token + session-bound |

## 2. Authentication

Single-factor: Chat ID whitelist + Telegram token.
No OAuth needed for Telegram (Bot API handles auth).

## 3. Authorization Matrix

| Command | Requires Chat ID Match | Requires Approval Token | Requires Dry-Run |
|---|---|---|---|
| /status | Yes | No | N/A |
| /briefing | Yes | No | N/A |
| /approve | Yes | Yes | Yes (pre-approval) |
| /reject | Yes | Yes | N/A |
| /pending | Yes | No | N/A |
| /run | Yes | Yes | Yes (mandatory) |

## 4. Secrets Policy

- `TELEGRAM_BOT_TOKEN` — env var only, never persisted
- Chat ID whitelist — config file, not .env
- Approval tokens — generated per session, ephemeral
- All secrets sanitized from logs

## 5. Audit

Every remote command generates a SinkEvent in the Akasha event sink.
Every approval/rejection generates a DecisionLog entry.
