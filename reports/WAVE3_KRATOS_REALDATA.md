# WAVE 3 — KRATOS Real Data Bridge

**Date:** 2026-05-22
**Status:** COMPLETE (documentation + bridge — no KRATOS code modified per guardrail)

## Approach

Per OMNIS rule "NUNCA tocar KRATOS", this wave documents the bridge contract and creates the OMNIS-side data feeds. KRATOS code is NOT modified.

## Findings

| Block | Action | Result |
|-------|--------|--------|
| 1 | Map fake data | KRATOS store.ts + omnis/store.ts: 100% hardcoded mock |
| 2 | Map runtime sources | Health bridge, metrics spine, event bus available |
| 3 | Bridge runtime->KRATOS | `kratos_health.json` format mapped |
| 4 | Health sync | `omnis_health.json` -> `kratos_health.json` written |
| 5 | Mission sync | Mission events now in `data/missions/events/` |
| 6 | Event sync | Redis streams on :6381, 10 channels |
| 7 | Replay visibility | Replay buffer functional, graphs have manifests |
| 8 | Dashboard validation | KRATOS expects `{status, score, components}` |
| 9 | Fallback validation | If bridge file missing, KRATOS should fall back to mock |
| 10 | Report | THIS FILE |

## Bridge Contract

KRATOS consumes:
```
~/.claude/state/kratos_health.json
{
  "status": "healthy|degraded|unhealthy",
  "score": 0.0-1.0,
  "timestamp": "ISO-8601",
  "components": {
    "<name>": {"status": "...", "message": "..."}
  }
}
```

## Status
- OMNIS-side bridge: OPERATIONAL (Wave 2)
- KRATOS-side integration: PENDING (requires KRATOS code change — blocked by guardrail)
- Human decision needed: authorize KRATOS code change or keep mock fallback
