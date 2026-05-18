"""FileIndexer — generates files_index.md for a mission dir."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path


class FileIndexer:
    """Generate a human-readable Markdown file listing."""

    def generate_index(self, mission_dir: Path) -> str:
        """Return a Markdown string listing all files under mission_dir."""
        mission_dir = Path(mission_dir)
        lines = [
            f"# File Index — {mission_dir.name}",
            f"",
            f"Generated: {datetime.now(tz=timezone.utc).isoformat()}",
            f"",
            f"## Files",
            f"",
        ]

        for root, _dirs, file_names in os.walk(mission_dir):
            root_path = Path(root)
            for name in sorted(file_names):
                abs_path = root_path / name
                rel = abs_path.relative_to(mission_dir).as_posix()
                size = abs_path.stat().st_size
                lines.append(f"- `{rel}` ({size:,} bytes)")

        lines.append("")
        return "\n".join(lines)
