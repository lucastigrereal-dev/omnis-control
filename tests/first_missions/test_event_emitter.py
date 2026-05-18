"""W191 — Tests for MissionEventEmitter."""
import pytest
from src.first_missions.event_emitter import MissionEvent, MissionEventEmitter
from src.first_missions.models import Mission, MissionStatus, MissionType


# ---------------------------------------------------------------------------
# MissionEvent
# ---------------------------------------------------------------------------

def test_mission_event_to_dict():
    e = MissionEvent(
        event_id="mev_abc", event_type="completed",
        mission_id="mss_x", mission_name="test",
        mission_type="CUSTOM", status="COMPLETED",
        timestamp="2026-01-01T00:00:00Z",
    )
    d = e.to_dict()
    assert d["event_id"] == "mev_abc"
    assert d["event_type"] == "completed"
    assert d["mission_id"] == "mss_x"


# ---------------------------------------------------------------------------
# Emitter — standalone (no bus)
# ---------------------------------------------------------------------------

def test_emitter_mission_started():
    em = MissionEventEmitter(dry_run=True)
    m = Mission(name="m1")
    em.mission_started(m)
    assert len(em.history()) == 1
    assert em.history()[0].event_type == "started"


def test_emitter_mission_completed():
    em = MissionEventEmitter(dry_run=True)
    m = Mission(name="m1", result={"x": 1})
    m.status = MissionStatus.COMPLETED
    em.mission_completed(m)
    e = em.history()[0]
    assert e.event_type == "completed"
    assert e.data.get("result") == {"x": 1}


def test_emitter_mission_failed():
    em = MissionEventEmitter(dry_run=True)
    m = Mission(name="fail", error="boom")
    m.status = MissionStatus.FAILED
    em.mission_failed(m)
    e = em.history()[0]
    assert e.event_type == "failed"
    assert e.data.get("error") == "boom"


def test_emitter_dry_run():
    em = MissionEventEmitter(dry_run=True)
    m = Mission(name="dry")
    m.status = MissionStatus.DRY_RUN
    em.mission_dry_run(m)
    assert em.history()[0].event_type == "dry_run"


def test_emit_for_dispatches_correctly():
    em = MissionEventEmitter(dry_run=True)

    m1 = Mission(name="c"); m1.status = MissionStatus.COMPLETED
    m2 = Mission(name="f"); m2.status = MissionStatus.FAILED
    m3 = Mission(name="d"); m3.status = MissionStatus.DRY_RUN

    em.emit_for(m1)
    em.emit_for(m2)
    em.emit_for(m3)

    assert len(em.history()) == 3
    types = [e.event_type for e in em.history()]
    assert "completed" in types
    assert "failed" in types
    assert "dry_run" in types


def test_emitter_stats():
    em = MissionEventEmitter(dry_run=True)
    m = Mission(name="x")
    em.mission_started(m)
    m.status = MissionStatus.COMPLETED
    em.mission_completed(m)
    s = em.stats()
    assert s["total"] == 2
    assert s["by_type"]["started"] == 1
    assert s["by_type"]["completed"] == 1


# ---------------------------------------------------------------------------
# Integration with orchestrator
# ---------------------------------------------------------------------------

def test_orchestrator_emits_events():
    from src.first_missions.orchestrator import MissionOrchestrator
    orch = MissionOrchestrator(dry_run=True)
    m = Mission.content_generation("test", "topic")
    orch.run_one(m)
    events = orch.emitter.history()
    assert len(events) >= 2  # started + dry_run/completed
    event_types = [e.event_type for e in events]
    assert "started" in event_types


def test_orchestrator_emits_on_run_pending():
    from src.first_missions.orchestrator import MissionOrchestrator
    orch = MissionOrchestrator(dry_run=True)
    orch.submit(Mission(name="m1"))
    orch.submit(Mission(name="m2"))
    orch.run_pending()
    events = orch.emitter.history()
    assert len(events) >= 2  # one event per mission


# ---------------------------------------------------------------------------
# With fake bus
# ---------------------------------------------------------------------------

class FakeBus:
    def __init__(self):
        self.events = []

    def emit_new(self, event_type: str, source_module: str, data=None):
        self.events.append({"event_type": event_type, "source": source_module, "data": data})
        from src.omnis_os.models import OmnisEvent
        return OmnisEvent.new(event_type, source_module, data=data)


def test_emitter_bridges_to_bus():
    fake = FakeBus()
    em = MissionEventEmitter(dry_run=False, bus=fake)
    m = Mission(name="bridge_test")
    m.status = MissionStatus.COMPLETED
    em.mission_completed(m)
    assert len(fake.events) == 1
    assert fake.events[0]["event_type"] == "mission.completed"
    assert fake.events[0]["source"] == "first_missions"


def test_emitter_no_bus():
    """Should work fine without a bus."""
    em = MissionEventEmitter(dry_run=False)
    m = Mission(name="solo")
    em.mission_started(m)
    assert len(em.history()) == 1
