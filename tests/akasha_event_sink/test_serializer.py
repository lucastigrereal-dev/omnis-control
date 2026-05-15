import json
from src.akasha_event_sink.serializer import EventSerializer
from src.akasha_event_sink.models import SinkEvent


class TestEventSerializer:
    def test_serialize_single(self):
        ev = SinkEvent(event_id="e1", event_type="log", source="omnis")
        result = EventSerializer.serialize(ev)
        data = json.loads(result)
        assert data["event_id"] == "e1"
        assert data["event_type"] == "log"

    def test_deserialize(self):
        raw = '{"event_id": "e2", "event_type": "decision", "source": "pipeline", "payload": {}, "status": "QUEUED"}'
        ev = EventSerializer.deserialize(raw)
        assert ev.event_id == "e2"
        assert ev.event_type == "decision"

    def test_serialize_batch(self):
        events = [
            SinkEvent(event_id="e1", event_type="a"),
            SinkEvent(event_id="e2", event_type="b"),
            SinkEvent(event_id="e3", event_type="c"),
        ]
        result = EventSerializer.serialize_batch(events)
        data = json.loads(result)
        assert data["batch_size"] == 3
        assert len(data["events"]) == 3
        assert "serialized_at" in data

    def test_round_trip(self):
        original = SinkEvent(
            event_id="rt1",
            event_type="test",
            source="unit",
            payload={"key": "val"},
        )
        serialized = EventSerializer.serialize(original)
        restored = EventSerializer.deserialize(serialized)
        assert restored.event_id == original.event_id
        assert restored.event_type == original.event_type
        assert restored.payload == original.payload
