"""Tests for OMNIS Bus replay buffer (17.5)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from src.omnis_bus.replay import ReplayBuffer


class TestReplayBuffer:
    def test_append_and_replay(self):
        buf = ReplayBuffer(maxlen=10)
        buf.append({"event_type": "test.1", "data": "a"})
        buf.append({"event_type": "test.2", "data": "b"})
        buf.append({"event_type": "test.3", "data": "c"})

        result = buf.replay(n=2)
        assert len(result) == 2
        assert result[0]["event_type"] == "test.2"
        assert result[1]["event_type"] == "test.3"

    def test_replay_empty_buffer(self):
        buf = ReplayBuffer()
        result = buf.replay(n=10)
        assert result == []

    def test_replay_by_type(self):
        buf = ReplayBuffer(maxlen=10)
        buf.append({"event_type": "system.heartbeat", "id": 1})
        buf.append({"event_type": "memory.ingested", "id": 2})
        buf.append({"event_type": "system.heartbeat", "id": 3})

        result = buf.replay_by_type("system.heartbeat", n=10)
        assert len(result) == 2
        assert all(e["event_type"] == "system.heartbeat" for e in result)

    def test_replay_by_source(self):
        buf = ReplayBuffer(maxlen=10)
        buf.append({"event_type": "test", "source": {"service": "kratos-mission-control"}})
        buf.append({"event_type": "test", "source": {"service": "akasha"}})
        buf.append({"event_type": "test", "source": {"service": "kratos-mission-control"}})

        result = buf.replay_by_source("kratos-mission-control", n=10)
        assert len(result) == 2
        for e in result:
            assert e["source"]["service"] == "kratos-mission-control"

    def test_replay_by_source_no_match(self):
        buf = ReplayBuffer()
        buf.append({"event_type": "test", "source": {"service": "akasha"}})
        result = buf.replay_by_source("nonexistent")
        assert result == []

    def test_replay_by_timewindow(self):
        from datetime import datetime, timezone

        buf = ReplayBuffer(maxlen=10)
        now = datetime.now(timezone.utc)
        recent_ts = now.isoformat()
        old_ts = "2026-05-18T00:00:00.000000+00:00"

        buf.append({"event_type": "new", "timestamp": recent_ts, "_received_at": recent_ts})
        buf.append({"event_type": "old", "timestamp": old_ts})

        result = buf.replay_by_timewindow(300)  # 5 minutes
        assert len(result) == 1
        assert result[0]["event_type"] == "new"

    def test_timewindow_fallback_to_timestamp(self):
        """Events without _received_at should use timestamp field."""
        from datetime import datetime, timezone

        buf = ReplayBuffer(maxlen=10)
        recent = datetime.now(timezone.utc).isoformat()
        buf.append({"event_type": "recent", "timestamp": recent})

        result = buf.replay_by_timewindow(300)
        assert len(result) == 1

    def test_capacity_and_size(self):
        buf = ReplayBuffer(maxlen=5)
        assert buf.capacity == 5
        assert buf.size == 0

        for i in range(3):
            buf.append({"id": i})
        assert buf.size == 3

    def test_ring_buffer_cap(self):
        """Old events should be evicted when ring is full."""
        buf = ReplayBuffer(maxlen=3)
        for i in range(5):
            buf.append({"id": i})

        assert buf.size == 3
        ids = [e["id"] for e in buf.replay()]
        assert ids == [2, 3, 4]  # oldest (0,1) evicted

    def test_clear(self):
        buf = ReplayBuffer(maxlen=10)
        for i in range(5):
            buf.append({"id": i})
        buf.clear()
        assert buf.size == 0
        assert buf.replay() == []

    def test_get_status(self):
        buf = ReplayBuffer(maxlen=10)
        buf.append({"id": 1})
        status = buf.get_status()
        assert status["size"] == 1
        assert status["capacity"] == 10
        assert status["is_empty"] is False

    def test_replay_n_larger_than_buffer(self):
        buf = ReplayBuffer(maxlen=10)
        buf.append({"id": 1})
        result = buf.replay(n=100)
        assert len(result) == 1

    def test_replay_by_type_no_match(self):
        buf = ReplayBuffer()
        buf.append({"event_type": "test"})
        result = buf.replay_by_type("nonexistent")
        assert result == []
