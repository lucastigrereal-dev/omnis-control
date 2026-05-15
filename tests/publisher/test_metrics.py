"""Tests for publisher metrics placeholder (W087)."""
from __future__ import annotations

from src.publisher.metrics import PostMetrics, PublisherMetricsReport


class TestPostMetrics:
    def test_defaults(self):
        m = PostMetrics(post_id="p1")
        assert m.post_id == "p1"
        assert m.views == 0
        assert m.likes == 0
        assert m.comments == 0
        assert m.shares == 0
        assert m.saves == 0

    def test_engagement_total(self):
        m = PostMetrics(post_id="p1", likes=10, comments=3, shares=2, saves=1)
        assert m.engagement_total == 16

    def test_engagement_total_zero(self):
        m = PostMetrics(post_id="p1")
        assert m.engagement_total == 0

    def test_to_dict_roundtrip(self):
        m = PostMetrics(
            post_id="p1", content_id="c1",
            views=1000, likes=50, comments=10,
            shares=5, saves=3, reach=800, impressions=1200,
            engagement_rate=0.068,
        )
        restored = PostMetrics.from_dict(m.to_dict())
        assert restored.post_id == "p1"
        assert restored.views == 1000
        assert restored.likes == 50
        assert restored.engagement_rate == 0.068


class TestPublisherMetricsReport:
    def test_empty_report(self):
        r = PublisherMetricsReport(report_id="r1")
        assert r.post_count == 0
        assert r.total_views == 0
        assert r.total_engagement == 0

    def test_add_metrics(self):
        r = PublisherMetricsReport(report_id="r1")
        m1 = PostMetrics(post_id="p1", views=100, likes=10, comments=2, shares=1, saves=1)
        m2 = PostMetrics(post_id="p2", views=200, likes=20, comments=4, shares=2, saves=2)
        r.add(m1)
        r.add(m2)
        assert r.post_count == 2
        assert r.total_views == 300
        assert r.total_likes == 30
        assert r.total_comments == 6
        assert r.total_shares == 3
        assert r.total_engagement == 42

    def test_to_dict_roundtrip(self):
        r = PublisherMetricsReport(report_id="r1", period_start="2026-05-01", period_end="2026-05-15")
        r.add(PostMetrics(post_id="p1", views=100, likes=10))
        restored = PublisherMetricsReport.from_dict(r.to_dict())
        assert restored.report_id == "r1"
        assert restored.period_start == "2026-05-01"
        assert restored.post_count == 1
        assert restored.total_views == 100
