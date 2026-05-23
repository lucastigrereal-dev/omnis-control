from src.skill_execution.events import (
    SkillExecutionEvent,
    SkillEventBus,
    SkillEventType,
)


class TestSkillExecutionEvent:
    def test_default_event(self):
        e = SkillExecutionEvent()
        assert e.event_id.startswith("see_")
        assert e.event_type == SkillEventType.REQUEST_RECEIVED

    def test_blocked_event(self):
        e = SkillExecutionEvent(
            event_type=SkillEventType.EXECUTION_BLOCKED,
            skill_id="deploy",
            detail={"reason": "critical risk"},
        )
        assert e.skill_id == "deploy"
        assert e.detail["reason"] == "critical risk"

    def test_roundtrip(self):
        e = SkillExecutionEvent(
            event_type=SkillEventType.APPROVAL_REQUIRED,
            request_id="ser_x",
            skill_id="shell",
        )
        data = e.to_dict()
        e2 = SkillExecutionEvent.from_dict(data)
        assert e2.event_type == SkillEventType.APPROVAL_REQUIRED
        assert e2.request_id == "ser_x"


class TestSkillEventBus:
    def test_emit_and_query(self):
        bus = SkillEventBus()
        bus.emit(SkillExecutionEvent(event_type=SkillEventType.REQUEST_RECEIVED, skill_id="a"))
        bus.emit(SkillExecutionEvent(event_type=SkillEventType.EXECUTION_COMPLETED, skill_id="a"))
        assert bus.event_count == 2
        assert len(bus.query(skill_id="a")) == 2

    def test_query_by_type(self):
        bus = SkillEventBus()
        bus.emit(SkillExecutionEvent(event_type=SkillEventType.REQUEST_RECEIVED))
        bus.emit(SkillExecutionEvent(event_type=SkillEventType.EXECUTION_BLOCKED))
        assert len(bus.query(event_type="EXECUTION_BLOCKED")) == 1

    def test_subscriber_called(self):
        bus = SkillEventBus()
        calls = []
        bus.subscribe(SkillEventType.EXECUTION_COMPLETED, lambda e: calls.append(e))
        event = SkillExecutionEvent(event_type=SkillEventType.EXECUTION_COMPLETED)
        bus.emit(event)
        assert len(calls) == 1
        assert calls[0] is event
