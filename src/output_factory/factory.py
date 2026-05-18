"""OutputFactory — orchestrates manifest, index, checksums, zip, report."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .checksums import ChecksumGenerator
from .indexer import FileIndexer
from .manifest import ManifestGenerator
from .validator import PackageValidator
from .zipper import PackageZipper


class OutputFactory:
    """Orchestrate the full output-factory pipeline for a mission directory."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    def run(self, mission_dir: Path) -> dict:
        """Generate all standardized outputs for *mission_dir*.

        When dry_run=True no files are written; the result dict still contains
        the generated content so callers can inspect it.

        Returns:
            {
                "mission_id": str,
                "dry_run": bool,
                "outputs_written": [str, ...],
                "manifest": dict,
                "checksums": dict,
                "files_index": str,
                "package_report": str,
                "zip_path": str | None,
                "validation": dict,
            }
        """
        mission_dir = Path(mission_dir)
        exports_dir = mission_dir / "06_exports"

        # --- Generate content ---
        manifest = ManifestGenerator().generate(mission_dir)
        files_index = FileIndexer().generate_index(mission_dir)

        # Checksums before zip (zip itself excluded naturally)
        checksums = ChecksumGenerator().generate(mission_dir)

        # --- Package report ---
        package_report = self._build_report(mission_dir, manifest, checksums)

        outputs_written: list[str] = []

        if not self.dry_run:
            exports_dir.mkdir(parents=True, exist_ok=True)

            manifest_path = exports_dir / "outputs_manifest.json"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            outputs_written.append("06_exports/outputs_manifest.json")

            index_path = exports_dir / "files_index.md"
            index_path.write_text(files_index, encoding="utf-8")
            outputs_written.append("06_exports/files_index.md")

            checksums_path = exports_dir / "checksums.json"
            checksums_path.write_text(
                json.dumps(checksums, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            outputs_written.append("06_exports/checksums.json")

            report_path = exports_dir / "package_report.md"
            report_path.write_text(package_report, encoding="utf-8")
            outputs_written.append("06_exports/package_report.md")

            # Zip AFTER writing text files (includes them in archive)
            zip_path = PackageZipper().zip(mission_dir)
            outputs_written.append("06_exports/final_package.zip")
        else:
            zip_path = None

        # Validate
        validation = PackageValidator().validate(mission_dir)

        return {
            "mission_id": mission_dir.name,
            "dry_run": self.dry_run,
            "outputs_written": outputs_written,
            "manifest": manifest,
            "checksums": checksums,
            "files_index": files_index,
            "package_report": package_report,
            "zip_path": str(zip_path) if zip_path else None,
            "validation": validation,
        }

    @staticmethod
    def _build_report(mission_dir: Path, manifest: dict, checksums: dict) -> str:
        lines = [
            f"# Package Report — {mission_dir.name}",
            "",
            f"Generated: {datetime.now(tz=timezone.utc).isoformat()}",
            "",
            "## Summary",
            "",
            f"- **Total files:** {manifest['total_files']}",
            f"- **Total size:** {manifest['total_bytes']:,} bytes",
            f"- **Files with checksums:** {len(checksums)}",
            "",
            "## File List",
            "",
        ]
        for f in manifest["files"]:
            sha = checksums.get(f["path"], "n/a")[:12]
            lines.append(f"- `{f['path']}` — {f['size_bytes']:,} B — sha256: `{sha}...`")
        lines.append("")
        return "\n".join(lines)
