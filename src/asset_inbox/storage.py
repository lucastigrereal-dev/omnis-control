"""Asset Inbox Storage — manages local copy area. Never touches originals."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Optional

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_STORAGE_ROOT = BASE / "storage" / "asset_inbox"


def get_asset_dir(asset_id: str, storage_root: Path = DEFAULT_STORAGE_ROOT) -> Path:
    return storage_root / asset_id


def asset_exists(asset_id: str, storage_root: Path = DEFAULT_STORAGE_ROOT) -> bool:
    return get_asset_dir(asset_id, storage_root).is_dir()


def store_copy(
    source: Path,
    asset_id: str,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
) -> Path:
    """Copy source file into storage/<asset_id>/original_copy<ext>. Returns stored path.

    Uses shutil.copy2 (preserves metadata). Never moves or modifies source.
    Raises OSError if copy fails.
    """
    dest_dir = get_asset_dir(asset_id, storage_root)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"original_copy{source.suffix.lower()}"
    shutil.copy2(str(source), str(dest))
    return dest


def write_import_manifest(
    asset_id: str,
    manifest_data: dict,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
) -> None:
    dest_dir = get_asset_dir(asset_id, storage_root)
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / "import_manifest.json").write_text(
        json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def read_import_manifest(
    asset_id: str,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
) -> Optional[dict]:
    manifest_path = get_asset_dir(asset_id, storage_root) / "import_manifest.json"
    if not manifest_path.exists():
        return None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
