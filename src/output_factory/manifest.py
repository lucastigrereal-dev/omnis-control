"""ManifestGenerator — generates outputs_manifest.json for a mission dir."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


class ManifestGenerator:
    """Generate a structured manifest of all output files in a mission."""

    def generate(self, mission_dir: Path) -> dict:
        """Walk mission_dir and return manifest dict.

        Returns:
            {
                "mission_id": str,
                "generated_at": ISO-8601,
                "files": [ {"path": rel, "size_bytes": int, "ext": str}, ... ],
                "total_files": int,
                "total_bytes": int,
            }
        """
        mission_dir = Path(mission_dir)
        files = []
        total_bytes = 0

        for root, _dirs, file_names in os.walk(mission_dir):
            root_path = Path(root)
            for name in sorted(file_names):
                abs_path = root_path / name
                rel = abs_path.relative_to(mission_dir).as_posix()
                size = abs_path.stat().st_size
                total_bytes += size
                files.append(
                    {
                        "path": rel,
                        "size_bytes": size,
                        "ext": abs_path.suffix.lower(),
                    }
                )

        return {
            "mission_id": mission_dir.name,
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "files": files,
            "total_files": len(files),
            "total_bytes": total_bytes,
        }
