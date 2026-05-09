"""Package zipper — stdlib zipfile, zero external deps. FASE 5.

Creates ZIP archives of delivery packages for manual delivery.
NEVER calls external APIs. NEVER publishes.
"""
from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ZIP_ROOT_DEFAULT = None  # resolved at call time from EXPORT_ROOT sibling


@dataclass
class ZipResult:
    package_id: str
    zip_path: str
    files_zipped: int
    size_bytes: int

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "zip_path": self.zip_path,
            "files_zipped": self.files_zipped,
            "size_bytes": self.size_bytes,
        }


def zip_package(package_id: str, export_root: Path, zip_root: Optional[Path] = None) -> ZipResult:
    """Find package by ID (prefix match), zip it, return ZipResult.

    Args:
        package_id: Full or prefix of package ID.
        export_root: exports/offline_factory/ root.
        zip_root: Where to place the zip. Defaults to exports/offline_factory_zips/.
    """
    if zip_root is None:
        zip_root = export_root.parent / "offline_factory_zips"

    if not export_root.exists():
        raise FileNotFoundError(f"Export root nao encontrado: {export_root}")

    matches = [d for d in export_root.iterdir() if d.is_dir() and d.name.startswith(package_id)]
    if not matches:
        raise FileNotFoundError(f"Pacote '{package_id}' nao encontrado em {export_root}")

    package_dir = matches[0]
    zip_root.mkdir(parents=True, exist_ok=True)
    zip_path = zip_root / f"{package_dir.name}.zip"

    files_added = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fpath in sorted(package_dir.iterdir()):
            if fpath.is_file():
                zf.write(fpath, arcname=fpath.name)
                files_added += 1

    size = zip_path.stat().st_size

    return ZipResult(
        package_id=package_dir.name,
        zip_path=str(zip_path),
        files_zipped=files_added,
        size_bytes=size,
    )
