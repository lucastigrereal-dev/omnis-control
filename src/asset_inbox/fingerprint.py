"""Fingerprint — SHA256 in 8KB chunks. Never loads full file into memory."""
from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK_SIZE = 8 * 1024  # 8 KB


def compute_fingerprint(path: Path) -> tuple[str, str]:
    """Compute SHA256 fingerprint reading file in 8KB chunks.

    Returns (fingerprint_hex, error_msg).
    error_msg is "" on success, non-empty string on failure.
    Never raises — errors are returned as the second tuple element.
    """
    if not path.exists():
        return "", f"file not found: {path.name}"
    if not path.is_file():
        return "", f"not a file: {path.name}"

    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest(), ""
    except PermissionError:
        return "", f"permission denied: {path.name}"
    except OSError as exc:
        return "", f"read error: {exc}"
