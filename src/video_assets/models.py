"""Modelo de dados VideoAsset e tipos suportados."""

import unicodedata
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone

from .status import AssetStatus


class AssetSourceType:
    LOCAL = "local"
    GOOGLE_DRIVE = "google_drive"
    MANUAL = "manual"
    UNKNOWN = "unknown"


class AssetFormat:
    REEL = "reel"
    CAROUSEL = "carousel"
    STATIC = "static"
    STORY = "story"
    UNKNOWN = "unknown"


def _normalize_account(account: str) -> str:
    """Remove @, lowercase, trim."""
    return account.strip().lstrip("@").lower()


def _normalize_city(city: str) -> str:
    """Lowercase, remove accents, trim."""
    normalized = unicodedata.normalize("NFKD", city.strip().lower())
    return re.sub(r"[^a-z0-9\s-]", "", normalized).strip()


def _make_fingerprint(source_path: str, size_bytes: int, modified_at: str) -> str:
    """Fingerprint sem SHA256: path + size + mtime."""
    return f"{source_path}|{size_bytes}|{modified_at}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class VideoAsset:
    asset_id: str
    source_type: str  # local | google_drive | manual | unknown
    source_path: str
    file_name: str
    extension: str
    size_bytes: int
    fingerprint: str

    status: AssetStatus = AssetStatus.INBOX

    # Metadados opcionais
    drive_file_id: str | None = None
    account_target: str | None = None  # @handle normalizado
    tags: list[str] = field(default_factory=list)
    city: str | None = None  # normalizado
    format: str = AssetFormat.UNKNOWN
    caption: str | None = None
    hashtags: str | None = None
    cta: str | None = None

    # Timestamps
    used_at: str | None = None
    scheduled_at: str | None = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    notes: str | None = None

    @classmethod
    def new(
        cls,
        asset_id: str,
        source_type: str,
        source_path: str,
        file_name: str,
        extension: str,
        size_bytes: int,
        **kwargs: object,
    ) -> "VideoAsset":
        modified_at = kwargs.pop("modified_at", _now_iso())
        fingerprint = _make_fingerprint(source_path, size_bytes, modified_at)

        # Normalizar campos
        account = kwargs.pop("account_target", None)
        if account is not None:
            kwargs["account_target"] = _normalize_account(account)
        city = kwargs.pop("city", None)
        if city is not None:
            kwargs["city"] = _normalize_city(city)

        return cls(
            asset_id=asset_id,
            source_type=source_type,
            source_path=source_path,
            file_name=file_name,
            extension=extension,
            size_bytes=size_bytes,
            fingerprint=fingerprint,
            **kwargs,
        )

    def to_dict(self) -> dict[str, object]:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "VideoAsset":
        data = dict(data)
        data["status"] = AssetStatus(data.get("status", "inbox"))
        return cls(**data)

    def normalize(self) -> None:
        """Re-normaliza campos in-place."""
        if self.account_target:
            self.account_target = _normalize_account(self.account_target)
        if self.city:
            self.city = _normalize_city(self.city)
