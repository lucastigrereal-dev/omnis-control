# P5 Marketing Supreme — Skeleton Specification

**Date:** 2026-05-12
**Status:** COMPLETE
**Phase:** P5
**Wave:** 3

## Overview

Deterministic, dry-run, stdlib-only module for planning marketing campaigns,
content calendars, campaign packages, post briefings, CTAs, and export specs.

**Constraints:** Zero LLM. Zero network. Zero database. No pandas.

## Scope

### Permitted
- `src/marketing/`
- `tests/marketing/`
- `docs/marketing/`

### Prohibited
- `src/cli.py`
- `src/core/`
- `src/mission/`
- `src/app_factory/`
- `src/automation/`
- `src/governance/`
- `src/analytics/`
- `src/computer_ops/`
- `src/output_generator/`
- `data/**`
- `exports/**`
- `logs/**`
- `config/**`
- `.env`
- `pyproject.toml`

## Package Structure

```
src/marketing/
    __init__.py       # Public API — 69 symbols exported
    models.py         # 6 dataclasses + 8 constant groups
    service.py        # MarketingPlanner + ValidationResult
    errors.py         # 8 exception classes
    exporters.py      # 3 export functions (md, csv, json)

tests/marketing/
    __init__.py
    test_models.py    # 33 tests
    test_service.py   # 23 tests
    test_exporters.py # 9 tests

docs/marketing/
    P5_MARKETING_SUPREME_SKELETON.md
```

## Models

| Model | ID Prefix | Description |
|---|---|---|
| `MarketingObjective` | `mktobj_` | Measurable marketing goal with target metric |
| `AudienceProfile` | `aud_` | Target audience definition with demographics |
| `ContentPillar` | `pil_` | Thematic pillar with topics, formats, frequency |
| `ContentItem` | — | Single content delivery slot in a plan |
| `CampaignBrief` | `cmp_` | Campaign blueprint with objective, audience, messaging |
| `ContentPlan` | `pln_` | Scheduled content calendar |
| `CampaignPackage` | `pkg_` | Assembled deliverable (brief + plan + validation) |

## Constants

| Group | Count | Values |
|---|---|---|
| `VALID_OBJECTIVE_TYPES` | 4 | awareness, engagement, conversion, retention |
| `VALID_PRIORITIES` | 4 | low, medium, high, critical |
| `VALID_PILLAR_TYPES` | 4 | educational, entertaining, inspirational, promotional |
| `VALID_CONTENT_FORMATS` | 5 | carousel, reel, multi_copy, story, post |
| `VALID_PLATFORMS` | 4 | instagram, facebook, tiktok, youtube |
| `VALID_FREQUENCIES` | 4 | daily, weekly, biweekly, monthly |
| `VALID_TONES` | 5 | professional, casual, humorous, inspirational, urgent |
| `VALID_CTAS` | 7 | link_bio, dm, comment, share, save, visit, book |

## Services

### MarketingPlanner

| Method | Returns | Description |
|---|---|---|
| `define_objective()` | `MarketingObjective` | Define a marketing goal |
| `define_audience()` | `AudienceProfile` | Define target audience |
| `define_pillar()` | `ContentPillar` | Define content pillar |
| `build_campaign_brief()` | `CampaignBrief` | Build campaign blueprint |
| `generate_content_plan()` | `ContentPlan` | Generate content calendar from pillars |
| `build_campaign_package()` | `CampaignPackage` | Assemble full deliverable |
| `validate_campaign()` | `ValidationResult` | Validate brief + plan consistency |

### Exporters

| Function | Output | Description |
|---|---|---|
| `export_campaign_package_markdown()` | `str` | Full campaign spec as markdown |
| `export_content_calendar_csv()` | `str` | Content items as CSV |
| `export_content_calendar_json()` | `str` | Content items as JSON |

## Design Decisions

1. **String constants over Enums** — follows project convention (e.g., `TRIGGER_WEBHOOK = "webhook"`).
2. **`frozenset` for valid-values** — hashable, immutable, allows O(1) membership check.
3. **`.new()` factory constructors** — centralize validation before instantiation.
4. **`to_dict()` / `from_dict()` on every model** — serialization round-trip contract.
5. **`ValidationResult` dataclass** — lightweight result type for validation outcomes.
6. **Defensive copies in properties** — prevents external mutation of internal state.
7. **Dry-run by default** — no side effects unless explicitly opted into.
8. **Stdlib CSV via `io.StringIO`** — no file system writes required for export tests.

## Verification

```bash
python -m pytest tests/marketing/ -q
```

## Next Steps (Out of Scope)

- CLI integration (`src/cli.py`)
- Multi-language post generation (requires LLM)
- Database persistence (requires PostgreSQL/pgvector)
- External API posting (requires Meta/Instagram API)
- Advanced analytics/reporting dashboard
