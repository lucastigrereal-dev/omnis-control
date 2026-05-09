"""Campaign auditor models."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PackageAuditEntry:
    post_number: int
    package_id: Optional[str]
    score: Optional[int]          # None = not scored (no package)
    grade: Optional[str]
    checks_failed: list[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "post_number": self.post_number,
            "package_id": self.package_id,
            "score": self.score,
            "grade": self.grade,
            "checks_failed": self.checks_failed,
            "error": self.error,
        }


@dataclass
class CampaignAuditResult:
    campaign_id: str
    campaign_name: str
    account_handle: str
    total_posts: int
    scored_posts: int
    unscored_posts: int          # posts without a package_id
    avg_score: Optional[float]
    min_score: Optional[int]
    max_score: Optional[int]
    ready_count: int             # score >= 90
    needs_adjustment_count: int  # 70 <= score < 90
    blocked_count: int           # score < 70
    entries: list[PackageAuditEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def overall_grade(self) -> str:
        if self.avg_score is None:
            return "unscored"
        if self.avg_score >= 90:
            return "ready"
        if self.avg_score >= 70:
            return "needs_adjustment"
        return "blocked"

    def to_dict(self) -> dict:
        return {
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "account_handle": self.account_handle,
            "total_posts": self.total_posts,
            "scored_posts": self.scored_posts,
            "unscored_posts": self.unscored_posts,
            "avg_score": self.avg_score,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "ready_count": self.ready_count,
            "needs_adjustment_count": self.needs_adjustment_count,
            "blocked_count": self.blocked_count,
            "overall_grade": self.overall_grade(),
            "entries": [e.to_dict() for e in self.entries],
            "errors": self.errors,
        }
