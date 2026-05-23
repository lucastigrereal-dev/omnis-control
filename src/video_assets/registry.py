"""Registry — CRUD JSONL para VideoAsset."""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .models import VideoAsset
from .status import AssetStatus

_ROOT = os.path.normpath(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control")))
REGISTRY_PATH = os.path.join(_ROOT, "data", "video_assets.jsonl")


class Registry:
    """Gerencia o arquivo JSONL de assets de vídeo."""

    def __init__(self, path: str = REGISTRY_PATH):
        self.path = path
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        Path(os.path.dirname(self.path)).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ CRUD

    def add(self, asset: VideoAsset) -> VideoAsset:
        """Adiciona um novo asset ao registro."""
        if not asset.asset_id:
            asset.asset_id = uuid.uuid4().hex[:12]
        asset.created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        asset.updated_at = asset.created_at
        self._append(asset)
        return asset

    def get(self, asset_id: str) -> VideoAsset | None:
        """Busca um asset por ID."""
        for asset in self.list_all():
            if asset.asset_id == asset_id:
                return asset
        return None

    def update(self, asset_id: str, **kwargs: object) -> VideoAsset | None:
        """Atualiza campos de um asset."""
        assets = self.list_all()
        found = None
        for i, a in enumerate(assets):
            if a.asset_id == asset_id:
                for key, val in kwargs.items():
                    if hasattr(a, key) and val is not None:
                        setattr(a, key, val)
                # Re-normalizar se necessário
                a.normalize()
                a.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                found = a
                assets[i] = a
                break
        if found:
            self._rewrite(assets)
        return found

    def delete(self, asset_id: str) -> bool:
        """Remove um asset do registro."""
        assets = self.list_all()
        new_assets = [a for a in assets if a.asset_id != asset_id]
        if len(new_assets) == len(assets):
            return False
        self._rewrite(new_assets)
        return True

    def list_all(self) -> list[VideoAsset]:
        """Retorna todos os assets."""
        if not os.path.isfile(self.path):
            return []
        assets = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        assets.append(VideoAsset.from_dict(json.loads(line)))
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        return assets

    def filter(
        self,
        status: AssetStatus | None = None,
        account: str | None = None,
        tag: str | None = None,
    ) -> list[VideoAsset]:
        """Filtra assets por status, conta ou tag."""
        results = self.list_all()
        if status:
            results = [a for a in results if a.status == status]
        if account:
            acct = account.strip().lstrip("@").lower()
            results = [a for a in results if a.account_target == acct]
        if tag:
            results = [a for a in results if tag in a.tags]
        return results

    def count(self, status: AssetStatus | None = None) -> int:
        """Contagem rápida (opcionalmente filtrada por status)."""
        if not os.path.isfile(self.path):
            return 0
        if status is None:
            # Contagem rápida: contar linhas
            with open(self.path, encoding="utf-8") as f:
                return sum(1 for line in f if line.strip())
        return len(self.filter(status=status))

    # ------------------------------------------------------------------ Status

    def transition(self, asset_id: str, target: AssetStatus) -> VideoAsset | None:
        """Transiciona asset para novo status, validando a transição."""
        asset = self.get(asset_id)
        if not asset:
            return None
        if not asset.status.can_transition_to(target):
            raise ValueError(
                f"Transição inválida: {asset.status.value} → {target.value}"
            )
        return self.update(asset_id, status=target)

    def mark_published(self, asset_id: str) -> VideoAsset | None:
        """Marca como publicado e auto-preenche used_at."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return self.update(asset_id, status=AssetStatus.PUBLISHED, used_at=now)

    # ------------------------------------------------------------------ Stats

    def stats(self) -> dict[str, object]:
        """Estatísticas agregadas do registro."""
        assets = self.list_all()
        total = len(assets)
        by_status = {}
        for a in assets:
            s = a.status.value
            by_status[s] = by_status.get(s, 0) + 1
        total_bytes = sum(a.size_bytes for a in assets)
        formats = {}
        for a in assets:
            f = a.format or "unknown"
            formats[f] = formats.get(f, 0) + 1
        return {
            "total": total,
            "by_status": by_status,
            "total_bytes": total_bytes,
            "formats": formats,
        }

    def export_csv(self, path: str) -> None:
        """Exporta registro como CSV."""
        assets = self.list_all()
        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            if not assets:
                return
            writer = csv.DictWriter(f, fieldnames=assets[0].to_dict().keys())
            writer.writeheader()
            for a in assets:
                writer.writerow(a.to_dict())

    # ------------------------------------------------------------------ Internal

    def _append(self, asset: VideoAsset) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asset.to_dict(), ensure_ascii=False) + "\n")

    def _rewrite(self, assets: list[VideoAsset]) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            for a in assets:
                f.write(json.dumps(a.to_dict(), ensure_ascii=False) + "\n")
