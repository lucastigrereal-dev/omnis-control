# OMNIS Supreme Local 100% — Operating Manual

**Version:** v1.0.0
**Date:** 2026-05-18
**Scope:** Fully offline autonomous operation

---

## Quick Reference

```bash
# Run all Supreme tests
python -m pytest tests/template_registry/ tests/local_search/ tests/mission_replay/ \
  tests/output_versioning/ tests/backlog/ tests/parallel_runner/ tests/quality_gate/ \
  tests/app_factory_exec/ tests/video_studio/test_render_presets.py \
  tests/video_studio/test_ab_comparison.py tests/design_art/test_brand_presets.py \
  tests/design_art/test_consistency_checker.py \
  --import-mode=importlib -p no:warnings -q

# Run a single module
python -m pytest tests/<module>/ --import-mode=importlib -p no:warnings -v
```

---

## Module Operations

### S01 — Template Registry

```python
from src.template_registry import TemplateRegistry

registry = TemplateRegistry()
registry.list_by_category("marketing")
registry.search("hotel")
registry.promote("template-id")
```

### S02 — Local Search

```python
from src.local_search import SearchEngine

engine = SearchEngine()
results = engine.search("viagem natal hotel", limit=10)
engine.stats()  # Index size, term count
```

CLI:
```bash
python -m src.local_search.cli "hotel natal" --source mission --limit 5
python -m src.local_search.cli --stats
```

### S03 — Mission Replay

```python
from src.mission_replay import MissionReplay

replay = MissionReplay()
replay.list_missions()
session = replay.create_replay("mission-id", dry_run=True)
diff = replay.diff("session-id")
```

### S04 — Output Versioning

```python
from src.output_versioning import OutputVersioner

versioner = OutputVersioner()
v1 = versioner.snapshot("output-id", content)
v2 = versioner.snapshot("output-id", modified_content)
diff = versioner.diff("output-id", v1, v2)
versioner.rollback("output-id", v1)
```

### S05 — Video Studio (Render Presets + A/B)

```python
from src.video_studio.render_presets import RenderPresets

preset = RenderPresets.get("REEL")  # 1080x1920, 30fps
# preset.resolution, preset.fps, preset.aspect_ratio

from src.video_studio.ab_comparison import ABComparator
comparison = ABComparator().compare(package_a, package_b)
# comparison.winner, comparison.recommendation, comparison.dimensions
```

### S06 — Design Art (Brand Presets + Consistency)

```python
from src.design_art.brand_presets import BrandPresets

brand = BrandPresets.get("LUCAS_TIGRE_REAL")
# brand.colors, brand.fonts, brand.archetype, brand.mood_keywords

from src.design_art.consistency_checker import ConsistencyChecker
report = ConsistencyChecker().check_design_brief(brief)
# report.score, report.verdict, report.issues
```

### S07 — App Factory Exec

```python
from src.app_factory_exec import AppSpec, AppType, AppGenerator, AppPackager

spec = AppSpec(app_name="my-api", app_type=AppType.API_BACKEND,
               description="My API", entities=["User", "Product"])
gen = AppGenerator()
files = gen.generate(spec)

packager = AppPackager()
result = packager.write_and_package(spec, files, dry_run=True)
# result["zip_path"], result["manifest_path"]
```

### S08 — Quality Intelligence Gate

```python
from src.quality_gate import QualityScorer

scorer = QualityScorer()
report = scorer.score("output-1", "caption", content_text)
# report.overall_score, report.grade (A-F), report.ready_for_use
# report.dimensions — clarity, hook_strength, seo, cta, tone, risk
```

### S09 — Autonomous Local Backlog

```python
from src.backlog import BacklogManager, ItemType

mgr = BacklogManager()
mgr.enqueue(ItemType.MISSION, "Title", "Description", priority=2, tags=["urgent"])
item = mgr.dequeue()        # Get highest-priority pending item
mgr.complete(item.item_id)  # Mark done
mgr.block(item.item_id, "Waiting for X")
mgr.count()                 # {total, pending, in_progress, blocked, completed, cancelled}
```

CLI:
```bash
python -m src.backlog.cli add --type mission --title "Review content" --priority 1
python -m src.backlog.cli next
python -m src.backlog.cli list
python -m src.backlog.cli done <item_id>
python -m src.backlog.cli count
```

### S10 — Parallel Local Runner

```python
from src.parallel_runner import ParallelRunner, RunnerTask

runner = ParallelRunner(max_workers=4)

# Parallel execution
tasks = [RunnerTask(task_id=f"t{i}", name=f"task_{i}") for i in range(10)]
batch = runner.run(tasks, parallel=True)
# batch.succeeded, batch.failed, batch.total_duration

# File locking
with runner.lock("critical-section"):
    # exclusive access
    pass

# Consolidation
summary = runner.consolidate([batch1, batch2])
# summary["success_rate"], summary["total_duration"]
```

---

## File Locking Protocol

The parallel runner uses file-based locks in `data/runs/locks/`:

```python
from src.parallel_runner.runner import FileLock

lock = FileLock(Path("data/runs/locks/my-resource.lock"), timeout=5.0)
if lock.acquire():
    try:
        # Critical section
        pass
    finally:
        lock.release()
```

Locks are exclusive (O_CREAT | O_EXCL). Poll interval: 50ms. Timeout: configurable.

---

## Backlog Queue Protocol

Items flow through states:
```
PENDING → IN_PROGRESS → COMPLETED
                   ↘ BLOCKED → PENDING (unblock)
                   ↘ CANCELLED
```

Priority 1-5 (1 = highest). Dequeue always returns the highest-priority PENDING item.

Persistence: `data/backlog.json` — auto-saved on every mutation.

---

## Quality Gate Thresholds

- Score >= 9.0 → Grade A
- Score >= 7.5 → Grade B
- Score >= 6.0 → Grade C
- Score >= 4.0 → Grade D
- Score < 4.0  → Grade F

`ready_for_use` requires:
- `overall_score >= 7.0` AND
- `failed_dimensions == 0` (all dimensions >= 5.5)

Dimensions vary by output type (caption, carrossel, reel, dm, app).

---

## Directory Layout

```
data/
  backlog.json          — Backlog queue state
  runs/                 — Parallel run batch results (*.json)
    locks/              — File lock markers (*.lock)

templates/
  template_registry.json — Central template catalog (39 entries)

src/
  template_registry/    — Template lifecycle management
  local_search/         — Inverted-index search engine
  mission_replay/       — Mission recording + replay
  output_versioning/    — Content versioning
  backlog/              — Autonomous work queue
  parallel_runner/      — Concurrent execution + locks
  quality_gate/         — Multi-dimension quality scoring
  app_factory_exec/     — App generation + packaging
  video_studio/         — Render presets, A/B comparison (extended)
  design_art/           — Brand presets, consistency (extended)
```

---

## Constraints

- **Zero network** — all modules operate offline
- **Zero LLM** — heuristic/regex scoring only
- **Zero database** — JSON file persistence
- **dry_run first** — simulate before executing
- **No secrets** — never reads .env, never generates credentials
- **Git worktrees** — isolated parallel development branches
