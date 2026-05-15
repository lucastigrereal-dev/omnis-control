import json
from pathlib import Path

from src.akasha_event_sink.file_sink import FileSinkWriter
from src.akasha_event_sink.adapter import FileAkashaSink, MockAkashaSink
from src.akasha_event_sink.models import SinkEvent, SinkStatus


class TestFileSinkWriter:
    def test_dry_run_flush_does_not_write_files(self, tmp_path):
        writer = FileSinkWriter(str(tmp_path), dry_run=True)
        writer.buffer(SinkEvent(event_type="test", source="test"))
        flushed = writer.flush()
        assert len(flushed) == 1
        assert flushed[0].status == SinkStatus.FLUSHED
        assert len(list(tmp_path.glob("*.json"))) == 0

    def test_real_flush_writes_files(self, tmp_path):
        writer = FileSinkWriter(str(tmp_path), dry_run=False)
        ev = SinkEvent(event_type="decision", source="omnis", payload={"a": 1})
        writer.buffer(ev)
        flushed = writer.flush()
        assert len(flushed) == 1
        assert flushed[0].status == SinkStatus.WRITTEN
        files = list(tmp_path.glob("*.json"))
        assert len(files) == 1
        content = json.loads(files[0].read_text(encoding="utf-8"))
        assert content["event_type"] == "decision"

    def test_pending_count(self):
        writer = FileSinkWriter("/tmp")
        assert writer.pending_count == 0
        writer.buffer(SinkEvent())
        assert writer.pending_count == 1
        writer.buffer(SinkEvent())
        assert writer.pending_count == 2


class TestFileAkashaSink:
    def test_dry_run_does_not_create_file(self, tmp_path):
        sink = FileAkashaSink(str(tmp_path), dry_run=True)
        ev = SinkEvent(event_type="test")
        assert sink.write_event(ev) is True
        assert ev.status == SinkStatus.QUEUED
        assert not list(tmp_path.glob("*.json"))

    def test_write_and_query(self, tmp_path):
        sink = FileAkashaSink(str(tmp_path), dry_run=False)
        ev = SinkEvent(event_type="alpha", source="src1")
        sink.write_event(ev)
        assert ev.status == SinkStatus.WRITTEN

        results = sink.query_events("alpha")
        assert len(results) == 1
        assert results[0].source == "src1"

    def test_query_filter(self, tmp_path):
        sink = FileAkashaSink(str(tmp_path), dry_run=False)
        sink.write_event(SinkEvent(event_type="a"))
        sink.write_event(SinkEvent(event_type="b"))
        sink.write_event(SinkEvent(event_type="a"))

        a_events = sink.query_events("a")
        assert len(a_events) == 2

    def test_health_check(self, tmp_path):
        sink = FileAkashaSink(str(tmp_path), dry_run=True)
        assert sink.health_check() is True


class TestMockAkashaSink:
    def test_write_and_query(self):
        sink = MockAkashaSink()
        sink.write_event(SinkEvent(event_type="x", event_id="e1"))
        sink.write_event(SinkEvent(event_type="y", event_id="e2"))
        assert len(sink.query_events()) == 2
        assert len(sink.query_events("x")) == 1
        assert sink.health_check() is True
