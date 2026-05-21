# OMNIS P0/P1/P2 Roadmap

**Date:** 2026-05-21

---

## P0 — Core Stability (IMMEDIATE)

| # | Item | Status | Effort | Notes |
|---|---|---|---|---|
| 1 | Health service stable | ✅ DONE | — | 47/48 healthy, :8700 active |
| 2 | Skills registry clean | ⚠️ PARTIAL | Small | 2 registries out of sync (`skills.yaml` vs `omnis_skills.yaml`) |
| 3 | Contract between axes | ✅ DONE | — | Engineering/Expression contract defined |
| 4 | Governance boundaries | ⚠️ PARTIAL | Medium | L2 active, OAuth token gating missing (P0 gap) |
| 5 | Mission Control read-only | 📋 DEFINED | Small | Requirements ready, CLI option recommended |
| 6 | KRATOS contract/auth awareness | ⚠️ PARTIAL | Medium | Bridge exists, auth layer missing |

### P0 Quick Wins (do now)
- [ ] Archive 8 idle Jarvis v1 skills → `_archived/`
- [ ] Sync `omnis_skills.yaml` with actual disk state (remove 18 non-existent entries or create skill dirs)
- [ ] Add OAuth token access to `guardian` pre-flight checks
- [ ] Create single-page CLI dashboard from existing `dashboard_cmd.py`

---

## P1 — Enhancement (SHORT-TERM)

| # | Item | Status | Effort | Notes |
|---|---|---|---|---|
| 1 | Akasha bridge integration | ⚠️ PARTIAL | Medium | `akasha_event_sink/` exists, full bridge pending |
| 2 | Publisher safe queue | ⚠️ PARTIAL | Medium | Queue exists, Meta OAuth blocks publishing |
| 3 | Capability graph | ❌ NOT STARTED | Large | Visual graph of all capabilities and dependencies |
| 4 | Evaluator loop | ❌ NOT STARTED | Medium | Post-execution evaluation → learning |
| 5 | Reporting automation | ⚠️ PARTIAL | Small | `reports/` module exists, automate aggregation |
| 6 | Install P1 forge skills | ❌ NOT STARTED | Medium | Create skill dirs for creator, forgelite, forgereal, etc. |
| 7 | L4 Policy-as-code | ❌ NOT STARTED | Large | Declarative policy engine |
| 8 | Guardian audit trail | ❌ NOT STARTED | Small | Log all guardian decisions |
| 9 | Cross-system observability | ❌ NOT STARTED | Medium | Trace requests across OMNIS → KRATOS → Akasha |

---

## P2 — Expansion (MEDIUM-TERM)

| # | Item | Status | Effort | Notes |
|---|---|---|---|---|
| 1 | Agentic planner | ❌ NOT STARTED | Large | Autonomous mission planning |
| 2 | Sandbox execution | ❌ NOT STARTED | Medium | Isolated execution environment |
| 3 | MCP fabric | ❌ NOT STARTED | Large | MCP server network |
| 4 | Skill factory | ❌ NOT STARTED | Medium | Automated skill generation |
| 5 | Semi-autonomy | ❌ NOT STARTED | Large | System operates within boundaries without human |
| 6 | Install P2 expansion skills | ❌ NOT STARTED | Medium | 8 skill dirs to create |
| 7 | Self-governance (L5) | ❌ NOT STARTED | Large | System adapts to risk automatically |

---

## Summary

| Priority | Total | Done | Partial | Not Started |
|---|---|---|---|---|
| P0 | 6 | 2 | 3 | 1 |
| P1 | 9 | 0 | 3 | 6 |
| P2 | 7 | 0 | 0 | 7 |

## Sequencing

```
Now (P0) ──────────────────────────────────────────────▶
  ├─ Archive idle Jarvis skills (hours)
  ├─ Sync skill registries (hours)
  ├─ Add OAuth gating to guardian (days)
  └─ Create CLI dashboard (days)

Next (P1) ────────────────────────────────────────────▶
  ├─ Install P1 forge skills (days)
  ├─ Guardian audit trail (hours)
  ├─ Report automation (days)
  ├─ Akasha bridge full integration (weeks)
  ├─ Cross-system observability (weeks)
  ├─ Capability graph (weeks)
  └─ L4 Policy-as-code (months)

Later (P2) ───────────────────────────────────────────▶
  ├─ Sandbox execution (weeks)
  ├─ Skill factory (weeks)
  ├─ Agentic planner (months)
  ├─ MCP fabric (months)
  └─ Semi-autonomy (months)
```

## What NOT to Do
- ❌ No heavy framework installation for any P0 item
- ❌ No cloud deployment
- ❌ No real auth implementation (use OS-level security for now)
- ❌ No swarm activation
- ❌ No external paid automation
