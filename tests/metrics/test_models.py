"""Testes dos modelos Metrics Spine — P0.9."""
from __future__ import annotations

import pytest

from src.metrics.models import MetricEvent, RunSummary


class TestMetricEventValid:
    """MetricEvent valido — campos obrigatorios e opcionais."""

    def test_valid_minimal_event(self):
        m = MetricEvent(name="test_metric")
        assert m.metric_id != ""
        assert len(m.metric_id) == 12
        assert m.timestamp != ""
        assert "T" in m.timestamp
        assert m.name == "test_metric"
        assert m.value == 0.0

    def test_all_optional_fields(self):
        m = MetricEvent(
            name="full_metric",
            value=42.0,
            mission_id="abc123",
            run_id="run001",
            tool_id="docker",
            event_type="tool_use",
            unit="ms",
            status="success",
            duration_ms=1500.0,
            tokens_in=100,
            tokens_out=200,
            cost_usd=0.05,
            tags={"env": "dev"},
            metadata={"detail": "extra"},
        )
        assert m.mission_id == "abc123"
        assert m.run_id == "run001"
        assert m.tool_id == "docker"
        assert m.tokens_in == 100
        assert m.tokens_out == 200
        assert m.cost_usd == 0.05
        assert m.tags == {"env": "dev"}
        assert m.metadata == {"detail": "extra"}

    def test_auto_metric_id_unique(self):
        a = MetricEvent(name="a")
        b = MetricEvent(name="b")
        assert a.metric_id != b.metric_id

    def test_explicit_metric_id_respected(self):
        m = MetricEvent(name="x", metric_id="my-custom-id")
        assert m.metric_id == "my-custom-id"

    def test_explicit_timestamp_respected(self):
        m = MetricEvent(name="x", timestamp="2026-01-01T00:00:00Z")
        assert m.timestamp == "2026-01-01T00:00:00Z"


class TestRunSummaryValid:
    """RunSummary valido."""

    def test_valid_minimal_summary(self):
        r = RunSummary(run_id="run123")
        assert r.run_id == "run123"
        assert r.started_at != ""
        assert r.status == "running"
        assert r.tools_used == []
        assert r.duration_ms == 0.0

    def test_all_fields(self):
        r = RunSummary(
            run_id="run456",
            mission_id="m789",
            status="success",
            duration_ms=5000.0,
            warnings_count=2,
            retries_count=1,
            checkpoints_count=3,
            tools_used=["docker", "publisher"],
            artifacts_count=5,
            events_count=12,
            total_tokens=500,
            total_cost_usd=0.10,
        )
        assert r.warnings_count == 2
        assert r.checkpoints_count == 3
        assert r.tools_used == ["docker", "publisher"]
        assert r.total_tokens == 500
        assert r.total_cost_usd == 0.10

    def test_auto_started_at(self):
        r = RunSummary(run_id="r1")
        assert "T" in r.started_at

    def test_explicit_started_at_respected(self):
        r = RunSummary(run_id="r1", started_at="2026-05-01T10:00:00Z")
        assert r.started_at == "2026-05-01T10:00:00Z"


class TestExtraFieldsBlocked:
    """ConfigDict(extra='forbid') rejeita campos desconhecidos."""

    def test_extra_field_metric_event(self):
        with pytest.raises(Exception):
            MetricEvent(name="x", unknown_field=42)

    def test_extra_field_run_summary(self):
        with pytest.raises(Exception):
            RunSummary(run_id="r1", unknown_field=42)
