"""Offline Dashboard service — read-only aggregation of factory state."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

EXPORT_ROOT = Path("exports/offline_factory")
RENDER_ROOT = Path("exports/rendered")
CAMPAIGNS_ROOT = Path("exports/campaigns")
DELIVERY_ROOT = Path("exports/client_delivery")
MANUAL_LOG = Path("data/manual_publishing_log.jsonl")
SCORES_LOG = Path("data/quality_scores.jsonl")

# OAuth gate target
OAUTH_TARGET = 5


def _count_dirs(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for d in root.iterdir() if d.is_dir())


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _package_status_counts(root: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not root.exists():
        return counts
    for d in root.iterdir():
        if not d.is_dir():
            continue
        manifest = d / "manifest.json"
        if manifest.exists():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                status = data.get("status", "unknown")
            except Exception:
                status = "unknown"
        else:
            status = "unknown"
        counts[status] = counts.get(status, 0) + 1
    return counts


def _campaign_status_counts(root: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not root.exists():
        return counts
    for d in root.iterdir():
        if not d.is_dir():
            continue
        meta = d / "campaign.json"
        if meta.exists():
            try:
                data = json.loads(meta.read_text(encoding="utf-8"))
                status = data.get("status", "unknown")
            except Exception:
                status = "unknown"
        else:
            status = "unknown"
        counts[status] = counts.get(status, 0) + 1
    return counts


def _oauth_ready_count() -> int:
    try:
        from src.oauth_readiness.checker import OAuthReadinessChecker
        report = OAuthReadinessChecker().check_all()
        return getattr(report, "ready_count", 0)
    except Exception:
        return 0


def _avg_quality_score(scores: list[dict]) -> Optional[float]:
    if not scores:
        return None
    values = [s.get("score") for s in scores if isinstance(s.get("score"), (int, float))]
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def get_dashboard_data() -> dict:
    """Return read-only snapshot of factory production state."""
    package_counts = _package_status_counts(EXPORT_ROOT)
    render_count = _count_dirs(RENDER_ROOT)
    campaign_counts = _campaign_status_counts(CAMPAIGNS_ROOT)
    delivery_count = _count_dirs(DELIVERY_ROOT)
    manual_records = _load_jsonl(MANUAL_LOG)
    quality_scores = _load_jsonl(SCORES_LOG)
    oauth_ready = _oauth_ready_count()

    return {
        "packages": {
            "total": sum(package_counts.values()),
            "by_status": package_counts,
        },
        "renders": render_count,
        "quality": {
            "scored_count": len(quality_scores),
            "avg_score": _avg_quality_score(quality_scores),
        },
        "campaigns": {
            "total": sum(campaign_counts.values()),
            "by_status": campaign_counts,
        },
        "deliveries": delivery_count,
        "manual_published": len(manual_records),
        "oauth_gate": {
            "ready": oauth_ready,
            "target": OAUTH_TARGET,
            "go": oauth_ready >= OAUTH_TARGET,
        },
    }
