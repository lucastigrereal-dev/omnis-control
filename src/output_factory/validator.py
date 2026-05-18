"""PackageValidator — checks required files exist in a mission directory."""
from __future__ import annotations

from pathlib import Path

REQUIRED_FILES = [
    "06_exports/outputs_manifest.json",
    "06_exports/files_index.md",
    "06_exports/checksums.json",
    "06_exports/final_package.zip",
    "06_exports/package_report.md",
]


class PackageValidator:
    """Validate that a mission directory contains all required output files."""

    def validate(self, mission_dir: Path) -> dict:
        """Check for required files.

        Returns:
            {
                "valid": bool,
                "present": [paths],
                "missing": [paths],
            }
        """
        mission_dir = Path(mission_dir)
        present = []
        missing = []

        for rel in REQUIRED_FILES:
            p = mission_dir / rel
            if p.exists():
                present.append(rel)
            else:
                missing.append(rel)

        return {
            "valid": len(missing) == 0,
            "present": present,
            "missing": missing,
        }
