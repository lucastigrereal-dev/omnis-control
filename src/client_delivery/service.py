"""Client delivery service."""
import json
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.client_delivery.errors import DeliveryNotFoundError, DeliverySourceError
from src.client_delivery.exporter import export_delivery
from src.client_delivery.models import Delivery, DeliverySource, DeliveryStatus

DELIVERY_ROOT = Path("exports/client_delivery")
DELIVERY_ZIPS_ROOT = Path("exports/client_delivery_zips")
OFFLINE_FACTORY_ROOT = Path("exports/offline_factory")
CAMPAIGNS_ROOT = Path("exports/campaigns")


def _find_source_dir(source_type: DeliverySource, source_id: str) -> Optional[Path]:
    if source_type == DeliverySource.PACKAGE:
        root = OFFLINE_FACTORY_ROOT
    else:
        root = CAMPAIGNS_ROOT
    if not root.exists():
        return None
    for d in root.iterdir():
        if d.is_dir() and d.name.startswith(source_id):
            return d
    return None


def create_delivery_from_package(
    package_id: str,
    delivery_root: Path = None,
    offline_root: Path = None,
) -> Delivery:
    if delivery_root is None:
        delivery_root = DELIVERY_ROOT
    if offline_root is None:
        offline_root = OFFLINE_FACTORY_ROOT
    source_dir = None
    if offline_root.exists():
        for d in offline_root.iterdir():
            if d.is_dir() and d.name.startswith(package_id):
                source_dir = d
                break
    if not source_dir:
        raise DeliverySourceError(f"Package '{package_id}' not found in {offline_root}")

    delivery_id = f"delivery_{uuid.uuid4().hex[:8]}"
    created_at = datetime.now(timezone.utc).isoformat()
    out_dir = delivery_root / delivery_id

    delivery = Delivery(
        delivery_id=delivery_id,
        source_type=DeliverySource.PACKAGE,
        source_id=source_dir.name,
        status=DeliveryStatus.DRAFT,
        output_dir=str(out_dir),
        created_at=created_at,
    )

    files = export_delivery(delivery, out_dir, source_dir=source_dir)
    delivery.files_generated = files
    delivery.status = DeliveryStatus.READY

    (out_dir / "delivery_manifest.json").write_text(
        json.dumps(delivery.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return delivery


def create_delivery_from_campaign(
    campaign_id: str,
    delivery_root: Path = None,
    campaigns_root: Path = None,
) -> Delivery:
    if delivery_root is None:
        delivery_root = DELIVERY_ROOT
    if campaigns_root is None:
        campaigns_root = CAMPAIGNS_ROOT
    source_dir = None
    if campaigns_root.exists():
        for d in campaigns_root.iterdir():
            if d.is_dir() and d.name.startswith(campaign_id):
                source_dir = d
                break
    if not source_dir:
        raise DeliverySourceError(f"Campaign '{campaign_id}' not found in {campaigns_root}")

    delivery_id = f"delivery_{uuid.uuid4().hex[:8]}"
    created_at = datetime.now(timezone.utc).isoformat()
    out_dir = delivery_root / delivery_id

    delivery = Delivery(
        delivery_id=delivery_id,
        source_type=DeliverySource.CAMPAIGN,
        source_id=source_dir.name,
        status=DeliveryStatus.DRAFT,
        output_dir=str(out_dir),
        created_at=created_at,
    )

    files = export_delivery(delivery, out_dir, source_dir=source_dir)
    delivery.files_generated = files
    delivery.status = DeliveryStatus.READY

    (out_dir / "delivery_manifest.json").write_text(
        json.dumps(delivery.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return delivery


def list_deliveries(delivery_root: Path = None) -> list[dict]:
    if delivery_root is None:
        delivery_root = DELIVERY_ROOT
    if not delivery_root.exists():
        return []
    results = []
    for d in delivery_root.iterdir():
        if not d.is_dir():
            continue
        manifest_path = d / "delivery_manifest.json"
        if not manifest_path.exists():
            continue
        try:
            results.append(json.loads(manifest_path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return results


def get_delivery(delivery_id_prefix: str, delivery_root: Path = None) -> Optional[dict]:
    if delivery_root is None:
        delivery_root = DELIVERY_ROOT
    if not delivery_root.exists():
        return None
    for d in delivery_root.iterdir():
        if d.is_dir() and d.name.startswith(delivery_id_prefix):
            manifest_path = d / "delivery_manifest.json"
            if manifest_path.exists():
                try:
                    return json.loads(manifest_path.read_text(encoding="utf-8"))
                except Exception:
                    pass
    return None


def zip_delivery(
    delivery_id_prefix: str,
    delivery_root: Path = None,
    zips_root: Path = None,
) -> dict:
    if delivery_root is None:
        delivery_root = DELIVERY_ROOT
    if zips_root is None:
        zips_root = DELIVERY_ZIPS_ROOT
    delivery_dir = None
    if delivery_root.exists():
        for d in delivery_root.iterdir():
            if d.is_dir() and d.name.startswith(delivery_id_prefix):
                delivery_dir = d
                break
    if not delivery_dir:
        raise DeliveryNotFoundError(f"Delivery '{delivery_id_prefix}' not found")

    zips_root.mkdir(parents=True, exist_ok=True)
    zip_path = zips_root / f"{delivery_dir.name}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in delivery_dir.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(delivery_dir.parent))

    size_kb = round(zip_path.stat().st_size / 1024, 1)
    return {
        "delivery_id": delivery_dir.name,
        "zip_path": str(zip_path),
        "size_kb": size_kb,
    }
