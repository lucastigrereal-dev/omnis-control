"""Asset Inbox Registry — JSONL-based, append-only. No external DB."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.asset_inbox.models import ImportedAsset

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_REGISTRY_PATH = BASE / "data" / "asset_inbox_registry.jsonl"


class AssetInboxRegistry:
    def __init__(self, registry_path: Path = DEFAULT_REGISTRY_PATH) -> None:
        self._path = registry_path

    def add(self, asset: ImportedAsset) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asset.to_dict(), ensure_ascii=False) + "\n")

    def list(self) -> list[ImportedAsset]:
        if not self._path.exists():
            return []
        entries = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(ImportedAsset.from_dict(json.loads(line)))
            except (json.JSONDecodeError, TypeError, KeyError):
                continue  # tolerate corrupt lines
        return list(reversed(entries))  # newest first

    def get(self, asset_id: str) -> Optional[ImportedAsset]:
        for asset in self.list():
            if asset.asset_id == asset_id:
                return asset
        return None

    def find_by_fingerprint(self, fingerprint: str) -> Optional[ImportedAsset]:
        for asset in self.list():
            if asset.source_fingerprint == fingerprint:
                return asset
        return None

    def exists(self, asset_id: str) -> bool:
        return self.get(asset_id) is not None
