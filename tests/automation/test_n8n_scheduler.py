"""Tests for W145 — n8n Execution Scheduler."""
import pytest
from src.automation.n8n_scheduler import N8nScheduler, ScheduledExecution, SCHEDULE_STATUS_FIRED, SCHEDULE_STATUS_SKIPPED
from src.automation.models import AutomationWorkflow, AutomationTrigger


@pytest.fixture
def scheduler():
    return N8nScheduler()


@pytest.fixture
def wf():
    t = AutomationTrigger.new("schedule", config={"cron": "0 8 * * *"})
    return AutomationWorkflow.new("Daily", "daily run", t)


def test_schedule_returns_entry(scheduler, wf):
    s = scheduler.schedule(wf, "0 8 * * *")
    assert isinstance(s, ScheduledExecution)
    assert s.workflow_id == wf.workflow_id


def test_schedule_default_dry_run(scheduler, wf):
    s = scheduler.schedule(wf, "0 8 * * *")
    assert s.dry_run is True


def test_schedule_count(scheduler, wf):
    scheduler.schedule(wf, "0 8 * * *")
    assert scheduler.count() == 1


def test_fire_returns_trigger_result(scheduler, wf):
    s = scheduler.schedule(wf, "0 8 * * *")
    result = scheduler.fire(s.schedule_id, wf)
    assert result.status == "simulated"


def test_fire_increments_count(scheduler, wf):
    s = scheduler.schedule(wf, "0 8 * * *")
    scheduler.fire(s.schedule_id, wf)
    scheduler.fire(s.schedule_id, wf)
    assert s.fire_count == 2


def test_fire_updates_status(scheduler, wf):
    s = scheduler.schedule(wf, "0 8 * * *")
    scheduler.fire(s.schedule_id, wf)
    assert s.status == SCHEDULE_STATUS_FIRED


def test_fire_unknown_raises(scheduler, wf):
    with pytest.raises(KeyError):
        scheduler.fire("bad_id", wf)


def test_skip_updates_status(scheduler, wf):
    s = scheduler.schedule(wf, "0 8 * * *")
    scheduler.skip(s.schedule_id)
    assert s.status == SCHEDULE_STATUS_SKIPPED


def test_skip_unknown_raises(scheduler, wf):
    with pytest.raises(KeyError):
        scheduler.skip("bad_id")


def test_get_schedule(scheduler, wf):
    s = scheduler.schedule(wf, "0 8 * * *")
    found = scheduler.get(s.schedule_id)
    assert found is s


def test_list_all(scheduler, wf):
    scheduler.schedule(wf, "0 8 * * *")
    scheduler.schedule(wf, "0 20 * * *")
    assert len(scheduler.list_all()) == 2


def test_to_dict_after_fire(scheduler, wf):
    s = scheduler.schedule(wf, "0 8 * * *")
    scheduler.fire(s.schedule_id, wf)
    d = s.to_dict()
    assert d["fire_count"] == 1
    assert d["last_result"] is not None
