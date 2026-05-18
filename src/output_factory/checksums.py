"""ChecksumGenerator — generates checksums.json with SHA-256 per file."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path


class ChecksumGenerator:
    """Compute SHA-256 checksums for all files in a mission directory."""

    def generate(self, mission_dir: Path) -> dict:
        """Return dict mapping relative path → sha256 hex string."""
        mission_dir = Path(mission_dir)
        checksums: dict[str, str] = {}

        for root, _dirs, file_names in os.walk(mission_dir):
            root_path = Path(root)
            for name in sorted(file_names):
                abs_path = root_path / name
                rel = abs_path.relative_to(mission_dir).as_posix()
                checksums[rel] = self._sha256(abs_path)

        return checksums

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
