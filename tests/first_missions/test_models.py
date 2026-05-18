"""W181 — Tests for Mission model & MissionRegistry."""
import pytest
from src.first_missions.models import (
    Mission,
    MissionPriority,
    MissionRegistry,
    MissionStatus,
    MissionType,
)


# ---------------------------------------------------------------------------
# Mission defaults
# ---------------------------------------------------------------------------

def test_mission_defaults():
    m = Mission()
    assert m.mission_id.startswith("mss_")
    assert m.status == MissionStatus.PENDING
    assert m.priority == MissionPriority.NORMAL
    assert m.dry_run is True
    assert m.mission_type == MissionType.CUSTOM
    assert m.created_at != ""


def test_mission_is_not_terminal_when_pending():
    m = Mission()
    assert not m.is_terminal


def test_mission_is_terminal_completed():
    m = Mission(status=MissionStatus.COMPLETED)
    assert m.is_terminal


def test_mission_is_terminal_failed():
    m = Mission(status=MissionStatus.FAILED)
    assert m.is_terminal


def test_mission_is_terminal_cancelled():
    m = Mission(status=MissionStatus.CANCELLED)
    assert m.is_terminal


def test_mission_running_not_terminal():
    m = Mission(status=MissionStatus.RUNNING)
    assert not m.is_terminal


# ---------------------------------------------------------------------------
# to_dict / from_dict round-trip
# ---------------------------------------------------------------------------

def test_to_dict_keys():
    m = Mission(name="test")
    d = m.to_dict()
    for key in ("mission_id", "name", "mission_type", "priority", "status",
                "payload", "result", "dry_run", "created_at", "tags", "metadata"):
        assert key in d


def test_from_dict_round_trip():
    m = Mission(name="roundtrip", tags=["a", "b"], payload={"x": 1})
    d = m.to_dict()
    m2 = Mission.from_dict(d)
    assert m2.mission_id == m.mission_id
    assert m2.name == m.name
    assert m2.tags == m.tags
    assert m2.payload == m.payload


def test_from_dict_defaults():
    m = Mission.from_dict({})
    assert m.mission_id.startswith("mss_")
    assert m.status == MissionStatus.PENDING


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

def test_content_generation_factory():
    m = Mission.content_generation("lucastigrereal", "travel")
    assert m.mission_type == MissionType.CONTENT_GENERATION
    assert "lucastigrereal" in m.name
    assert m.payload["profile"] == "lucastigrereal"
    assert m.payload["topic"] == "travel"


def test_metric_report_factory():
    m = Mission.metric_report("followers", "weekly")
    assert m.mission_type == MissionType.METRIC_REPORT
    assert m.payload["metric"] == "followers"
    assert m.payload["period"] == "weekly"


def test_metric_report_default_period():
    m = Mission.metric_report("reach")
    assert m.payload["period"] == "daily"


def test_health_snapshot_factory():
    m = Mission.health_snapshot()
    assert m.mission_type == MissionType.HEALTH_SNAPSHOT
    assert m.priority == MissionPriority.HIGH


# ---------------------------------------------------------------------------
# MissionRegistry
# ---------------------------------------------------------------------------

def test_registry_register_and_get():
    reg = MissionRegistry()
    m = Mission(name="reg_test")
    reg.register(m)
    assert reg.get(m.mission_id) is m


def test_registry_get_missing():
    reg = MissionRegistry()
    assert reg.get("unknown") is None


def test_registry_query_by_status():
    reg = MissionRegistry()
    m1 = Mission(status=MissionStatus.PENDING)
    m2 = Mission(status=MissionStatus.COMPLETED)
    reg.register(m1)
    reg.register(m2)
    pending = reg.query(status=MissionStatus.PENDING)
    assert len(pending) == 1
    assert pending[0].mission_id == m1.mission_id


def test_registry_query_by_type():
    reg = MissionRegistry()
    reg.register(Mission(mission_type=MissionType.CONTENT_GENERATION))
    reg.register(Mission(mission_type=MissionType.METRIC_REPORT))
    results = reg.query(mission_type=MissionType.METRIC_REPORT)
    assert len(results) == 1


def test_registry_query_by_priority():
    reg = MissionRegistry()
    reg.register(Mission(priority=MissionPriority.HIGH))
    reg.register(Mission(priority=MissionPriority.LOW))
    high = reg.query(priority=MissionPriority.HIGH)
    assert len(high) == 1


def test_registry_pending_helper():
    reg = MissionRegistry()
    reg.register(Mission(status=MissionStatus.PENDING))
    reg.register(Mission(status=MissionStatus.RUNNING))
    assert len(reg.pending()) == 1


def test_registry_completed_helper():
    reg = MissionRegistry()
    reg.register(Mission(status=MissionStatus.COMPLETED))
    reg.register(Mission(status=MissionStatus.FAILED))
    assert len(reg.completed()) == 1


def test_registry_stats():
    reg = MissionRegistry()
    reg.register(Mission(status=MissionStatus.PENDING, mission_type=MissionType.CUSTOM))
    reg.register(Mission(status=MissionStatus.COMPLETED, mission_type=MissionType.CUSTOM))
    s = reg.stats()
    assert s["total"] == 2
    assert s["by_status"]["PENDING"] == 1
    assert s["by_status"]["COMPLETED"] == 1
    assert s["by_type"]["CUSTOM"] == 2


def test_registry_limit():
    reg = MissionRegistry()
    for _ in range(10):
        reg.register(Mission())
    assert len(reg.query(limit=3)) == 3
