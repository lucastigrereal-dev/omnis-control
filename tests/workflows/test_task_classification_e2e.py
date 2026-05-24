"""Tests — TaskClassificationWorkflow (Onda 30).

Cobertura:
  - run() com tasks válidas
  - tasks_count, classifications length
  - ClassifiedTask: intent, risk_level, complexity, capabilities
  - complexity_distribution soma tasks_count
  - unique_capabilities é lista
  - high_risk_count com risk_level "high"
  - unknown intent → fallback complexity medium
  - akasha event emitido
  - error: empty_tasks
  - to_dict keys
"""
from __future__ import annotations

import pytest

from src.akasha_event_sink.adapter import MockAkashaSink
from src.akasha_event_sink.models import SinkStatus
from src.workflows.task_classification_workflow import TaskClassificationWorkflow


# ── helpers ───────────────────────────────────────────────────────────────────

def _task(intent: str = "generate_caption", risk_level: str = "low") -> dict:
    return {"intent": intent, "risk_level": risk_level}


# ── basic run ────────────────────────────────────────────────────────────────

def test_run_succeeds():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task()])
    assert result.success is True


def test_run_tasks_count():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task(), _task("analyze_lead"), _task("plan_mission")])
    assert result.tasks_count == 3


def test_run_classifications_length():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task(), _task("analyze_lead")])
    assert len(result.classifications) == 2


def test_run_run_id_nonempty():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task()])
    assert result.run_id
    assert len(result.run_id) == 12


def test_run_dry_run_flag():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task()], dry_run=True)
    assert result.dry_run is True


# ── ClassifiedTask fields ─────────────────────────────────────────────────────

def test_classified_task_intent():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task("analyze_lead")])
    assert result.classifications[0].intent == "analyze_lead"


def test_classified_task_risk_level():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task("plan_mission", "high")])
    assert result.classifications[0].risk_level == "high"


def test_classified_task_complexity_nonempty():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task("generate_caption")])
    assert result.classifications[0].complexity != ""


def test_classified_task_capabilities_nonempty():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task("generate_caption")])
    assert len(result.classifications[0].capabilities) > 0


# ── known intent checks ───────────────────────────────────────────────────────

def test_classify_intent_known_complexity():
    from src.multi_model_orchestration.models import COMPLEXITY_MEDIUM
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task("generate_caption")])
    assert result.classifications[0].complexity == COMPLEXITY_MEDIUM


def test_classify_plan_mission_high_complexity():
    from src.multi_model_orchestration.models import COMPLEXITY_HIGH
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task("plan_mission")])
    assert result.classifications[0].complexity == COMPLEXITY_HIGH


def test_classify_unknown_intent_fallback():
    from src.multi_model_orchestration.models import COMPLEXITY_MEDIUM
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task("totally_unknown_intent_xyz")])
    assert result.classifications[0].complexity == COMPLEXITY_MEDIUM


# ── aggregate properties ──────────────────────────────────────────────────────

def test_complexity_distribution_sums_to_count():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    tasks = [_task("generate_caption"), _task("plan_mission"), _task("analyze_lead")]
    result = wf.run(tasks=tasks)
    assert sum(result.complexity_distribution.values()) == 3


def test_unique_capabilities_is_list():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task("generate_caption"), _task("analyze_lead")])
    assert isinstance(result.unique_capabilities, list)


def test_high_risk_count_with_high_tasks():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    tasks = [_task("generate_caption", "low"), _task("plan_mission", "high"), _task("analyze_lead", "high")]
    result = wf.run(tasks=tasks)
    assert result.high_risk_count == 2


def test_high_risk_count_zero_when_all_low():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    tasks = [_task("generate_caption", "low"), _task("analyze_lead", "low")]
    result = wf.run(tasks=tasks)
    assert result.high_risk_count == 0


# ── akasha event ──────────────────────────────────────────────────────────────

def test_run_emits_akasha_event():
    sink = MockAkashaSink()
    wf = TaskClassificationWorkflow(akasha_sink=sink)
    wf.run(tasks=[_task()])
    events = sink.query_events("task_classification_completed")
    assert len(events) == 1


def test_run_event_source_is_run_id():
    sink = MockAkashaSink()
    wf = TaskClassificationWorkflow(akasha_sink=sink)
    result = wf.run(tasks=[_task()])
    events = sink.query_events("task_classification_completed")
    assert events[0].source == result.run_id


def test_run_akasha_event_id_nonempty():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task()])
    assert result.akasha_event_id.startswith("ske_")


def test_run_event_status_written():
    sink = MockAkashaSink()
    wf = TaskClassificationWorkflow(akasha_sink=sink)
    wf.run(tasks=[_task()])
    events = sink.query_events("task_classification_completed")
    assert events[0].status == SinkStatus.WRITTEN


# ── error: empty_tasks ────────────────────────────────────────────────────────

def test_empty_tasks_success_false():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[])
    assert result.success is False


def test_empty_tasks_error_field():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[])
    assert result.error == "empty_tasks"


def test_empty_tasks_still_emits_event():
    sink = MockAkashaSink()
    wf = TaskClassificationWorkflow(akasha_sink=sink)
    wf.run(tasks=[])
    events = sink.query_events("task_classification_completed")
    assert len(events) == 1


# ── to_dict ───────────────────────────────────────────────────────────────────

def test_to_dict_has_required_keys():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task()])
    d = result.to_dict()
    for key in ["run_id", "success", "tasks_count", "complexity_distribution",
                "unique_capabilities", "high_risk_count",
                "akasha_event_id", "dry_run", "cost_local_pct"]:
        assert key in d


def test_cost_local_pct_100():
    wf = TaskClassificationWorkflow(akasha_sink=MockAkashaSink())
    result = wf.run(tasks=[_task()])
    assert result.cost_local_pct == 100
