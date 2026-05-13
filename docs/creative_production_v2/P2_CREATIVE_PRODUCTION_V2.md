# P2 Creative Production V2 — Skeleton

**Status:** ✅ Implemented
**Branch:** `parallel/p2-creative-production-v2`
**Date:** 2026-05-13

## Overview

Creative Production V2 is a deterministic, dry-run, stdlib-only pipeline for planning
creative production workflows. It replaces the legacy `src/creative_production/` module
with a clean v2 architecture that never generates real images, renders real HTML, or
calls external APIs.

## Architecture

```
CreativeRequest
    │
    ▼
build_creative_brief()  →  CreativeBriefV2
    │
    ▼
plan_production_assets() →  ProductionAssetPlan
    │
    ▼
build_production_batch() →  ProductionBatch
    │
    ▼
plan_creative_review()   →  CreativeReviewPlan
    │
    ▼
validate_creative_package() → CreativePackage
    │
    ▼
export_creative_package_markdown() → str
```

## Models

| Model | Description |
|---|---|
| `CreativeRequest` | Input request — account, format, topic, objective, tone, etc. |
| `CreativeBriefV2` | Deterministic creative brief with hooks, shots, design notes |
| `AssetSpec` | Single asset specification — type, dimensions, description |
| `ProductionAssetPlan` | Complete asset plan with tool assignments and templates |
| `CreativeTask` | Individual unit of work — type, tool, dependencies, status |
| `ProductionBatch` | Batch of tasks with parallel/sequential analysis |
| `ReviewCheckpoint` | Single review checkpoint with criteria |
| `CreativeReviewPlan` | Full review plan with checkpoints and verdict |
| `CreativePackage` | Final bundle: brief + asset plan + batch + review |

## Enums

| Enum | Values |
|---|---|
| `CreativeFormat` | carousel, reel, photo, video, story, multi_copy |
| `CreativeStatus` | draft, planned, in_production, review, approved, rejected, ready, archived |
| `AssetType` | image, video, audio, text_overlay, logo, background, thumbnail, caption_card |
| `TaskStatus` | pending, in_progress, done, skipped, blocked, failed |
| `ReviewVerdict` | pending, approved, changes_requested, rejected |
| `PackageStatus` | draft, validated, ready, exported, archived |

## Service: CreativeProductionPlanner

| Method | Input | Output | Description |
|---|---|---|---|
| `build_creative_brief` | `CreativeRequest` | `CreativeBriefV2` | Transforms request into structured brief |
| `plan_production_assets` | `CreativeBriefV2` | `ProductionAssetPlan` | Plans all required assets |
| `build_production_batch` | `ProductionAssetPlan`, `CreativeBriefV2` | `ProductionBatch` | Creates task batch with dependencies |
| `plan_creative_review` | `CreativeBriefV2` | `CreativeReviewPlan` | Creates review checkpoints |
| `validate_creative_package` | `CreativePackage` | `CreativePackage` | Validates and populates errors/warnings |
| `export_creative_package_markdown` | `CreativePackage` | `str` | Exports as markdown string |
| `plan_from_request` | `CreativeRequest` | `CreativePackage` | Full pipeline in one call |

## Rules

- ❌ No real image generation
- ❌ No real HTML rendering
- ❌ No Canva/Figma/external API calls
- ❌ No network, no LLM, no database
- ❌ No PIL/OpenCV
- ✅ Dataclasses + enums + stdlib only
- ✅ All operations are deterministic / dry-run
- ✅ Same input → Same output (except UUIDs)

## Files

```
src/creative_production_v2/
├── __init__.py    # Package init with re-exports
├── models.py      # All dataclass models + enums
└── planner.py     # CreativeProductionPlanner service

tests/creative_production_v2/
├── __init__.py
├── test_models.py  # 40+ tests for all models
└── test_planner.py # 40+ tests for planner pipeline

docs/creative_production_v2/
└── P2_CREATIVE_PRODUCTION_V2.md  # This file
```

## Test Coverage

- **test_models.py**: Model creation, to_dict/from_dict roundtrips, enum values, edge cases
- **test_planner.py**: Deterministic output, all pipeline steps, validation, markdown export, format variations

## Usage

```python
from src.creative_production_v2 import CreativeProductionPlanner, CreativeRequest, CreativeFormat

planner = CreativeProductionPlanner()

request = CreativeRequest(
    account_handle="@lucastigrereal",
    format=CreativeFormat.CAROUSEL,
    topic="Viagem em família para Natal",
    objective="Vender pacote Growth",
    tone="inspirador",
)

package = planner.plan_from_request(request)
markdown = planner.export_creative_package_markdown(package)
print(markdown)
```
