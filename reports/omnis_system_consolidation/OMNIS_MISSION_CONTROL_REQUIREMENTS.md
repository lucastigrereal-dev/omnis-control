# OMNIS Mission Control Requirements

**Date:** 2026-05-21  
**Status:** V1 READ-ONLY (requirements defined, no frontend implementation)

---

## Design Principles

1. **Read-only first** — V1 is dashboard only, no mutations
2. **Single source of truth** — data comes from OMNIS Health (:8700), registry, and git state
3. **No new backend** — leverage existing health endpoint and file system
4. **Local-only** — no cloud deployment for V1
5. **Minimal dependencies** — static HTML/JS or CLI output, not a full app

---

## Cards / Views

### 1. Health Overview
| Metric | Source |
|---|---|
| Health status | `GET :8700/health → status` |
| Total skills | `total_skills` |
| Healthy | `healthy` |
| Stale | `stale` |
| Missing metadata | `missing_metadata` |
| Last health check | Snapshot timestamp |

### 2. Skills Registry
| Column | Source |
|---|---|
| Skill name | Health response |
| Status | `status` |
| Last used | `last_used` |
| Priority (P0/P1/P2) | `omnis_skills.yaml` |
| Category | Skills inventory classification |

### 3. Capabilities Grid
| Column | Source |
|---|---|
| Capability ID | `capabilities.yaml` |
| Domain | kratos, akasha, omnis, etc. |
| Layer | transport, application, etc. |
| Status | active, planned, candidate |
| Risk | low, medium, high |

### 4. Engineering Pipeline Status
| Stage | Skills | Status |
|---|---|---|
| Design | architect → schema-planner | ✅ |
| Build | scaffolder → builder | ✅ |
| Quality | qa → auditor | ✅ |
| Governance | guardian → merge-gate | ✅ |
| Orchestration | orchestrator → execution-runner | ✅ |

### 5. Expression Pipeline Status
| Stage | Module | Status |
|---|---|---|
| Content | content_factory/ | ✅ |
| Design | design_art/ | ✅ |
| Approval | approval_center/ | ✅ |
| Publishing | publisher/ + argos_bridge/ | ✅ (blocked by Meta OAuth) |
| Video | video_studio/ | ✅ |

### 6. Integration Status
| Integration | Status |
|---|---|
| OMNIS ↔ KRATOS | ✅ bridged |
| OMNIS ↔ AKASHA | ✅ event sink |
| OMNIS ↔ Publisher OS | ✅ MCP |
| OMNIS ↔ n8n | ✅ bridge |
| KRATOS ↔ AKASHA | ⚠️ pending |
| Publisher OS ↔ Instagram | ❌ blocked (Meta OAuth) |

### 7. Blockers
| Blocker | Affects | Priority |
|---|---|---|
| Meta OAuth credentials pending | Instagram publishing | P0 |
| No auth between OMNIS ↔ KRATOS | Security | P0 |
| OAuth token not gated by guardian | Security | P0 |
| 18 P1/P2 skills not installed | Completeness | P1 |
| Two skill registries out of sync | Consistency | P1 |

### 8. Next Action
Based on `control_tower/next_action.py`:
- **Immediate:** Resolve Meta OAuth blocker (requires Lucas to fill .env vars)
- **Short-term:** Sync skill registries, archive idle Jarvis v1 skills
- **Medium-term:** Build auth layer between OMNIS ↔ KRATOS

### 9. Risk Map
| Risk | Level | Mitigation |
|---|---|---|
| Redis single point of failure | HIGH | None yet (P1) |
| No auth between systems | HIGH | P0 — needs auth layer |
| 20-agent CrewAI stability | HIGH | monitor jobs |
| Skill registry drift | MEDIUM | sync script |
| 8 idle Jarvis skills | LOW | archive or delete |

### 10. Commit Map (recent activity)
| Repo | Branch | Ahead | Modified |
|---|---|---|---|
| omnis-control | feature/omnis-5waves-runtime-supreme | — | 47 files |
| kratos-mission-control | feature/fase14-integration | 4 commits | 2 files |

---

## Implementation Options for V1

### Option A: CLI Dashboard (recommended)
- `python -m omnis_control.cli dashboard` — already exists patterns in `cli_commands/dashboard_cmd.py`
- Zero dependencies
- Terminal output with color

### Option B: Static HTML Dashboard
- Read health JSON + registry YAML → generate single HTML file
- No server needed
- Opens in browser

### Option C: Cockpit Extension
- Add card to existing Cockpit (:3200)
- Requires Cockpit to be running

**Recommendation:** V1 = Option A (CLI). Extend `dashboard_cmd.py` with OMNIS-specific cards.

## What NOT to Do
- ❌ No real-time WebSocket (overengineering for V1)
- ❌ No database (use existing health + registry)
- ❌ No authentication (V1 is local only)
- ❌ No deployment (V1 runs from omnis-control repo)
