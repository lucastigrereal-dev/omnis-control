"""Asset Inbox Scanner — read-only directory scan.

NUNCA move, copia, apaga ou modifica arquivos.
NUNCA importa para registry.
NUNCA associa a queue.
NUNCA chama rede.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.asset_inbox.models import (
    AssetInboxScanResult,
    AssetInboxItem,
    SUPPORTED_EXTENSIONS,
    DEFAULT_SCAN_LIMIT,
    DEFAULT_MAX_SIZE_BYTES,
    DEFAULT_EXCLUDE_DIRS,
    STATUS_CANDIDATE,
    STATUS_IGNORED,
    STATUS_TOO_LARGE,
    STATUS_MISSING,
    STATUS_BLOCKED,
)
from src.asset_inbox.fingerprint import compute_fingerprint
from src.asset_inbox.metadata import get_media_type, is_supported, get_file_size
from src.asset_inbox.errors import AssetInboxScanError, PathTraversalError


def scan(
    root: Path,
    limit: int = DEFAULT_SCAN_LIMIT,
    exclude: Optional[set[str]] = None,
    max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES,
) -> AssetInboxScanResult:
    """Scan root path read-only and return AssetInboxScanResult.

    Args:
        root: Directory or single file to scan.
        limit: Max number of files to process (default 500).
        exclude: Set of directory names to skip (merged with DEFAULT_EXCLUDE_DIRS).
        max_size_bytes: Files larger than this are marked too_large (default 2 GB).

    Raises:
        AssetInboxScanError: root does not exist or is not accessible.
        PathTraversalError: root contains path traversal sequence.
    """
    _check_traversal(root)

    if not root.exists():
        raise AssetInboxScanError(f"Path nao existe: {root}")

    exclude_dirs = DEFAULT_EXCLUDE_DIRS | (exclude or set())
    result = AssetInboxScanResult.new(str(root.resolve()))

    if root.is_file():
        _process_file(root, result, max_size_bytes)
        result.total_seen = 1
        return result

    _walk(root, result, exclude_dirs, limit, max_size_bytes)
    return result


def _check_traversal(path: Path) -> None:
    path_str = str(path)
    if ".." in path.parts or "%2e%2e" in path_str.lower() or "../" in path_str:
        raise PathTraversalError(f"Path traversal detectado: {path}")


def _walk(
    root: Path,
    result: AssetInboxScanResult,
    exclude_dirs: set[str],
    limit: int,
    max_size_bytes: int,
) -> None:
    seen = 0
    try:
        for entry in _iter_files(root, exclude_dirs):
            if seen >= limit:
                result.warnings.append(
                    f"Limite de {limit} arquivos atingido — scan interrompido."
                )
                break
            result.total_seen += 1
            seen += 1
            _process_file(entry, result, max_size_bytes)
    except PermissionError as exc:
        result.warnings.append(f"Permissao negada ao percorrer: {exc}")


def _iter_files(root: Path, exclude_dirs: set[str]):
    """Yield regular files recursively, skipping excluded dirs and symlinks."""
    try:
        entries = sorted(root.iterdir())
    except PermissionError:
        return

    for entry in entries:
        if entry.name in exclude_dirs:
            continue
        if entry.is_symlink():
            continue  # never follow symlinks
        if entry.is_dir():
            yield from _iter_files(entry, exclude_dirs)
        elif entry.is_file():
            yield entry


def _process_file(
    path: Path,
    result: AssetInboxScanResult,
    max_size_bytes: int,
) -> None:
    warnings: list[str] = []
    ext = path.suffix.lower()

    if not is_supported(ext):
        item = AssetInboxItem(
            path=str(path),
            file_name=path.name,
            extension=ext,
            size_bytes=0,
            media_type="unknown",
            fingerprint="",
            exists_on_disk=path.exists(),
            status=STATUS_IGNORED,
        )
        result.items.append(item)
        result.total_ignored += 1
        return

    if not path.exists():
        item = AssetInboxItem(
            path=str(path),
            file_name=path.name,
            extension=ext,
            size_bytes=0,
            media_type=get_media_type(ext),
            fingerprint="",
            exists_on_disk=False,
            status=STATUS_MISSING,
            warnings=["file disappeared during scan"],
        )
        result.items.append(item)
        result.total_supported += 1
        return

    size_bytes, size_err = get_file_size(path)
    if size_err:
        warnings.append(size_err)

    if size_bytes > max_size_bytes:
        item = AssetInboxItem(
            path=str(path),
            file_name=path.name,
            extension=ext,
            size_bytes=size_bytes,
            media_type=get_media_type(ext),
            fingerprint="",
            exists_on_disk=True,
            status=STATUS_TOO_LARGE,
            warnings=[f"size {size_bytes} exceeds limit {max_size_bytes}"],
        )
        result.items.append(item)
        result.total_supported += 1
        result.total_too_large += 1
        result.total_size_bytes += size_bytes
        return

    fp, fp_err = compute_fingerprint(path)
    if fp_err:
        warnings.append(f"fingerprint: {fp_err}")

    item = AssetInboxItem(
        path=str(path),
        file_name=path.name,
        extension=ext,
        size_bytes=size_bytes,
        media_type=get_media_type(ext),
        fingerprint=fp,
        exists_on_disk=True,
        status=STATUS_CANDIDATE,
        warnings=warnings,
    )
    result.items.append(item)
    result.total_supported += 1
    result.total_size_bytes += size_bytes
