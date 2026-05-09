"""Tests for Task Decomposer models."""
from src.task_decomposer.models import SquadTask, TASK_STATUS_PLANNED


def test_squad_task_id_prefix():
    from src.task_decomposer.models import _make_task_id
    tid = _make_task_id()
    assert tid.startswith("task_")


def test_squad_task_to_dict():
    t = SquadTask("task_abc", "copywriter", "Write copy", "Write captions", "caption", [], TASK_STATUS_PLANNED)
    d = t.to_dict()
    assert d["task_id"] == "task_abc"
    assert d["role_id"] == "copywriter"
    assert d["status"] == TASK_STATUS_PLANNED
    assert d["depends_on"] == []
