"""Metadata extraction — read-only stat() only. Never opens file content."""
from __future__ import annotations

from pathlib import Path

from src.asset_inbox.models import SUPPORTED_EXTENSIONS


def get_media_type(extension: str) -> str:
    """Return 'image', 'video', or 'unknown' for a given extension."""
    return SUPPORTED_EXTENSIONS.get(extension.lower(), "unknown")


def is_supported(extension: str) -> bool:
    """Return True if the extension is in the supported set."""
    return extension.lower() in SUPPORTED_EXTENSIONS


def get_file_size(path: Path) -> tuple[int, str]:
    """Return (size_bytes, error_msg). Uses stat(), never opens the file.

    Returns (0, error_msg) on failure.
    Never raises.
    """
    try:
        return path.stat().st_size, ""
    except FileNotFoundError:
        return 0, f"file not found: {path.name}"
    except PermissionError:
        return 0, f"permission denied: {path.name}"
    except OSError as exc:
        return 0, f"stat error: {exc}"
