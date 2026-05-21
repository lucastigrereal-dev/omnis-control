# Expression Axis Map — OMNIS Communication Pipeline

**Date:** 2026-05-21

---

## Pipeline: Content Strategy → Production → Approval → Publication → Metrics

```
strategy/brief → draft → seo → approval → queue → publish → metrics → learn
                                                                    │
                                                            brand voice loop
```

## Expression Skills (11 on disk)

### Content Production (6)
| Skill | Status | Role |
|---|---|---|
| `content-machine` | ✅ healthy | Content production |
| `seogram-engine` | ✅ healthy | SEO-optimized Instagram captions |
| `campaign-planner` | ✅ healthy | Campaign planning & strategy |
| `content-variant-maker` | ✅ healthy | A/B content variants |
| `hub-social` | ✅ healthy | Social media hub |
| `humanizer` | ✅ healthy | Humanizes AI-generated text |

### Design (4)
| Skill | Status | Role |
|---|---|---|
| `brand` | ✅ healthy | Brand voice and identity |
| `design` | ✅ healthy | Visual design |
| `design-system` | ✅ healthy | Design system management |
| `banner-design` | ✅ healthy | Banner creation |
| `slides` | ✅ healthy | Slide creation |

## OMNIS Control — Expression Modules

| Module | Description | Status |
|---|---|---|
| `content_factory/` | Approval flow, brand voice, brief, calendar, carousel, reels, stories, seogram, batch export | ✅ Complete |
| `content_queue/` | Queue with accounts, models | ✅ Complete |
| `content_scheduler/` | Planner and scheduling models | ✅ Complete |
| `caption_approval/` | Caption drafts and approval workflow | ✅ Complete |
| `publisher/` | Pipeline, state machine, approval gate, export, metrics, worker | ✅ Complete |
| `publisher_argos/` | ARGOS bridge planner | ✅ Complete |
| `argos_bridge/` | Draft builder, exporter | ✅ Complete |
| `campaign_manager/` | Campaign management service | ✅ Complete |
| `campaign_auditor/` | Campaign auditing | ✅ Complete |
| `campaign_package/` | Campaign packaging and export | ✅ Complete |
| `creative_production/` | Briefs, exporter, HTML renderer, mock images, review, production queue | ✅ Complete |
| `approval_center/` | Approval service, store, errors | ✅ Complete |
| `approval_runtime/` | Runtime approval policy, tokens, store | ✅ Complete |
| `first_post/` | Preflight, package, models | ✅ Complete |
| `marketing/` | Exporters, service, models | ✅ Complete |
| `client_delivery/` | Client export, service, models | ✅ Complete |
| `delivery_portal/` | Delivery portal models | Partial |
| `delivery_templates/` | Service and models | ✅ Complete |
| `design_art/` | Brand presets, consistency checker, exporters | ✅ Complete |
| `render_engine/` | HTML rendering service | ✅ Complete |
| `video_studio/` | Full video pipeline: ingest, captions, cut plan, hooks, render, SRT, transcription, A/B | ✅ Complete |
| `video_assets/` | Asset queue, registry, scanner, status | ✅ Complete |
| `video_production/` | Production service | ✅ Complete |

## What's Legacy
- `manual_publishing/` — likely superseded by automated pipeline
- `first_post/` — one-shot, may be legacy

## What's Partial
- `delivery_portal/` — models defined but service structure not fully baked
- `preview/` — only carousel_preview.py

## What Needs to Become a Formal Capability

1. **Brand Voice** (`content_factory/brand_voice.py`) — exists as code but not a registered capability
2. **Calendar Auto** (`content_scheduler/`) — exists but no skill wrapper
3. **Approval Gate** (`caption_approval/`, `approval_center/`) — exists but not a formal capability
4. **Batch Export** (`content_factory/batch_export.py`) — exists as code
5. **Video Pipeline** (`video_studio/`) — mature but no skill wrapper

## Integration with External Systems

| System | Via | Status |
|---|---|---|
| ARGOS (Publisher OS MCP) | `argos_bridge/` | ✅ Active |
| n8n | `automation/n8n_bridge.py` | ✅ Active |
| Instagram (Meta OAuth) | `oauth_readiness/` | ❌ Blocked — pending credentials |

## Expression Axis Summary
**Status: OPERATIONAL.** Content production, design, and publishing pipeline are implemented in Python modules. 11 skills on disk. Full video pipeline exists. The main blocker is Meta OAuth for Instagram publishing.
