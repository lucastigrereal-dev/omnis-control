"""PackageZipper — creates final_package.zip from a mission directory."""
from __future__ import annotations

import os
import zipfile
from pathlib import Path


class PackageZipper:
    """Zip entire mission directory into a self-contained archive."""

    def zip(self, mission_dir: Path, output_path: Path | None = None) -> Path:
        """Create zip archive of mission_dir.

        Args:
            mission_dir: root of the mission.
            output_path: destination .zip file. Defaults to
                         mission_dir/06_exports/final_package.zip.

        Returns:
            Path to the created zip file.
        """
        mission_dir = Path(mission_dir)
        if output_path is None:
            output_path = mission_dir / "06_exports" / "final_package.zip"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _dirs, file_names in os.walk(mission_dir):
                root_path = Path(root)
                for name in sorted(file_names):
                    abs_path = root_path / name
                    # Skip the zip itself to avoid recursion
                    if abs_path == output_path:
                        continue
                    arcname = abs_path.relative_to(mission_dir).as_posix()
                    zf.write(abs_path, arcname)

        return output_path
