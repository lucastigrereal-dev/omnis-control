"""Asset Importer — copies a supported file to local storage safely.

NUNCA move original.
NUNCA apaga original.
NUNCA modifica original.
NUNCA faz assign.
NUNCA chama rede.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.asset_inbox.models import (
    ImportedAsset,
    AssetImportResult,
    SUPPORTED_EXTENSIONS,
    DEFAULT_MAX_SIZE_BYTES,
    IMPORT_STATUS_IMPORTED,
    IMPORT_STATUS_DUPLICATE,
    IMPORT_STATUS_MISSING_SOURCE,
    IMPORT_STATUS_UNSUPPORTED,
    IMPORT_STATUS_TOO_LARGE,
    IMPORT_STATUS_FP_MISMATCH,
    IMPORT_STATUS_FAILED,
)
from src.asset_inbox.fingerprint import compute_fingerprint
from src.asset_inbox.metadata import get_media_type
from src.asset_inbox.storage import (
    DEFAULT_STORAGE_ROOT,
    asset_exists,
    store_copy,
    write_import_manifest,
)
from src.asset_inbox.registry import AssetInboxRegistry, DEFAULT_REGISTRY_PATH


def import_asset(
    source_path: str,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES,
) -> AssetImportResult:
    """Import a copy of source file to local storage. Never moves/modifies original.

    Returns AssetImportResult with status: imported | duplicate | missing_source |
    unsupported_extension | too_large | fingerprint_mismatch | failed
    """
    registry = AssetInboxRegistry(registry_path)
    source = Path(source_path)

    if not source.exists():
        return AssetImportResult(
            asset=None,
            status=IMPORT_STATUS_MISSING_SOURCE,
            blockers=[f"Source not found: {source_path}"],
        )

    if not source.is_file():
        return AssetImportResult(
            asset=None,
            status=IMPORT_STATUS_BLOCKED,
            blockers=[f"Not a file: {source_path}"],
        )

    ext = source.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return AssetImportResult(
            asset=None,
            status=IMPORT_STATUS_UNSUPPORTED,
            blockers=[f"Extension not supported: {ext}"],
        )

    try:
        size_bytes = source.stat().st_size
    except OSError as exc:
        return AssetImportResult(
            asset=None,
            status=IMPORT_STATUS_FAILED,
            blockers=[f"Cannot stat file: {exc}"],
        )

    if size_bytes > max_size_bytes:
        return AssetImportResult(
            asset=None,
            status=IMPORT_STATUS_TOO_LARGE,
            blockers=[f"File size {size_bytes} exceeds limit {max_size_bytes}"],
        )

    src_fp, fp_err = compute_fingerprint(source)
    if fp_err:
        return AssetImportResult(
            asset=None,
            status=IMPORT_STATUS_FAILED,
            blockers=[f"Cannot fingerprint source: {fp_err}"],
        )

    # Duplicate check by fingerprint
    existing = registry.find_by_fingerprint(src_fp)
    if existing is not None:
        return AssetImportResult(
            asset=existing,
            status=IMPORT_STATUS_DUPLICATE,
            warnings=[f"Asset already imported as {existing.asset_id}"],
        )

    asset_id = f"ai_{src_fp[:16]}"

    # Copy to storage
    try:
        stored_path = store_copy(source, asset_id, storage_root)
    except OSError as exc:
        return AssetImportResult(
            asset=None,
            status=IMPORT_STATUS_FAILED,
            blockers=[f"Copy failed: {exc}"],
        )

    # Verify fingerprint of copy
    stored_fp, stored_fp_err = compute_fingerprint(stored_path)
    fp_match = (stored_fp == src_fp) and not stored_fp_err

    if not fp_match:
        return AssetImportResult(
            asset=None,
            status=IMPORT_STATUS_FP_MISMATCH,
            blockers=[f"Fingerprint mismatch after copy: {stored_fp_err}"],
        )

    asset = ImportedAsset(
        asset_id=asset_id,
        source_path=str(source.resolve()),
        stored_path=str(stored_path),
        file_name=source.name,
        extension=ext,
        media_type=get_media_type(ext),
        size_bytes=size_bytes,
        source_fingerprint=src_fp,
        stored_fingerprint=stored_fp,
        fingerprint_match=fp_match,
        status=IMPORT_STATUS_IMPORTED,
    )

    write_import_manifest(asset_id, asset.to_dict(), storage_root)
    registry.add(asset)

    return AssetImportResult(asset=asset, status=IMPORT_STATUS_IMPORTED)
