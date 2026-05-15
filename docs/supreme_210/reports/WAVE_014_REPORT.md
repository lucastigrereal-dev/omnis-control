# WAVE 014 — Mission CLI Commands — REPORT
**Date:** 2026-05-15 | **Status:** COMPLETE (VERIFIED) | **Skills:** sc:audit

## Blocos: 10/10 PASS

Existing CLI verified — 8 Typer commands with Rich formatting:
- create: --title, --objective, --sector, --request, --risk-level, --approval, budget flags
- list: with --status filter
- show: full contract display with prefix matching
- pause, resume, retry, checkpoint, resume-context
- ID resolution via _resolve_id() with prefix matching
- Rich Table, Panel, Console for output

## Files (existing, verified)
- `src/cli_commands/missions_cmd.py` — 488 lines
