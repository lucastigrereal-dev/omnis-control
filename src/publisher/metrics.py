"""Publisher Metrics — placeholder models for post-performance data."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class PostMetrics:
    post_id: str
    content_id: str = ""
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    reach: int = 0
    impressions: int = 0
    engagement_rate: float = 0.0
    collected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def engagement_total(self) -> int:
        return self.likes + self.comments + self.shares + self.saves

    def to_dict(self) -> dict:
        return {
            "post_id": self.post_id,
            "content_id": self.content_id,
            "views": self.views,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "saves": self.saves,
            "reach": self.reach,
            "impressions": self.impressions,
            "engagement_rate": self.engagement_rate,
            "engagement_total": self.engagement_total,
            "collected_at": self.collected_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PostMetrics":
        return cls(
            post_id=d["post_id"],
            content_id=d.get("content_id", ""),
            views=d.get("views", 0),
            likes=d.get("likes", 0),
            comments=d.get("comments", 0),
            shares=d.get("shares", 0),
            saves=d.get("saves", 0),
            reach=d.get("reach", 0),
            impressions=d.get("impressions", 0),
            engagement_rate=d.get("engagement_rate", 0.0),
            collected_at=d.get("collected_at", ""),
        )


@dataclass
class PublisherMetricsReport:
    report_id: str
    metrics: list[PostMetrics] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    period_start: str = ""
    period_end: str = ""

    def add(self, m: PostMetrics) -> None:
        self.metrics.append(m)

    @property
    def total_views(self) -> int:
        return sum(m.views for m in self.metrics)

    @property
    def total_likes(self) -> int:
        return sum(m.likes for m in self.metrics)

    @property
    def total_comments(self) -> int:
        return sum(m.comments for m in self.metrics)

    @property
    def total_shares(self) -> int:
        return sum(m.shares for m in self.metrics)

    @property
    def total_engagement(self) -> int:
        return sum(m.engagement_total for m in self.metrics)

    @property
    def post_count(self) -> int:
        return len(self.metrics)

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "post_count": self.post_count,
            "totals": {
                "views": self.total_views,
                "likes": self.total_likes,
                "comments": self.total_comments,
                "shares": self.total_shares,
                "engagement": self.total_engagement,
            },
            "metrics": [m.to_dict() for m in self.metrics],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PublisherMetricsReport":
        report = cls(
            report_id=d["report_id"],
            generated_at=d.get("generated_at", ""),
            period_start=d.get("period_start", ""),
            period_end=d.get("period_end", ""),
        )
        for m in d.get("metrics", []):
            report.add(PostMetrics.from_dict(m))
        return report
