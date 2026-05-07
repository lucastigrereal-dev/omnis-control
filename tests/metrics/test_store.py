"""Testes do MetricsStore — P0.9."""
from __future__ import annotations

import pytest

from src.metrics.models import MetricEvent, RunSummary
from src.metrics.store import MetricsStore


@pytest.fixture
def tmp_store(tmp_path):
    return MetricsStore(base_dir=str(tmp_path / "metrics_spine"))


@pytest.fixture
def sample_metric():
    return MetricEvent(name="test_metric", value=1.0, event_type="test_event")


@pytest.fixture
def sample_run():
    return RunSummary(run_id="run001", mission_id="m001")


class TestWriteAndReadMetrics:
    """write_metric + get_metrics com filtros."""

    def test_write_and_read_one(self, tmp_store, sample_metric):
        tmp_store.write_metric(sample_metric)
        results = tmp_store.get_metrics()
        assert len(results) == 1
        assert results[0].name == "test_metric"

    def test_filter_by_mission_id(self, tmp_store):
        tmp_store.write_metric(MetricEvent(name="a", mission_id="m1"))
        tmp_store.write_metric(MetricEvent(name="b", mission_id="m2"))
        results = tmp_store.get_metrics(mission_id="m1")
        assert len(results) == 1
        assert results[0].name == "a"

    def test_filter_by_run_id(self, tmp_store):
        tmp_store.write_metric(MetricEvent(name="a", run_id="r1"))
        tmp_store.write_metric(MetricEvent(name="b", run_id="r2"))
        results = tmp_store.get_metrics(run_id="r2")
        assert len(results) == 1
        assert results[0].name == "b"

    def test_empty_store(self, tmp_store):
        assert tmp_store.get_metrics() == []


class TestWriteAndReadRuns:
    """write_run + get_run + get_runs."""

    def test_write_and_get_run(self, tmp_store, sample_run):
        tmp_store.write_run(sample_run)
        found = tmp_store.get_run("run001")
        assert found is not None
        assert found.mission_id == "m001"

    def test_get_nonexistent_run(self, tmp_store):
        assert tmp_store.get_run("nonexistent") is None

    def test_filter_runs_by_mission(self, tmp_store):
        tmp_store.write_run(RunSummary(run_id="r1", mission_id="m1"))
        tmp_store.write_run(RunSummary(run_id="r2", mission_id="m2"))
        results = tmp_store.get_runs(mission_id="m1")
        assert len(results) == 1
        assert results[0].run_id == "r1"

    def test_empty_runs(self, tmp_store):
        assert tmp_store.get_runs() == []


class TestUpdateRun:
    """update_run sobrescreve campos."""

    def test_update_existing_run(self, tmp_store, sample_run):
        tmp_store.write_run(sample_run)
        updated = tmp_store.update_run("run001", status="success", duration_ms=100.0)
        assert updated is not None
        assert updated.status == "success"
        assert updated.duration_ms == 100.0
        # Verify persisted
        found = tmp_store.get_run("run001")
        assert found.status == "success"

    def test_update_nonexistent(self, tmp_store):
        assert tmp_store.update_run("ghost", status="success") is None

    def test_upsert_via_write_run(self, tmp_store, sample_run):
        tmp_store.write_run(sample_run)
        # Second write with same run_id should update
        updated = RunSummary(run_id="run001", mission_id="m001", status="completed")
        tmp_store.write_run(updated)
        found = tmp_store.get_run("run001")
        assert found.status == "completed"
