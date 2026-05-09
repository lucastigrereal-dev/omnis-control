"""Campaign package service."""
import json
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.campaign_package.errors import CampaignNotFoundError, CampaignValidationError
from src.campaign_package.exporter import export_campaign
from src.campaign_package.models import Campaign, CampaignPost, CampaignStatus

CAMPAIGNS_ROOT = Path("exports/campaigns")
CAMPAIGN_ZIPS_ROOT = Path("exports/campaign_zips")


def _make_posts(count: int, account_handle: str) -> list[CampaignPost]:
    posts = []
    for i in range(1, count + 1):
        posts.append(CampaignPost(
            post_number=i,
            title=f"Post {i:02d}",
            account_handle=account_handle,
            scheduled_date=f"2026-06-{i:02d}",
            status="draft",
        ))
    return posts


def create_campaign(
    name: str,
    count: int = 10,
    account_handle: str = "afamiliatigrereal",
    campaigns_root: Path = CAMPAIGNS_ROOT,
) -> Campaign:
    if count < 1 or count > 50:
        raise CampaignValidationError(f"count must be between 1 and 50, got {count}")

    campaign_id = f"campaign_{uuid.uuid4().hex[:8]}"
    created_at = datetime.now(timezone.utc).isoformat()
    out_dir = campaigns_root / campaign_id
    posts = _make_posts(count, account_handle)

    campaign = Campaign(
        campaign_id=campaign_id,
        name=name,
        post_count=count,
        status=CampaignStatus.DRAFT,
        account_handle=account_handle,
        created_at=created_at,
        output_dir=str(out_dir),
        posts=posts,
    )

    export_campaign(campaign, out_dir)
    campaign.status = CampaignStatus.READY
    # Re-write manifest with READY status
    (out_dir / "campaign_manifest.json").write_text(
        json.dumps(campaign.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return campaign


def list_campaigns(campaigns_root: Path = CAMPAIGNS_ROOT) -> list[dict]:
    if not campaigns_root.exists():
        return []
    results = []
    for d in campaigns_root.iterdir():
        if not d.is_dir():
            continue
        manifest_path = d / "campaign_manifest.json"
        if not manifest_path.exists():
            continue
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            results.append(data)
        except Exception:
            continue
    return results


def get_campaign(campaign_id_prefix: str, campaigns_root: Path = CAMPAIGNS_ROOT) -> Optional[dict]:
    if not campaigns_root.exists():
        return None
    for d in campaigns_root.iterdir():
        if d.is_dir() and d.name.startswith(campaign_id_prefix):
            manifest_path = d / "campaign_manifest.json"
            if manifest_path.exists():
                try:
                    return json.loads(manifest_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
    return None


def validate_campaign(campaign_id_prefix: str, campaigns_root: Path = CAMPAIGNS_ROOT) -> dict:
    """Quick structural validation of a campaign."""
    if not campaigns_root.exists():
        raise CampaignNotFoundError(f"Campaign '{campaign_id_prefix}' not found")
    campaign_dir = None
    for d in campaigns_root.iterdir():
        if d.is_dir() and d.name.startswith(campaign_id_prefix):
            campaign_dir = d
            break
    if not campaign_dir:
        raise CampaignNotFoundError(f"Campaign '{campaign_id_prefix}' not found")

    checks_passed = []
    checks_failed = []

    if (campaign_dir / "campaign_manifest.json").exists():
        checks_passed.append("manifest_exists")
    else:
        checks_failed.append("manifest_exists")

    if (campaign_dir / "calendar.csv").exists():
        checks_passed.append("calendar_exists")
    else:
        checks_failed.append("calendar_exists")

    if (campaign_dir / "README.md").exists():
        checks_passed.append("readme_exists")
    else:
        checks_failed.append("readme_exists")

    if (campaign_dir / "posts").is_dir():
        checks_passed.append("posts_dir_exists")
    else:
        checks_failed.append("posts_dir_exists")

    manifest = {}
    try:
        manifest = json.loads((campaign_dir / "campaign_manifest.json").read_text(encoding="utf-8"))
        posts = manifest.get("posts", [])
        if len(posts) >= 1:
            checks_passed.append("has_posts")
        else:
            checks_failed.append("has_posts")
    except Exception:
        checks_failed.append("manifest_valid_json")

    return {
        "campaign_id": campaign_dir.name,
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "is_valid": len(checks_failed) == 0,
        "post_count": manifest.get("post_count", 0),
    }


def zip_campaign(
    campaign_id_prefix: str,
    campaigns_root: Path = CAMPAIGNS_ROOT,
    zips_root: Path = CAMPAIGN_ZIPS_ROOT,
) -> dict:
    if not campaigns_root.exists():
        raise CampaignNotFoundError(f"Campaign '{campaign_id_prefix}' not found")
    campaign_dir = None
    for d in campaigns_root.iterdir():
        if d.is_dir() and d.name.startswith(campaign_id_prefix):
            campaign_dir = d
            break
    if not campaign_dir:
        raise CampaignNotFoundError(f"Campaign '{campaign_id_prefix}' not found")

    zips_root.mkdir(parents=True, exist_ok=True)
    zip_path = zips_root / f"{campaign_dir.name}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in campaign_dir.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(campaign_dir.parent))

    size_kb = round(zip_path.stat().st_size / 1024, 1)
    return {
        "campaign_id": campaign_dir.name,
        "zip_path": str(zip_path),
        "size_kb": size_kb,
    }
