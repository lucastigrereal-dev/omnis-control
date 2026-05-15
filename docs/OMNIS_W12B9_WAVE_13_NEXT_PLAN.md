# OMNIS W12B9 — Wave 13 Next Plan

**Date:** 2026-05-15

## Summary
Waves 8-12 built the secure foundations: execution engine, memory bridge, remote control, MCP/plugin system, and governance docs. Wave 13 should bridge these into production-ready integrations.

## Recommended phases (P47-P52)

### P47 — Real Akasha Sink
- Wire AkashaRuntimeService to real pgvector
- Implement real PostgreSQL connection behind dry_run gate
- Add embedding generation integration
- Performance benchmarks with real data

### P48 — Real Telegram Bot
- Wire TelegramAdapter to python-telegram-bot
- Implement webhook receiver
- Add command menu and inline keyboards
- Rate limiting with real user data

### P49 — Real MCP Bridge
- Start MCP server processes from descriptors
- Implement stdio/SSE transport adapters
- Tool discovery and invocation
- Security sandbox for spawned processes

### P50 — Real WhatsApp Integration
- Wire WhatsAppAdapter to WhatsApp Business API
- Template management and approval
- Media message handling
- Session persistence

### P51 — Observability Pipeline
- Structured logging (structlog)
- Metrics export (Prometheus-compatible)
- Health endpoint aggregation
- Alert rules definition

### P52 — Production Hardening
- End-to-end integration tests with real adapters
- Performance profiling and optimization
- Error recovery and retry policies
- Full documentation pass

## Priority order
1. P47 (Akasha) — foundation for all memory operations
2. P49 (MCP) — enables external tool ecosystem
3. P48 (Telegram) — remote control channel
4. P50 (WhatsApp) — secondary channel
5. P51 (Observability) — monitoring before production
6. P52 (Hardening) — final polish

## Decisions needed from Lucas
1. Which integration first: Akasha or Telegram?
2. Real credentials available for any service?
3. Docker environment ready for pgvector?
4. Prefer webhook or polling for Telegram?
