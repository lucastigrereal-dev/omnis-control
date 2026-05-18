"""App Packager — writes generated files to disk and creates ZIP."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .models import AppSpec, GeneratedFile

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EXPORTS_DIR = PROJECT_ROOT / "exports" / "app_factory"


class AppPackager:
    """Writes generated app files to disk and produces ZIP package."""

    def __init__(self, output_root: Path | None = None):
        self.output_root = Path(output_root) if output_root else EXPORTS_DIR

    def write_and_package(
        self,
        spec: AppSpec,
        files: list[GeneratedFile],
        dry_run: bool = True,
    ) -> dict:
        """Write all files and create ZIP. Returns manifest."""
        app_dir = self.output_root / spec.app_name
        package_id = f"{spec.app_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        manifest = {
            "package_id": package_id,
            "app_name": spec.app_name,
            "app_type": spec.app_type.value,
            "description": spec.description,
            "files": [f.relative_path for f in files],
            "file_count": len(files),
            "dry_run": dry_run,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

        if dry_run:
            manifest_path = self.output_root / f"{package_id}_manifest.json"
            self.output_root.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            manifest["manifest_path"] = str(manifest_path)
            return manifest

        # Real write
        app_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for gf in files:
            file_path = app_dir / gf.relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(gf.content, encoding="utf-8")
            written.append(str(file_path.relative_to(self.output_root)))

        # Create ZIP
        zip_path = self.output_root / f"{package_id}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for gf in files:
                file_path = app_dir / gf.relative_path
                zf.write(file_path, f"{spec.app_name}/{gf.relative_path}")

        manifest["zip_path"] = str(zip_path)
        manifest["written_files"] = written
        manifest["zip_size_bytes"] = zip_path.stat().st_size

        # Write manifest
        manifest_path = self.output_root / f"{package_id}_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        manifest["manifest_path"] = str(manifest_path)

        return manifest
