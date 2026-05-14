# P28 — SELF-IMPROVEMENT LOOP SKELETON

> **Data:** 2026-05-14
> **Status:** SKELETON COMPLETE

---

## FILES

```
src/self_improvement/
├── __init__.py          # Public exports (33 symbols)
├── models.py            # ExecutionFeedback, ImprovementProposal, ImpactMeasurement, Pattern, PrioritizedGap
├── errors.py            # ImprovementError + 6 subclasses
├── collector.py         # FeedbackCollector — collects from missions/builds/actions/system
├── analyzer.py          # PatternAnalyzer — failure, performance, gap pattern detection
├── prioritizer.py       # GapPrioritizer — composite scoring by impact × frequency × urgency
├── proposer.py          # ImprovementProposer — generates concrete proposals from gaps
├── executor.py          # ImprovementExecutor — implements approved proposals (4 types)
├── measurer.py          # ImpactMeasurer — before/after with metric-specific verdicts
└── cli.py               # CLI: analyze, gaps, propose, list, approve, reject, execute, measure, status, history

tests/self_improvement/
├── test_models.py       # 26 testes
├── test_collector.py    # 12 testes
├── test_analyzer.py     # 12 testes
├── test_prioritizer.py  # 10 testes
├── test_proposer.py     # 14 testes
├── test_executor.py     # 12 testes
├── test_measurer.py     # 11 testes
└── test_e2e_improvement.py # 19 testes

docs/self_improvement/
└── P28_SELF_IMPROVEMENT_LOOP_SKELETON.md
```

---

## CONTRACTS

### ExecutionFeedback
- `feedback_id` prefix: `sif_`
- Source types: mission | build | action | system
- Factory alternates: `.new()`, `.from_mission_report()`, `.from_build_result()`, `.from_action_result()`

### ImprovementProposal
- `proposal_id` prefix: `sip_`
- Categories: capability_gap | performance | reliability | cost | security
- Status flow: draft → proposed → approved | rejected → implemented → measured
- Implementation types: code_change | config_change | new_capability | process_change

### ImpactMeasurement
- `measurement_id` prefix: `sim_`
- Verdicts: improved | degraded | neutral | insufficient_data

### FeedbackCollector
- Dry-run generates mock feedback for testing
- collect_all() aggregates from all 4 sources

### PatternAnalyzer
- detect_failure_patterns: min 2 occurrences
- detect_performance_patterns: > 1.5× avg latency
- detect_gap_patterns: warnings with "missing"/"gap"/"not found"

### CLI
- `omnis-improve analyze` — collect + analyze
- `omnis-improve gaps [--top N]` — prioritized gaps
- `omnis-improve propose` — generate proposals
- `omnis-improve list [--status]` — list proposals
- `omnis-improve approve <id>` / `omnis-improve reject <id>`
- `omnis-improve execute <id>` / `omnis-improve measure <id>`

---

## DEPENDENCIES
- Reads from P20 (mission reports), P26 (builds), P27 (actions)
- Proposals leverage P22 Forge for capability generation
- Zero toques em módulos existentes
