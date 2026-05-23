"""Scanner — Varredura local de arquivos de vídeo.

Dedup via fingerprint (path + size + mtime).
Read-only — nunca modifica os arquivos escaneados.
"""

import os
import time
import uuid
from datetime import datetime, timezone

from .models import VideoAsset, _make_fingerprint
from .registry import Registry

KNOWN_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".webm"}
IGNORE_DIRS = {"node_modules", ".venv", ".git", "__pycache__", ".next", "dist", "build"}
SCAN_ROOTS = [
    os.path.expanduser("~/Videos"),
    os.path.expanduser("~/Downloads"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "inbox", "videos"),
]
MAX_DEPTH = 2
MAX_FILES = 500
SCAN_TIMEOUT_S = 30


class Scanner:
    """Scanner local de arquivos de vídeo."""

    def __init__(self, registry: Registry | None = None):
        self.registry = registry or Registry()

    def scan(
        self,
        roots: list[str] | None = None,
        dry_run: bool = True,
        max_depth: int = MAX_DEPTH,
        max_files: int = MAX_FILES,
    ) -> dict[str, object]:
        """
        Varre diretórios em busca de arquivos de vídeo.

        Args:
            roots: Lista de diretórios para varrer (default: ~/Videos, ~/Downloads)
            dry_run: Se True, não importa — só reporta o que encontraria
            max_depth: Profundidade máxima de subdiretórios
            max_files: Limite de arquivos a processar

        Returns:
            dict com found, imported, skipped, errors, dry_run
        """
        roots = roots or SCAN_ROOTS
        deadline = time.time() + SCAN_TIMEOUT_S

        # Fingerprints existentes (para dedup)
        existing_fingerprints = set()
        if not dry_run:
            existing_fingerprints = {
                a.fingerprint for a in self.registry.list_all()
            }

        found_files = []
        for root in roots:
            if time.time() > deadline:
                break
            if not os.path.isdir(root):
                continue
            self._walk(root, 0, max_depth, max_files, deadline, found_files)

        timed_out = time.time() > deadline
        found = len(found_files)
        imported = 0
        skipped = 0
        errors = []

        if not dry_run:
            for file_path, size, mtime in found_files:
                if imported + skipped >= max_files:
                    break
                ext = os.path.splitext(file_path)[1].lower()
                fingerprint = _make_fingerprint(
                    file_path, size,
                    datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                )
                if fingerprint in existing_fingerprints:
                    skipped += 1
                    continue

                try:
                    asset = VideoAsset.new(
                        asset_id=uuid.uuid4().hex[:12],
                        source_type="local",
                        source_path=file_path,
                        file_name=os.path.basename(file_path),
                        extension=ext,
                        size_bytes=size,
                        modified_at=datetime.fromtimestamp(
                            mtime, tz=timezone.utc
                        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    )
                    self.registry.add(asset)
                    imported += 1
                except Exception as e:
                    errors.append(f"{file_path}: {e}")

        return {
            "found": found,
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
            "dry_run": dry_run,
            "timed_out": timed_out,
            "roots": roots,
        }

    def _walk(
        self,
        directory: str,
        depth: int,
        max_depth: int,
        max_files: int,
        deadline: float,
        results: list[tuple[str, int, float]],
    ) -> None:
        if depth > max_depth or len(results) >= max_files:
            return
        if time.time() > deadline:
            return
        try:
            for entry in os.scandir(directory):
                if len(results) >= max_files or time.time() > deadline:
                    return
                if entry.is_dir(follow_symlinks=False):
                    if entry.name not in IGNORE_DIRS:
                        self._walk(entry.path, depth + 1, max_depth,
                                   max_files, deadline, results)
                elif entry.is_file(follow_symlinks=False):
                    ext = os.path.splitext(entry.name)[1].lower()
                    if ext in KNOWN_EXTENSIONS and entry.stat().st_size > 0:
                        results.append((
                            entry.path,
                            entry.stat().st_size,
                            entry.stat().st_mtime,
                        ))
        except (OSError, PermissionError):
            pass
