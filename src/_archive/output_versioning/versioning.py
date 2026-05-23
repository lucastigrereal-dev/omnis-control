"""Output Versioner — snapshot, diff, and rollback output files."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import VersionedOutput, VersionEntry, Changelog, DiffResult

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VERSIONS_DIR = PROJECT_ROOT / "data" / "output_versions"


class OutputVersioner:
    """Track versions of output files with snapshot, diff, and rollback."""

    def __init__(self, store_dir: Optional[Path] = None):
        self.store_dir = Path(store_dir) if store_dir else VERSIONS_DIR
        self.store_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------
    # Snapshot / Version creation
    # -----------------------------------------------------------

    def snapshot(self, output_id: str, file_paths: list[str], changelog_msg: str = "") -> VersionedOutput:
        """Create a new version snapshot of one or more output files."""
        existing = self._load(output_id)
        if existing:
            entry = existing
            entry.current_version += 1
        else:
            entry = VersionedOutput(output_id=output_id, name=output_id)

        version_entry = VersionEntry(
            version=entry.current_version,
            path=",".join(file_paths),
            size=sum(self._file_size(Path(p)) for p in file_paths),
            hash=self._combined_hash(file_paths),
            changelog=changelog_msg,
        )

        # Copy files to versioned storage
        version_dir = self.store_dir / output_id / f"v{entry.current_version}"
        version_dir.mkdir(parents=True, exist_ok=True)
        for fp in file_paths:
            src = Path(fp)
            if src.is_file():
                shutil.copy2(src, version_dir / src.name)

        entry.versions.append(version_entry)
        entry.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self._save(entry)
        return entry

    # -----------------------------------------------------------
    # Diff
    # -----------------------------------------------------------

    def diff(self, output_id: str, version_a: int, version_b: int) -> DiffResult:
        """Compare two versions of an output."""
        entry = self._load(output_id)
        if not entry:
            raise FileNotFoundError(f"Output not found: {output_id}")

        v_a = self._find_version(entry, version_a)
        v_b = self._find_version(entry, version_b)

        result = DiffResult(
            output_id=output_id,
            version_a=version_a,
            version_b=version_b,
            same_hash=v_a.hash == v_b.hash,
            size_delta=v_b.size - v_a.size,
        )

        if result.same_hash:
            result.summary = "Versions are identical (same hash)"
        else:
            result.summary = f"Size: {v_a.size} → {v_b.size} bytes (delta: {result.size_delta:+d})"

        return result

    # -----------------------------------------------------------
    # Rollback
    # -----------------------------------------------------------

    def rollback(self, output_id: str, target_version: int) -> VersionedOutput:
        """Rollback to a previous version (creates a new version with old content)."""
        entry = self._load(output_id)
        if not entry:
            raise FileNotFoundError(f"Output not found: {output_id}")

        target = self._find_version(entry, target_version)
        if not target:
            raise ValueError(f"Version {target_version} not found for {output_id}")

        # Restore files from the versioned storage
        version_dir = self.store_dir / output_id / f"v{target_version}"
        if not version_dir.is_dir():
            raise FileNotFoundError(f"Version data not found: {version_dir}")

        new_version = entry.current_version + 1
        new_version_dir = self.store_dir / output_id / f"v{new_version}"
        new_version_dir.mkdir(parents=True, exist_ok=True)

        # Copy files from target version
        restored_files = []
        for f in version_dir.iterdir():
            if f.is_file():
                shutil.copy2(f, new_version_dir / f.name)
                restored_files.append(str(new_version_dir / f.name))

        # Create rollback version entry
        v_entry = VersionEntry(
            version=new_version,
            path=",".join(restored_files),
            size=target.size,
            hash=target.hash,
            changelog=f"Rollback to v{target_version}",
            tags=["rollback", f"from_v{target_version}"],
        )

        entry.current_version = new_version
        entry.versions.append(v_entry)
        entry.status = "rolled_back"
        entry.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self._save(entry)
        return entry

    # -----------------------------------------------------------
    # Query
    # -----------------------------------------------------------

    def get(self, output_id: str) -> Optional[VersionedOutput]:
        return self._load(output_id)

    def list_all(self) -> list[VersionedOutput]:
        results = []
        for d in self.store_dir.iterdir():
            if d.is_dir():
                entry = self._load(d.name)
                if entry:
                    results.append(entry)
        return results

    def changelog(self, output_id: str) -> Changelog:
        entry = self._load(output_id)
        cl = Changelog(output_id=output_id)
        if entry:
            for v in entry.versions:
                if v.changelog:
                    cl.add(v.version, v.changelog)
        return cl

    # -----------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------

    def _load(self, output_id: str) -> Optional[VersionedOutput]:
        meta_file = self.store_dir / output_id / "metadata.json"
        if not meta_file.is_file():
            return None
        data = json.loads(meta_file.read_text(encoding="utf-8"))
        return VersionedOutput.from_dict(data)

    def _save(self, entry: VersionedOutput) -> None:
        entry_dir = self.store_dir / entry.output_id
        entry_dir.mkdir(parents=True, exist_ok=True)
        (entry_dir / "metadata.json").write_text(
            json.dumps(entry.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _find_version(self, entry: VersionedOutput, version: int) -> Optional[VersionEntry]:
        for v in entry.versions:
            if v.version == version:
                return v
        return None

    def _file_size(self, path: Path) -> int:
        return path.stat().st_size if path.is_file() else 0

    def _combined_hash(self, file_paths: list[str]) -> str:
        h = hashlib.sha256()
        for fp in sorted(file_paths):
            p = Path(fp)
            if p.is_file():
                h.update(p.read_bytes())
        return h.hexdigest()[:16]
