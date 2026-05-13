# P6 Design Art Engine — Skeleton Specification

**Date:** 2026-05-12
**Status:** COMPLETE
**Phase:** P6
**Wave:** 3

## Overview

Deterministic, dry-run, stdlib-only module for generating design briefs, visual
directions, brand visual profiles, asset specifications, carousel layouts, and
creative review packets.

**Constraints:** Zero LLM. Zero network. Zero database. Zero image generation.
No PIL/OpenCV. No Canva API. No external APIs.

## Scope

### Permitted
- `src/design_art/`
- `tests/design_art/`
- `docs/design_art/`

### Prohibited
- `src/cli.py`
- `src/core/`
- `src/mission/`
- `src/app_factory/`
- `src/automation/`
- `src/governance/`
- `src/analytics/`
- `src/computer_ops/`
- `src/finance/`
- `src/commercial_sdr/`
- `src/sales_crm/`
- `src/marketing/`
- `src/memory_pack/`
- `src/output_generator/`
- `data/**`
- `exports/**`
- `logs/**`
- `config/**`
- `.env`
- `pyproject.toml`

## Package Structure

```
src/design_art/
    __init__.py       # Public API — 60+ symbols exported
    models.py         # 6 dataclasses + 10 constant groups
    service.py        # DesignArtPlanner + ValidationResult
    errors.py         # 9 exception classes
    exporters.py      # 3 export functions (markdown)

tests/design_art/
    __init__.py
    conftest.py          # 6 fixtures (profile, direction, brief, asset, carousel, review)
    test_models.py       # model + constant tests
    test_service.py      # planner + validation tests
    test_exporters.py    # markdown export tests

docs/design_art/
    P6_DESIGN_ART_ENGINE.md
```

## Models

| Model | ID Prefix | Description |
|---|---|---|
| `BrandVisualProfile` | `bvprof_` | Core visual identity: colors, fonts, archetype, mood |
| `VisualDirection` | `vdir_` | Specific direction rule set: palette, composition, typography |
| `DesignBrief` | `dbrf_` | Complete design briefing: profile, directions, constraints |
| `AssetSpec` | `aspec_` | Placeholder spec for a single asset — no image generation |
| `CarouselLayoutSpec` | `clyt_` | Layout spec for Instagram carousel: slides, transitions |
| `CreativeReview` | `crvw_` | Review evaluation: score, status, issues, suggestions |

## Constants

| Group | Count | Values |
|---|---|---|
| `VALID_DIRECTION_TYPES` | 6 | moodboard, color_palette, typography, composition, iconography, photography |
| `VALID_ARCHETYPES` | 7 | minimalist, bold, elegant, playful, rustic, editorial, corporate |
| `VALID_DESIGN_FORMATS` | 6 | carousel, reel, story, post, banner, thumbnail |
| `VALID_ASSET_TYPES` | 7 | image, video, text_overlay, logo, background, icon, caption_bar |
| `VALID_COLOR_MODES` | 2 | rgb, cmyk |
| `VALID_FILE_FORMATS` | 5 | png, jpg, svg, mp4, webp |
| `VALID_REVIEW_STATUSES` | 3 | approved, rejected, needs_revision |
| `VALID_ASPECT_RATIOS` | 4 | 1:1, 4:5, 16:9, 9:16 |
| `VALID_TRANSITIONS` | 4 | swipe, fade, dissolve, none |

## Services

### DesignArtPlanner

| Method | Returns | Description |
|---|---|---|
| `define_brand_profile()` | `BrandVisualProfile` | Define brand visual identity |
| `define_visual_direction()` | `VisualDirection` | Define a visual direction rule set |
| `build_design_brief()` | `DesignBrief` | Build a complete design brief |
| `generate_asset_specs()` | `list[AssetSpec]` | Generate placeholder asset specs |
| `build_carousel_layout()` | `CarouselLayoutSpec` | Build carousel slide layout |
| `review_design()` | `CreativeReview` | Create a design review evaluation |
| `validate_visual_direction()` | `ValidationResult` | Validate directions against profile |

### Lookup Helpers

| Method | Returns | Description |
|---|---|---|
| `get_profile()` | `Optional[BrandVisualProfile]` | Look up profile by ID |
| `get_directions()` | `list[VisualDirection]` | Filter directions by IDs |
| `get_assets()` | `list[AssetSpec]` | Get all assets for a brief |
| `get_carousel()` | `Optional[CarouselLayoutSpec]` | Get carousel by brief ID |
| `get_review()` | `Optional[CreativeReview]` | Get review by brief ID |

### Exporters

| Function | Output | Description |
|---|---|---|
| `export_profile_markdown()` | `str` | Brand visual profile as markdown |
| `export_direction_markdown()` | `str` | Visual direction as markdown |
| `export_design_brief_markdown()` | `str` | Full design brief package as markdown (supports optional profile, directions, assets, carousel, review) |

## Design Decisions

1. **String constants over Enums** — follows project convention for domain value sets.
2. **`frozenset` for valid-values** — hashable, immutable, O(1) membership check.
3. **`.new()` factory constructors** — centralize validation before instantiation.
4. **`to_dict()` / `from_dict()` on every model** — serialization round-trip contract.
5. **`ValidationResult` dataclass** — standard lightweight result type with `.ok` property.
6. **`_dimensions_for_format()` helper** — deterministic dimension resolution for Instagram formats.
7. **Placeholder-only asset specs** — all `AssetSpec` instances carry hex placeholder colors, never actual rendered pixels.
8. **No image generation of any kind** — no PIL, no OpenCV, no Canva, no HTML-to-image.
9. **Markdown-only exports** — no CSV/JSON exporters (design briefs are inherently narrative documents).
10. **`layer_order` on AssetSpec** — enables deterministic z-ordering for layout composition.

## Verification

```bash
python -m pytest tests/design_art/ -q
```

## Next Steps (Out of Scope)

- CLI integration (`src/cli.py`)
- Actual image generation (requires PIL/OpenCV/Canva)
- Database persistence (requires PostgreSQL)
- External API calls (Canva, Figma, Remove.bg)
- Real-time collaborative review workflows
- AI-powered visual direction generation (requires LLM)
- Font file management and embedding
