"""Asset Inbox Assignment — assigns imported asset to queue or mission package.

NUNCA move original.
NUNCA publica.
NUNCA chama rede.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.asset_inbox.models import _now_iso
from src.asset_inbox.registry import AssetInboxRegistry, DEFAULT_REGISTRY_PATH

BASE = Path(__file__).resolve().parent.parent.parent

DEFAULT_VIDEO_ASSETS_PATH = str(BASE / "data" / "video_assets.jsonl")
DEFAULT_QUEUE_PATH = str(BASE / "data" / "content_queue.jsonl")
DEFAULT_PACKAGES_ROOT = BASE / "exports" / "mission_packages"
DEFAULT_INBOX_REGISTRY_PATH = DEFAULT_REGISTRY_PATH

# Assignment status values
ASSIGN_STATUS_OK = "assigned"
ASSIGN_STATUS_NOT_FOUND = "asset_not_found"
ASSIGN_STATUS_QUEUE_NOT_FOUND = "queue_item_not_found"
ASSIGN_STATUS_MISSION_NOT_FOUND = "mission_package_not_found"
ASSIGN_STATUS_ALREADY_ASSIGNED = "already_assigned"
ASSIGN_STATUS_FAILED = "failed"


@dataclass
class AssetAssignmentResult:
    status: str
    asset_id: str = ""
    target_type: str = ""  # "queue" | "mission"
    target_id: str = ""
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "asset_id": self.asset_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "warnings": self.warnings,
            "blockers": self.blockers,
            "created_at": self.created_at,
            "next_actions": ["B8D E2E Smoke Mission"] if self.status == ASSIGN_STATUS_OK else [],
        }


def assign_to_queue(
    asset_id: str,
    queue_id: str,
    force: bool = False,
    inbox_registry_path: Path = DEFAULT_INBOX_REGISTRY_PATH,
    video_assets_path: str = DEFAULT_VIDEO_ASSETS_PATH,
    queue_path: str = DEFAULT_QUEUE_PATH,
) -> AssetAssignmentResult:
    """Assigns imported asset to a queue slot.

    Creates VideoAsset entry in video_assets registry, updates queue item.
    Uses Queue.update() directly — avoids hardcoded VIDEO_ASSETS_PATH in Queue.assign_asset().
    """
    registry = AssetInboxRegistry(inbox_registry_path)
    imported = registry.get(asset_id)
    if imported is None:
        return AssetAssignmentResult(
            status=ASSIGN_STATUS_NOT_FOUND,
            asset_id=asset_id,
            target_type="queue",
            target_id=queue_id,
            blockers=[f"Asset {asset_id} not found in inbox registry"],
        )

    from src.video_assets.registry import Registry as VARegistry
    from src.video_assets.models import VideoAsset, AssetSourceType

    va_registry = VARegistry(path=video_assets_path)
    existing_va = va_registry.get(imported.asset_id)
    if existing_va is None:
        va = VideoAsset.new(
            asset_id=imported.asset_id,
            source_type=AssetSourceType.LOCAL,
            source_path=imported.stored_path,
            file_name=imported.file_name,
            extension=imported.extension,
            size_bytes=imported.size_bytes,
        )
        va_registry.add(va)

    from src.content_queue.queue import Queue

    q = Queue(path=queue_path)
    item = q.get(queue_id)
    if item is None:
        return AssetAssignmentResult(
            status=ASSIGN_STATUS_QUEUE_NOT_FOUND,
            asset_id=asset_id,
            target_type="queue",
            target_id=queue_id,
            blockers=[f"Queue item {queue_id} not found"],
        )

    warnings: list[str] = []
    if item.asset_id is not None and item.asset_id != asset_id and not force:
        return AssetAssignmentResult(
            status=ASSIGN_STATUS_ALREADY_ASSIGNED,
            asset_id=asset_id,
            target_type="queue",
            target_id=queue_id,
            blockers=[f"Queue item already has asset '{item.asset_id}'. Use force=True to override."],
        )
    if item.asset_id is not None and force:
        warnings.append(f"Overriding existing asset {item.asset_id}")

    updated = q.update(queue_id, asset_id=imported.asset_id)
    if updated is None:
        return AssetAssignmentResult(
            status=ASSIGN_STATUS_FAILED,
            asset_id=asset_id,
            target_type="queue",
            target_id=queue_id,
            blockers=["Failed to update queue item"],
        )

    return AssetAssignmentResult(
        status=ASSIGN_STATUS_OK,
        asset_id=asset_id,
        target_type="queue",
        target_id=queue_id,
        warnings=warnings,
    )


def assign_to_mission(
    asset_id: str,
    mission_id: str,
    inbox_registry_path: Path = DEFAULT_INBOX_REGISTRY_PATH,
    packages_root: Path = DEFAULT_PACKAGES_ROOT,
) -> AssetAssignmentResult:
    """Assigns imported asset to a mission package.

    Writes 04_outputs/asset_reference.json to mission package dir.
    Updates mission_manifest.json with assigned_asset_id if present.
    """
    registry = AssetInboxRegistry(inbox_registry_path)
    imported = registry.get(asset_id)
    if imported is None:
        return AssetAssignmentResult(
            status=ASSIGN_STATUS_NOT_FOUND,
            asset_id=asset_id,
            target_type="mission",
            target_id=mission_id,
            blockers=[f"Asset {asset_id} not found in inbox registry"],
        )

    package_dir = Path(packages_root) / mission_id
    if not package_dir.exists():
        return AssetAssignmentResult(
            status=ASSIGN_STATUS_MISSION_NOT_FOUND,
            asset_id=asset_id,
            target_type="mission",
            target_id=mission_id,
            blockers=[f"Mission package {mission_id} not found at {package_dir}"],
        )

    outputs_dir = package_dir / "04_outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    now = _now_iso()
    asset_ref = {
        "asset_id": imported.asset_id,
        "file_name": imported.file_name,
        "extension": imported.extension,
        "media_type": imported.media_type,
        "stored_path": imported.stored_path,
        "source_fingerprint": imported.source_fingerprint,
        "fingerprint_match": imported.fingerprint_match,
        "size_bytes": imported.size_bytes,
        "assigned_at": now,
        "mission_id": mission_id,
    }

    ref_path = outputs_dir / "asset_reference.json"
    ref_path.write_text(
        json.dumps(asset_ref, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    warnings: list[str] = []
    manifest_path = package_dir / "mission_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["assigned_asset_id"] = imported.asset_id
            manifest["assigned_at"] = now
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            warnings.append(f"Could not update mission_manifest.json: {exc}")
    else:
        warnings.append("mission_manifest.json not found — asset_reference.json written only")

    return AssetAssignmentResult(
        status=ASSIGN_STATUS_OK,
        asset_id=asset_id,
        target_type="mission",
        target_id=mission_id,
        warnings=warnings,
    )
