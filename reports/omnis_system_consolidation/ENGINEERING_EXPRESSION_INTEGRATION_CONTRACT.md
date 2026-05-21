# Engineering ↔ Expression Integration Contract

**Date:** 2026-05-21

---

## The Two Axes

```
ENGINEERING AXIS                    EXPRESSION AXIS
┌──────────────────────┐            ┌──────────────────────┐
│ architect            │            │ content-machine      │
│ schema-planner       │            │ seogram-engine       │
│ scaffolder           │    ⇄      │ campaign-planner     │
│ builder              │            │ brand                │
│ qa → auditor         │            │ design               │
│ merge-gate           │            │ publisher pipeline   │
│ registry             │            │ video_studio         │
└──────────────────────┘            └──────────────────────┘
         │                                   │
         └────────── OMNIS Control ──────────┘
```

## What Engineering Delivers to Expression

| Artifact | From | To | Format |
|---|---|---|---|
| App scaffold | `scaffolder` | Content systems | Directory structure |
| API contracts | `schema-planner` | Publisher integration | OpenAPI/Schema |
| Automation workflows | `automation/` | n8n publishing | n8n templates |
| Capabilities | `capabilityforge/` | Expression pipeline | YAML registry |
| Quality gates | `qa` → `auditor` | Content validation | Test reports |
| Infrastructure | `execution-runner` | Publisher OS | Docker/services |
| Event bus | `omnis_bus/` | Cross-axis events | Redis Pub/Sub |

## What Expression Requests from Engineering

| Request | From | To | Via |
|---|---|---|---|
| New content capability | Expression team | `capabilityforge/` | Work order |
| Publisher fix/enhance | Publisher OS | `kratos_bridge/` | Mission |
| Analytics dashboard | Campaign metrics | `analytics/` | Report |
| Approval flow update | `caption_approval/` | `approval_runtime/` | Config |
| Export format | Client delivery | `output_factory/` | Template |
| Video rendering fix | `video_studio/` | Engineering | Bug report |

## Capabilities Connecting Both Axes

| Capability | Domain | Connects |
|---|---|---|
| `cross_cutting.redis.bus` | Infrastructure | Both — event backbone |
| `cross_cutting.health.check` | Observability | Both — system health |
| `omnis.content.crew` | Orchestration | Expression production via Engineering infra |
| `publisher_os.seogram.skill` | Content | Expression skill on Engineering platform |
| `external.meta.oauth` | External | Expression publishing blocker |

## Data Flow Boundaries

### Can Circulate
- Content drafts (text, captions, briefs)
- Performance metrics (engagement, reach)
- Campaign status (active, paused, completed)
- Pipeline state (in_progress, blocked, done)
- Skill execution results

### Privacy Boundary (Requires Care)
- Client lead data (SDR pipeline)
- Revenue/commission data
- OAuth tokens (never logged)
- Personal contact info

### Requires Approval
- Publishing to Instagram
- Sending DMs to leads
- Deleting production data
- Modifying financial records

## Example Flow: Content Request → Publication

```
1. Expression: campaign-planner creates brief
2. Expression: content-machine generates draft
3. Cross: caption-approval reviews draft
4. Expression: seogram-engine optimizes SEO
5. Cross: approval_gate validates (requires human?)
6. Engineering: publisher pipeline queues post
7. Expression: ARGOS bridge publishes
8. Cross: metrics collected → learning loop
```

## Contract Enforcement

| Mechanism | Tool | Status |
|---|---|---|
| Approval gates | `approval_runtime/` | ✅ Active |
| Permission boundaries | `guardian` | ✅ Active |
| Work orders | `work_order/` | ✅ Active |
| Execution contracts | `execution_contracts/` | ✅ Active |
| Skill boundaries | `skill_execution/boundaries.py` | ✅ Active |

## Summary
**Contract Status: DEFINED.** Both axes have clear boundaries and multiple connection points. The event bus (`cross_cutting.redis.bus`) is the primary integration backbone. Work orders and approval gates enforce the contract at runtime.
