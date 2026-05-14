import json
import pytest
from src.decision_log.models import LogEventType, BaseEvent
from src.decision_log.writer import LogWriter
from src.decision_log.events import EventFactory


class TestLogWriter:
    @pytest.fixture
    def writer(self):
        return LogWriter()

    @pytest.fixture
    def tmp_writer(self, tmp_path):
        return LogWriter(base_dir=str(tmp_path))

    def test_write_appends_to_memory(self, writer):
        event = BaseEvent()
        writer.write(event)
        assert writer.count() == 1

    def test_write_returns_log_event(self, writer):
        event = BaseEvent()
        result = writer.write(event)
        assert result.event_id == event.event.event_id

    def test_write_persists_to_disk(self, tmp_writer, tmp_path):
        event = BaseEvent()
        tmp_writer.write(event)
        files = list(tmp_path.glob("*.json"))
        assert len(files) == 1

    def test_multiple_writes(self, writer):
        for _ in range(5):
            writer.write(BaseEvent())
        assert writer.count() == 5

    def test_by_type_filters_correctly(self, writer):
        evt1 = EventFactory.decision_created(decision_id="d1")
        evt2 = EventFactory.risk_blocked(risk_level="HIGH", reason="test")
        evt3 = EventFactory.decision_created(decision_id="d2")
        writer.write(evt1)
        writer.write(evt2)
        writer.write(evt3)
        decisions = writer.by_type("DecisionCreated")
        assert len(decisions) == 2

    def test_by_project_filters_correctly(self, writer):
        evt1 = EventFactory.decision_created(project="omnis-a")
        evt2 = EventFactory.decision_created(project="omnis-b")
        evt3 = EventFactory.decision_created(project="omnis-a")
        writer.write(evt1)
        writer.write(evt2)
        writer.write(evt3)
        assert len(writer.by_project("omnis-a")) == 2
        assert len(writer.by_project("omnis-b")) == 1
        assert len(writer.by_project("missing")) == 0

    def test_last_returns_most_recent(self, writer):
        evt1 = EventFactory.decision_created(decision_id="first")
        evt2 = EventFactory.decision_created(decision_id="last")
        writer.write(evt1)
        writer.write(evt2)
        assert writer.last().event_id == evt2.event.event_id

    def test_last_returns_none_when_empty(self, writer):
        assert writer.last() is None

    def test_clear_empties_memory(self, writer):
        writer.write(BaseEvent())
        writer.write(BaseEvent())
        writer.clear()
        assert writer.count() == 0

    def test_write_typed_is_alias_for_write(self, writer):
        event = BaseEvent()
        result = writer.write_typed(event)
        assert writer.count() == 1
        assert result.event_id == event.event.event_id

    def test_memory_returns_copy(self, writer):
        writer.write(BaseEvent())
        mem = writer.memory
        writer.write(BaseEvent())
        assert len(mem) == 1
