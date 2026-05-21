# Skills & Capabilities Inventory — OMNIS

**Date:** 2026-05-21  
**Sources:** OMNIS Health (:8700), `~/.claude/registry/skills.yaml`, `~/.claude/registry/omnis_skills.yaml`, `~/.claude/registry/capabilities.yaml`, `~/.claude/registry/sectors.yaml`

---

## Registry YAML Summary

| Registry | Contents | Status |
|---|---|---|
| `skills.yaml` | 8 Jarvis core + 15 custom skills + 4 deprecated | ✅ Active |
| `omnis_skills.yaml` | 30 skills (12 P0, 10 P1, 8 P2) — canonical OMNIS | ✅ Active |
| `capabilities.yaml` | 14 seed capabilities (ABA1) | ✅ Live |
| `sectors.yaml` | 7 sectors with skill mapping | ✅ Active |
| `agents.yaml` | Agents config | Present |
| `guardrails.yaml` | Safety rules | Present |
| `decision_engine.yaml` | Priority formula | Present |
| `workflows.yaml` | Workflow definitions | Present |
| `models.yaml` | Model mappings | Present |
| `memory_sources.yaml` | Memory source config | Present |

## Capabilities (14 registered)

| ID | Domain | Layer | Status | Risk |
|---|---|---|---|---|
| `kratos.live.stream` | kratos | transport | active | medium |
| `kratos.operational.truth` | kratos | application | active | medium |
| `kratos.event.bridge` | kratos | infrastructure | active | medium |
| `akasha.event.listener` | akasha | transport | active | low |
| `akasha.pgvector.source` | akasha | memory | active | medium |
| `omnis.content.crew` | omnis | orchestration | active | high |
| `omnis.mission.package` | omnis | orchestration | planned | high |
| `gringotts.treasury.schema` | gringotts | domain | candidate | low |
| `gringotts.cost.callback` | gringotts | application | candidate | medium |
| `publisher_os.seogram.skill` | publisher_os | content | active | low |
| `cross_cutting.redis.bus` | cross_cutting | infrastructure | active | high |
| `cross_cutting.health.check` | cross_cutting | observability | active | low |
| `external.supabase.hotels` | external | external | active | medium |
| `external.meta.oauth` | external | external | planned | high |

## Skill Classification

### OMNIS P0 — Engineering Pipeline (12)
| Skill | Status | Last Used |
|---|---|---|
| architect | healthy | 2026-05-19 |
| architect-omnis | healthy | 2026-05-20 |
| schema-planner | healthy | 2026-05-20 |
| scaffolder | healthy | 2026-05-20 |
| builder | healthy | 2026-05-20 |
| qa | healthy | 2026-05-20 |
| auditor | healthy | 2026-05-20 |
| refactor | healthy | 2026-05-20 |
| orchestrator | healthy | 2026-05-20 |
| guardian | healthy | 2026-05-20 |
| execution-runner | healthy | 2026-05-20 |
| merge-gate | healthy | 2026-05-20 |

### OMNIS P1 — Forge (listed but paths not in `~/.claude/skills/`)
| Skill | Status in omnis_skills.yaml | Path |
|---|---|---|
| creator | active | `~/.claude/skills/creator/SKILL.md` — NOT FOUND |
| forgelite | active | `~/.claude/skills/forgelite/SKILL.md` — NOT FOUND |
| forgereal | active | `~/.claude/skills/forgereal/SKILL.md` — NOT FOUND |
| repo-intake | active | `~/.claude/skills/repo-intake/SKILL.md` — NOT FOUND |
| dependency-audit | active | NOT FOUND |
| adapter-builder | active | NOT FOUND |
| bridge-builder | active | NOT FOUND |
| matcher | active | NOT FOUND |
| composer | active | NOT FOUND |
| decomposer | active | NOT FOUND |

### OMNIS P2 — Expansion (listed but NOT in `~/.claude/skills/`)
model-orchestration, worldactions, control, scheduler, missions, improvement, observability-local, report — **NOT FOUND on disk**

### Legacy Engineering (4)
| Skill | Status | Note |
|---|---|---|
| integration-architect | healthy | Cross-system integration |
| memory-architect | healthy | Memory architecture |
| roadmap-planner | healthy | Roadmap planning |
| mission-control-mapper | healthy | MC cockpit mapping |

### Governance & Safety (5)
| Skill | Status | Note |
|---|---|---|
| guardian | healthy | Pre-flight validation |
| qa-guard | healthy | Quality gate |
| merge-gate | healthy | Merge decision |
| git_guardian | healthy | Git safety |
| webhook-guardian | healthy | Webhook safety |
| workflow-validator | healthy | Workflow validation |
| workflow-versioning | healthy | Version control |

### Expression / Content Production (11)
| Skill | Status | Note |
|---|---|---|
| content-machine | active (skills.yaml) | Content production |
| seogram-engine | active | SEO captions |
| campaign-planner | active | Campaign planning |
| content-variant-maker | active | A/B variants |
| hub-social | active | Social hub |
| brand | healthy | Brand voice |
| humanizer | healthy | Humanization |
| design | healthy | Visual design |
| design-system | healthy | Design system |
| banner-design | healthy | Banner creation |
| slides | healthy | Slide creation |

### Jarvis v1 — Stale / Idle (8)
| Skill | Last Used | Note |
|---|---|---|
| jarvis-brain | 2026-04-29 | Absorbed by OMNIS |
| jarvis-decide | 2026-04-29 | Replaced by control_tower |
| jarvis-delegate | 2026-04-29 | Replaced by orchestrator |
| jarvis-guardrails | 2026-04-29 | Replaced by guardian |
| jarvis-memory-write | 2026-04-29 | Absorbed by Akasha |
| jarvis-morning | 2026-04-29 | Replaced by OMNIS briefing |
| jarvis-router | 2026-04-29 | Replaced by OMNIS router |
| skill-creator | 2026-04-29 | Replaced by P1 forge |

### Deprecated (in skills.yaml)
| Skill | Replaced By |
|---|---|
| knowledge-retriever | jarvis-brain |
| morning-briefing | jarvis-morning |
| organizer | jarvis-morning |
| context-restorer | jarvis-brain |

### Cross-cutting / Meta (6)
| Skill | Status | Role |
|---|---|---|
| registry | healthy | Canonical catalog |
| skill-router | healthy | Skill routing |
| skill-creator | healthy | Skill creation |
| using-superpowers | healthy | Meta-orchestration |
| systematic-debugging | healthy | Debugging |
| brainstorming | healthy | Ideation |
| cost-analyst | healthy | Cost analysis |

### Observability (3)
| Skill | Status |
|---|---|
| qa-guard | healthy |
| auditor | healthy |
| tester | healthy |

### Archived / Empty
- `_archived` — empty directory, placeholder

## Summary Counts

| Category | Count |
|---|---|
| OMNIS P0 (on disk) | 12 ✅ |
| OMNIS P1 (declared, NOT on disk) | 10 ❌ |
| OMNIS P2 (declared, NOT on disk) | 8 ❌ |
| Expression / Content | 11 |
| Jarvis v1 (idle) | 8 |
| Governance & Safety | 7 |
| Legacy Engineering | 4 |
| Cross-cutting / Meta | 7 |
| Observability | 3 |
| Deprecated | 4 |
| Archived | 1 |
| **Total on disk** | **47** |
| **Total declared (omnis_skills.yaml)** | **30** |

## Gaps
1. **10 P1 skills declared but not installed** — `omnis_skills.yaml` lists them but directories don't exist in `~/.claude/skills/`
2. **8 P2 skills declared but not installed**
3. **8 Jarvis v1 skills idle >22 days** — safe to archive
4. **No `observability-engineer` skill** — monitoring is split across qa-guard, auditor, health service
