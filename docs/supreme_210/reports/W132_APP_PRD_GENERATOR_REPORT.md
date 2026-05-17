# W132 - App PRD Generator Report

**Date:** 2026-05-16
**Status:** COMPLETE

## Summary

W132 connects stored `AppIdea` records from `IdeaStore` to the existing deterministic `AppFactoryPlanner` and PRD generator.

## Implemented

- `src/app_factory/prd_service.py`
- `StoredIdeaPRDGenerator.generate(idea_id, dry_run=True)`
- CLI command: `omnis idea plan <idea_id>`
- Optional local JSONL persistence when `dry_run=False` and an explicit output path is supplied

## Tests

- Stored idea to PRD
- Missing idea error
- Dry-run behavior
- Non-dry-run explicit JSONL persistence
- CLI `idea plan`

## Safety

- No external calls
- No generated files unless caller passes explicit output path and `dry_run=False`
- Reuses existing planner and PRD generator
