# OMNIS P41 — Telegram/WhatsApp Remote Control Architecture

**Status:** PLANNING ONLY — ZERO IMPLEMENTATION
**Date:** 2026-05-14
**Phase:** Design (no code)

## 1. Summary

Remote control bridge for approving/rejecting OMNIS actions via Telegram.
WhatsApp is a secondary option but Telegram is the primary target.

## 2. Architecture

```
Telegram Bot → webhook → OMNIS API → Approval Runtime → Execution
                                        ↑
                                   Chat ID Whitelist
```

## 3. Planned Commands

| Command | Action | Risk |
|---|---|---|
| `/status` | Health check of all systems | LOW |
| `/briefing` | Daily Publisher OS briefing | LOW |
| `/approve <id>` | Approve pending action | HIGH |
| `/reject <id> <reason>` | Reject pending action | HIGH |
| `/pending` | List pending approvals | LOW |
| `/run <skill> <args>` | Execute skill (dry-run only) | MEDIUM |

## 4. Forbidden Commands

- `/shell` or any shell execution
- Access to .kratos/ or War Room internals
- Any code modification command
- Any credential/token exposure
- Any OAuth flow initiation

## 5. Security Model

- Chat ID hardcoded whitelist (only Lucas)
- Token in environment variable (never in code)
- Rate limiting: max 10 commands/minute
- Double confirmation for destructive actions
- All commands logged to audit trail

## 6. Dependencies (future, not installed)
- python-telegram-bot (for Telegram)
- Not installing during Wave 7B

## 7. Implementation Gate
Requires security audit before ANY code is written.
This document is the authorization gate.
