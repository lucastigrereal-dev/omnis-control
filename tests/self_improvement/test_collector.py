"""Tests for P28 FeedbackCollector."""
import pytest

from src.self_improvement.collector import FeedbackCollector
from src.self_improvement.models import (
    ExecutionFeedback,
    SOURCE_MISSION, SOURCE_BUILD, SOURCE_ACTION, SOURCE_SYSTEM,
)


class TestFeedbackCollector:
    @pytest.fixture
    def collector(self):
        return FeedbackCollector(dry_run=True)

    def test_collect_all_populates_feedback(self, collector):
        fb_list = collector.collect_all()
        assert len(fb_list) >= 10
        assert collector.count >= 10

    def test_collect_from_missions(self, collector):
        fb_list = collector.collect_from_missions()
        assert len(fb_list) >= 1
        assert all(f.source_type == SOURCE_MISSION for f in fb_list)

    def test_collect_from_builds(self, collector):
        fb_list = collector.collect_from_builds()
        assert len(fb_list) >= 1
        assert all(f.source_type == SOURCE_BUILD for f in fb_list)

    def test_collect_from_actions(self, collector):
        fb_list = collector.collect_from_actions()
        assert len(fb_list) >= 1
        assert all(f.source_type == SOURCE_ACTION for f in fb_list)

    def test_collect_from_system(self, collector):
        fb = collector.collect_from_system()
        assert fb is not None
        assert fb.source_type == SOURCE_SYSTEM
        assert fb.source_id == "system"

    def test_get_failures(self, collector):
        collector.collect_all()
        failures = collector.get_failures()
        # Some mock entries are failures/partial
        for f in failures:
            assert f.is_failure is True

    def test_get_by_source(self, collector):
        collector.collect_all()
        missions = collector.get_by_source(SOURCE_MISSION)
        assert len(missions) >= 1
        builds = collector.get_by_source(SOURCE_BUILD)
        assert len(builds) >= 1

    def test_failure_rate_between_zero_and_one(self, collector):
        collector.collect_all()
        rate = collector.failure_rate
        assert 0.0 <= rate <= 1.0

    def test_empty_collector_has_zero_failure_rate(self, collector):
        assert collector.count == 0
        assert collector.failure_rate == 0.0

    def test_get_all_returns_copy(self, collector):
        collector.collect_all()
        all_fb = collector.get_all()
        assert len(all_fb) == collector.count

    def test_mock_feedbacks_contain_varied_statuses(self, collector):
        collector.collect_all()
        statuses = {f.status for f in collector.get_all()}
        assert len(statuses) >= 2  # At least success and failure present

    def test_collect_all_includes_models_used(self, collector):
        collector.collect_all()
        models = {f.model_used for f in collector.get_all() if f.model_used}
        assert len(models) >= 1

    def test_collect_from_missions_with_since(self, collector):
        fb_list = collector.collect_from_missions(since="2026-05-01")
        assert len(fb_list) >= 1
