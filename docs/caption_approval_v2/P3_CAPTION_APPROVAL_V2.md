# P3 Caption Approval V2 — Skeleton

## Status

**Wave:** 4+  
**Phase:** Skeleton (dry-run only)  
**Branch:** `parallel/p3-caption-approval-v2`

## Purpose

Modelagem determinística do pipeline de aprovação de legendas para 6 perfis Instagram (690K+ seguidores).

**NÃO APROVA, NÃO PUBLICA, NÃO MUTA FILAS.**

## Architecture

```
src/caption_approval_v2/
├── __init__.py    # Public API exports
├── models.py      # 6 dataclass models + 5 enums
└── planner.py     # CaptionApprovalPlanner service (6 static methods + full pipeline)

tests/caption_approval_v2/
├── __init__.py
├── test_models.py  # 35 tests
└── test_planner.py # 30+ tests

docs/caption_approval_v2/
└── P3_CAPTION_APPROVAL_V2.md  # This document
```

## Models

| Model | Purpose |
|---|---|
| `CaptionDraftV2` | Immutable draft — plan only, never publishes |
| `CaptionVariant` | A/B variant of a caption |
| `CaptionChecklist` | Validation checklist with severity (block/warn/info) |
| `ApprovalDecision` | Planned approval decision — never executed |
| `ApprovalPolicy` | Rule set governing decisions (default, lenient, strict) |
| `CaptionApprovalPackage` | Complete bundle: draft + variants + checklist + decision |

## Enums

| Enum | Values |
|---|---|
| `DraftStatusV2` | draft, variant_proposed, checklist_built, policy_evaluated, decision_planned, package_valid, package_invalid |
| `DecisionOutcome` | approved, rejected, needs_revision, pending |
| `ChecklistSeverity` | block, warn, info |
| `PolicyEffect` | allow, deny, flag, require_review |
| `PolicyRule` | min_chars, max_chars, has_hook, has_cta, has_hashtags, no_blocked_placeholder, brand_voice_match, compliance_check |

## Service: CaptionApprovalPlanner

All methods are `@staticmethod`. Pure functions — no side effects.

| Method | Input | Output |
|---|---|---|
| `build_caption_draft()` | Field values | `CaptionDraftV2` |
| `generate_caption_variants()` | Draft + optional specs | `list[CaptionVariant]` |
| `build_approval_checklist()` | Draft + optional policy | `CaptionChecklist` |
| `evaluate_caption_policy()` | Checklist + policy | `dict[str, bool]` |
| `plan_approval_decision()` | Draft + checklist + checks | `ApprovalDecision` |
| `validate_caption_package()` | Package | `CaptionApprovalPackage` (with validation) |
| `plan_full_approval()` | All inputs | `CaptionApprovalPackage` (end-to-end) |

## Policies

Three built-in policies via factory methods:

| Policy | Behavior |
|---|---|
| `default` | Balanced: MIN_CHARS/MAX_CHARS/no_placeholder = DENY, rest = FLAG |
| `lenient` | Relaxed: only no_placeholder = DENY, most = FLAG/ALLOW |
| `strict` | All rules = DENY on violation |

## Rules Enforced

1. **No real approvals** — all outcomes are `DecisionOutcome` enum values, never executed
2. **No queue mutation** — zero imports from `content_queue`
3. **No data/ writes** — no file I/O whatsoever
4. **No publisher integration** — package is a model, not a command
5. **Dry-run only** — every method returns a model/plan
6. **Stdlib only** — dataclasses, enums, uuid, datetime, typing
7. **No network, no LLM, no DB** — pure computation

## Scope Boundaries

**ALLOWED:**
- `src/caption_approval_v2/`
- `tests/caption_approval_v2/`
- `docs/caption_approval_v2/`

**PROHIBITED (not touched):**
- `src/caption_approval/` (legacy module)
- `src/cli.py`, `src/core/`, `src/mission/`, `src/app_factory/`
- All other `src/*/` modules
- `data/`, `exports/`, `logs/`, `config/`, `.env`, `pyproject.toml`

## Testing

Run: `python -m pytest tests/caption_approval_v2/ -q`

Tests cover:
- Model defaults, serialization, immutability
- Planner methods: all 6 static methods
- Policy factories: default, lenient, strict
- Full pipeline: `plan_full_approval()` with variants and custom policies
- Package validation: missing fields, mismatches, empty variants
