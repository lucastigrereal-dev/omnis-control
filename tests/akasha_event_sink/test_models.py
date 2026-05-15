from src.akasha_event_sink.models import SinkEvent, SinkStatus, SinkConfig


class TestSinkStatus:
    def test_values(self):
        assert SinkStatus.QUEUED == "QUEUED"
        assert SinkStatus.WRITTEN == "WRITTEN"
        assert SinkStatus.FAILED == "FAILED"


class TestSinkEvent:
    def test_defaults(self):
        ev = SinkEvent()
        assert ev.event_id.startswith("ske_")
        assert ev.status == SinkStatus.QUEUED
        assert ev.payload == {}

    def test_to_dict_round_trip(self):
        ev = SinkEvent(
            event_type="decision",
            source="omnis",
            payload={"action": "approved"},
        )
        data = ev.to_dict()
        assert data["event_type"] == "decision"
        assert data["payload"] == {"action": "approved"}

    def test_from_dict(self):
        ev = SinkEvent.from_dict({
            "event_id": "ske_x",
            "event_type": "log",
            "source": "pipeline",
        })
        assert ev.event_id == "ske_x"
        assert ev.event_type == "log"


class TestSinkConfig:
    def test_defaults(self):
        cfg = SinkConfig()
        assert cfg.dry_run is True
        assert cfg.batch_size == 100
        assert cfg.max_file_size == 1048576
