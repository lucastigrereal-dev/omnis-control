# P1 Content Queue & Scheduling Skeleton

**Branch:** `parallel/p1-content-queue-scheduling`
**Status:** Skeleton deployed (dry-run only)
**Date:** 2026-05-12

## Purpose

Deterministic, stdlib-only content scheduling module. Models calendar slots, queue items, and assignment decisions — without ever publishing, calling external APIs, or touching databases.

## Architecture

```
src/content_scheduler/
├── __init__.py          # Public exports
├── models.py            # Dataclasses + enums (zero deps)
└── planner.py           # ContentSchedulerPlanner service
```

## Models

| Model | Role |
|---|---|
| `ContentStatus` | Enum: draft → ready → assigned → conflict → exported |
| `PublishingChannel` | Enum: instagram_feed, instagram_story, instagram_reel, youtube, tiktok, facebook |
| `SlotPriority` | Enum: low, normal, high, urgent |
| `ContentItemDraft` | A single content draft with title, caption, channel, status, tags |
| `ContentSlot` | A schedulable time window on a channel (opens_at + duration) |
| `ScheduleWindow` | Bounded date range with guard-rails (max slots/day, min gap) |
| `CalendarPlan` | Collection of ContentSlots organized across days/channels |
| `QueuePlan` | Ordered list of ContentItemDrafts waiting for assignment |
| `SchedulingDecision` | Result of assigning one item to one slot (always dry_run=True) |

## Planner Service

`ContentSchedulerPlanner` provides:

- `build_calendar_plan(start, days, channels)` → `CalendarPlan`
- `assign_content_slots(plan, queue)` → `list[SchedulingDecision]`
- `validate_schedule_window(window)` → `list[str]` (empty = valid)
- `detect_schedule_conflicts(plan)` → `list[dict]`
- `export_calendar_csv(plan)` → CSV string
- `export_queue_json(queue)` → JSON string

## Rules (Hard Constraints)

1. **NEVER publish** — no Meta/Publer/Metricool calls
2. **NEVER schedule** in real tools — output is plan/export spec only
3. **NEVER use network** — stdlib Python only
4. **NEVER use LLM** — deterministic logic only
5. **NEVER use database** — in-memory models only
6. **NEVER touch `src/content_queue/`** — isolated module

## Usage Example

```python
from datetime import datetime
from src.content_scheduler import (
    ContentSchedulerPlanner, ContentItemDraft,
    PublishingChannel, QueuePlan,
)

planner = ContentSchedulerPlanner()
plan = planner.build_calendar_plan(
    start=datetime(2026, 5, 18),
    days=7,
)

queue = QueuePlan(label="Weekly Content")
item = ContentItemDraft(
    title="Top 5 Praias RN",
    channel=PublishingChannel.INSTAGRAM_FEED,
)
item.mark_ready()
queue.add(item)

decisions = planner.assign_content_slots(plan, queue)

csv_output = ContentSchedulerPlanner.export_calendar_csv(plan)
json_output = ContentSchedulerPlanner.export_queue_json(queue)
```

## Tests

```bash
python -m pytest tests/content_scheduler/ -q
```

## Scope Boundaries

- **Permitted:** `src/content_scheduler/`, `tests/content_scheduler/`, `docs/content_scheduler/`
- **Forbidden:** `src/content_queue/`, `src/cli.py`, `src/core/`, `src/mission/`, `src/app_factory/`, `src/automation/`, `src/governance/`, `src/analytics/`, `src/computer_ops/`, `src/finance/`, `src/commercial_sdr/`, `src/sales_crm/`, `src/marketing/`, `src/memory_pack/`, `src/design_art/`, `src/video_studio/`, `src/output_generator/`, `data/**`, `exports/**`, `logs/**`, `config/**`, `.env`, `pyproject.toml`
