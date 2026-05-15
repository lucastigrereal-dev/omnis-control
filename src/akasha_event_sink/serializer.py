import json
from datetime import datetime, timezone

from src.akasha_event_sink.models import SinkEvent
from src.akasha_event_sink.errors import SerializationError


class EventSerializer:
    @staticmethod
    def serialize(event: SinkEvent) -> str:
        return json.dumps(event.to_dict(), ensure_ascii=False)

    @staticmethod
    def deserialize(data: str) -> SinkEvent:
        return SinkEvent.from_dict(json.loads(data))

    @staticmethod
    def serialize_batch(events: list[SinkEvent]) -> str:
        data = [e.to_dict() for e in events]
        wrapper = {
            "batch_size": len(events),
            "events": data,
            "serialized_at": datetime.now(timezone.utc).isoformat(),
        }
        return json.dumps(wrapper, ensure_ascii=False)
