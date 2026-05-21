# OMNIS ↔ KRATOS Integration Map

**Date:** 2026-05-21

---

## System Topology

```
                    ┌─────────────────────────────────────────────────┐
                    │                  OMNIS Control                   │
                    │  ~/omnis-control/                                │
                    │  Branch: feature/omnis-5waves-runtime-supreme    │
                    │  300+ source files, 70+ modules, 47 skills      │
                    └──────────┬──────────────┬───────────────────────┘
                               │              │
                    ┌──────────▼──┐    ┌──────▼───────────────────────┐
                    │  OMNIS Bus  │    │  Health Service (:8700)       │
                    │  Redis P/S  │    │  47/48 skills healthy         │
                    │  :6382      │    │  0 stale, 0 missing metadata  │
                    └──────────┬──┘    └──────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
 ┌────────▼────────┐  ┌───────▼────────┐  ┌───────▼────────────┐
 │    KRATOS        │  │    AKASHA       │  │   Publisher OS     │
 │  FastAPI          │  │  pgvector :5432 │  │   Content Crew     │
 │  :8701 (?)        │  │  20K docs       │  │   :8000            │
 │  Branch:          │  │  606K chunks    │  │                    │
 │  fase14-integrati │  │                │  │   LiteLLM :4002    │
 │  on               │  │                │  │   Ollama :11434    │
 └────────┬────────┘  └────────────────┘  └────────────────────┘
          │
 ┌────────▼────────┐
 │  Mission Control │
 │  Cockpit         │
 │  Dashboard       │
 │  Reports         │
 └─────────────────┘
```

## Who Calls Who

| Caller | Callee | Method | Purpose |
|---|---|---|---|
| OMNIS Control | KRATOS | REST/SSE | Mission dispatch, live stream, operational truth |
| OMNIS Control | Health Service (:8700) | REST (GET /health) | Skill health monitoring |
| OMNIS Bus (Redis) | KRATOS | Pub/Sub | System events, heartbeats |
| KRATOS | AKASHA | pgvector SQL | Memory queries, context retrieval |
| KRATOS | Publisher OS | REST (planned) | Content publishing pipeline |
| OMNIS Control | AKASHA | Event sink | Memory writes from missions |
| OMNIS Control | Publisher OS | MCP (publisher-os MCP) | Content production jobs |

## Source of Truth Mapping

| Concern | Source of Truth | Where Used |
|---|---|---|
| Skills catalog | `~/.claude/registry/skills.yaml` | OMNIS Health, Claude Code |
| OMNIS capabilities | `~/.claude/registry/capabilities.yaml`, `omnis_skills.yaml` | OMNIS Control, Health |
| Mission state | OMNIS Control `src/missions/` | KRATOS (via bridge) |
| KRATOS runtime state | KRATOS FastAPI | OMNIS Control (via kratos_bridge) |
| Health status | OMNIS Health (:8700) | Systems monitoring |
| Memory | AKASHA pgvector | All systems |
| Content briefs | OMNIS Control `content_factory/` | Publisher OS |
| Instagram accounts | Publisher OS | ARGOS |

## Duplicities Found

| Data | Where | Conflict |
|---|---|---|
| `skills.yaml` vs `omnis_skills.yaml` | Both registries | `skills.yaml` has 8+15+4; `omnis_skills.yaml` has 30. No sync mechanism. |
| Mission definitions | `src/missions/` + templates in `templates/ops/` | Templates duplicate in-mission definitions |
| Skill health | OMNIS Health (:8700) has its own skill tracking | May diverge from registry |

## Gaps Found

| Gap | Impact | Priority |
|---|---|---|
| No single system topology registry | Hard to know what talks to what | P1 |
| No auth/contract layer between OMNIS ↔ KRATOS | No security boundary | P0 |
| Publisher OS ↔ KRATOS integration not implemented | Expression pipeline can't use KRATOS services | P1 |
| No observability across systems | Can't trace a request across boundaries | P1 |
| `omnis_skills.yaml` out of sync with disk | 18 skills declared but not installed | P1 |

## KRATOS State

| Field | Value |
|---|---|
| Branch | `feature/fase14-integration` |
| Ahead of remote | 4 commits |
| Modified files | 2 (mission.py, event_bridge.py) |
| Untracked | Mission bus, runtime agent, registry tests, reports |
| Key service | `event_bridge.py` — Redis Pub/Sub bridge |
| Key route | `mission.py` — Mission management |

## Integration Contract

```
OMNIS Control ──kratos_bridge──▶ KRATOS FastAPI
     │                                 │
     │ omnis_bus (Redis)               │ event_bridge (Redis)
     │                                 │
     └───────────── Pub/Sub ───────────┘
```

The `kratos_bridge/` module in OMNIS Control provides:
- `health_monitor.py` — monitors KRATOS health
- `event_stream.py` — SSE stream consumer
- `dispatcher.py` — dispatches missions to KRATOS
- `permission_gate.py` — permission enforcement
- `queue_manager.py` — queue management
- `snapshot.py` — state snapshot reader
- `view_router.py` — view routing
