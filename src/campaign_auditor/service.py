"""Campaign Quality Batch Auditor service — P2.7."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.campaign_auditor.models import CampaignAuditResult, PackageAuditEntry

CAMPAIGNS_ROOT = Path("exports/campaigns")
PACKAGES_ROOT = Path("exports/offline_factory")
RENDER_ROOT = Path("exports/rendered")


class CampaignNotFoundError(ValueError):
    pass


def _load_campaign_manifest(campaign_dir: Path) -> Optional[dict]:
    manifest = campaign_dir / "campaign_manifest.json"
    if not manifest.exists():
        return None
    try:
        return json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        return None


def _score_package_safe(package_id: str, packages_root: Path, render_root: Path) -> PackageAuditEntry:
    from src.quality_layer.checks import run_checks, compute_score

    pkg_dir = None
    if packages_root.exists():
        for d in packages_root.iterdir():
            if d.is_dir() and d.name.startswith(package_id):
                pkg_dir = d
                break

    if not pkg_dir:
        return PackageAuditEntry(
            post_number=0,
            package_id=package_id,
            score=None,
            grade=None,
            error=f"Package '{package_id}' not found in {packages_root}",
        )

    render_dir = None
    if render_root.exists():
        for d in render_root.iterdir():
            if d.is_dir() and d.name.startswith(pkg_dir.name):
                render_dir = d
                break

    try:
        passed, failed, warnings = run_checks(pkg_dir, render_dir=render_dir)
        score = compute_score(passed)
        if score >= 90:
            grade = "ready"
        elif score >= 70:
            grade = "needs_adjustment"
        else:
            grade = "blocked"
        return PackageAuditEntry(
            post_number=0,
            package_id=pkg_dir.name,
            score=score,
            grade=grade,
            checks_failed=failed,
        )
    except Exception as exc:
        return PackageAuditEntry(
            post_number=0,
            package_id=package_id,
            score=None,
            grade=None,
            error=str(exc),
        )


def audit_campaign(
    campaign_id: str,
    campaigns_root: Path = None,
    packages_root: Path = None,
    render_root: Path = None,
) -> CampaignAuditResult:
    if campaigns_root is None:
        campaigns_root = CAMPAIGNS_ROOT
    if packages_root is None:
        packages_root = PACKAGES_ROOT
    if render_root is None:
        render_root = RENDER_ROOT

    campaign_dir = None
    if campaigns_root.exists():
        for d in campaigns_root.iterdir():
            if d.is_dir() and d.name.startswith(campaign_id):
                campaign_dir = d
                break

    if not campaign_dir:
        raise CampaignNotFoundError(f"Campaign '{campaign_id}' not found in {campaigns_root}")

    manifest = _load_campaign_manifest(campaign_dir)
    if not manifest:
        raise CampaignNotFoundError(f"No manifest in {campaign_dir}")

    posts = manifest.get("posts", [])
    entries = []
    errors = []

    for post in posts:
        pkg_id = post.get("package_id")
        entry = None
        if pkg_id:
            entry = _score_package_safe(pkg_id, packages_root, render_root)
            entry.post_number = post.get("post_number", 0)
            if entry.error:
                errors.append(f"Post {entry.post_number}: {entry.error}")
        else:
            entry = PackageAuditEntry(
                post_number=post.get("post_number", 0),
                package_id=None,
                score=None,
                grade=None,
            )
        entries.append(entry)

    scored = [e for e in entries if e.score is not None]
    unscored = len(entries) - len(scored)
    scores = [e.score for e in scored]

    avg_score = round(sum(scores) / len(scores), 1) if scores else None
    min_score = min(scores) if scores else None
    max_score = max(scores) if scores else None

    ready = sum(1 for e in scored if e.grade == "ready")
    needs = sum(1 for e in scored if e.grade == "needs_adjustment")
    blocked = sum(1 for e in scored if e.grade == "blocked")

    return CampaignAuditResult(
        campaign_id=manifest.get("campaign_id", campaign_dir.name),
        campaign_name=manifest.get("name", ""),
        account_handle=manifest.get("account_handle", ""),
        total_posts=len(posts),
        scored_posts=len(scored),
        unscored_posts=unscored,
        avg_score=avg_score,
        min_score=min_score,
        max_score=max_score,
        ready_count=ready,
        needs_adjustment_count=needs,
        blocked_count=blocked,
        entries=entries,
        errors=errors,
    )


def audit_all_campaigns(
    campaigns_root: Path = None,
    packages_root: Path = None,
    render_root: Path = None,
) -> list[CampaignAuditResult]:
    if campaigns_root is None:
        campaigns_root = CAMPAIGNS_ROOT
    if packages_root is None:
        packages_root = PACKAGES_ROOT
    if render_root is None:
        render_root = RENDER_ROOT

    if not campaigns_root.exists():
        return []

    results = []
    for d in sorted(campaigns_root.iterdir()):
        if not d.is_dir():
            continue
        try:
            result = audit_campaign(
                d.name,
                campaigns_root=campaigns_root,
                packages_root=packages_root,
                render_root=render_root,
            )
            results.append(result)
        except Exception:
            continue
    return results
