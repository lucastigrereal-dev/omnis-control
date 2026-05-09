"""Manifest generator — JSON index for delivery packages."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import DeliveryPackage


def generate_manifest(pkg: DeliveryPackage, package_dir: Path) -> Path:
    """Generate manifest.json for a delivery package.

    Returns path to generated manifest.
    """
    manifest = {
        "package_id": pkg.package_id,
        "package_type": pkg.package_type.value,
        "title": pkg.title,
        "account_handle": pkg.account_handle,
        "source_queue_id": pkg.source_queue_id,
        "source_caption_id": pkg.source_caption_id,
        "source_brief_id": pkg.source_brief_id,
        "asset_ids": pkg.asset_ids,
        "status": pkg.status.value,
        "files": _catalog_files(package_dir, pkg.files),
        "warnings": pkg.warnings,
        "blockers": pkg.blockers,
        "next_actions": pkg.next_actions,
        "seo_keywords": pkg.seo_keywords,
        "hashtags": pkg.hashtags,
        "cta": pkg.cta,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    manifest_path = package_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest_path


def read_manifest(package_dir: Path) -> Optional[dict]:
    """Read existing manifest.json from a package directory."""
    path = package_dir / "manifest.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _catalog_files(package_dir: Path, filenames: list[str]) -> list[dict]:
    """Build file catalog with sizes."""
    catalog = []
    for name in filenames:
        fpath = package_dir / name
        size = fpath.stat().st_size if fpath.is_file() else 0
        catalog.append({
            "name": name,
            "size_bytes": size,
        })
    return catalog
