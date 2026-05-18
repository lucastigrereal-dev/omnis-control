"""Tests for src/output_factory — OutputFactory pipeline."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from src.output_factory.checksums import ChecksumGenerator
from src.output_factory.factory import OutputFactory
from src.output_factory.indexer import FileIndexer
from src.output_factory.manifest import ManifestGenerator
from src.output_factory.validator import PackageValidator
from src.output_factory.zipper import PackageZipper


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mission_dir(tmp_path: Path) -> Path:
    """Create a minimal fake mission directory."""
    m = tmp_path / "MIS-TEST-001"
    (m / "05_outputs").mkdir(parents=True)
    (m / "06_exports").mkdir(parents=True)
    (m / "05_outputs" / "report.md").write_text("# Report", encoding="utf-8")
    (m / "05_outputs" / "data.json").write_text('{"key": "value"}', encoding="utf-8")
    (m / "mission_contract.json").write_text('{"id": "MIS-TEST-001"}', encoding="utf-8")
    return m


# ---------------------------------------------------------------------------
# 1. ManifestGenerator — correct file list
# ---------------------------------------------------------------------------


def test_manifest_generates_correct_file_list(mission_dir: Path) -> None:
    result = ManifestGenerator().generate(mission_dir)

    assert result["mission_id"] == "MIS-TEST-001"
    assert result["total_files"] == 3
    paths = [f["path"] for f in result["files"]]
    assert "05_outputs/report.md" in paths
    assert "05_outputs/data.json" in paths
    assert "mission_contract.json" in paths


# ---------------------------------------------------------------------------
# 2. ChecksumGenerator — valid SHA-256 hashes
# ---------------------------------------------------------------------------


def test_checksums_are_valid_sha256(mission_dir: Path) -> None:
    checksums = ChecksumGenerator().generate(mission_dir)

    assert len(checksums) == 3
    for path, digest in checksums.items():
        # SHA-256 hex is exactly 64 chars
        assert len(digest) == 64, f"Bad digest for {path}: {digest!r}"
        int(digest, 16)  # must be valid hex

    # Verify one manually
    content = (mission_dir / "mission_contract.json").read_bytes()
    expected = hashlib.sha256(content).hexdigest()
    assert checksums["mission_contract.json"] == expected


# ---------------------------------------------------------------------------
# 3. PackageZipper — zip created and extractable
# ---------------------------------------------------------------------------


def test_zip_created_and_extractable(mission_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "test.zip"
    zip_path = PackageZipper().zip(mission_dir, output_path=out)

    assert zip_path.exists()
    assert zip_path.stat().st_size > 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()

    assert "05_outputs/report.md" in names
    assert "mission_contract.json" in names


# ---------------------------------------------------------------------------
# 4. FileIndexer — files_index.md contains file names
# ---------------------------------------------------------------------------


def test_files_index_contains_file_names(mission_dir: Path) -> None:
    index_md = FileIndexer().generate_index(mission_dir)

    assert "report.md" in index_md
    assert "data.json" in index_md
    assert "mission_contract.json" in index_md
    assert "MIS-TEST-001" in index_md


# ---------------------------------------------------------------------------
# 5. PackageValidator — detects missing files
# ---------------------------------------------------------------------------


def test_validator_detects_missing_files(mission_dir: Path) -> None:
    result = PackageValidator().validate(mission_dir)

    assert result["valid"] is False
    assert "06_exports/outputs_manifest.json" in result["missing"]
    assert "06_exports/final_package.zip" in result["missing"]


# ---------------------------------------------------------------------------
# 6. OutputFactory.run() — produces all expected outputs
# ---------------------------------------------------------------------------


def test_factory_run_produces_all_outputs(mission_dir: Path) -> None:
    result = OutputFactory(dry_run=False).run(mission_dir)

    assert result["dry_run"] is False
    assert result["mission_id"] == "MIS-TEST-001"

    # All five outputs written
    written = result["outputs_written"]
    assert "06_exports/outputs_manifest.json" in written
    assert "06_exports/files_index.md" in written
    assert "06_exports/checksums.json" in written
    assert "06_exports/package_report.md" in written
    assert "06_exports/final_package.zip" in written

    # Files physically exist
    exports = mission_dir / "06_exports"
    assert (exports / "outputs_manifest.json").exists()
    assert (exports / "files_index.md").exists()
    assert (exports / "checksums.json").exists()
    assert (exports / "package_report.md").exists()
    assert (exports / "final_package.zip").exists()

    # manifest is valid JSON with expected keys
    manifest_data = json.loads((exports / "outputs_manifest.json").read_text())
    assert manifest_data["mission_id"] == "MIS-TEST-001"
    assert manifest_data["total_files"] > 0

    # Validation passes after run
    assert result["validation"]["valid"] is True


# ---------------------------------------------------------------------------
# 7. OutputFactory dry_run=True — no files written
# ---------------------------------------------------------------------------


def test_factory_dry_run_writes_nothing(mission_dir: Path) -> None:
    result = OutputFactory(dry_run=True).run(mission_dir)

    assert result["dry_run"] is True
    assert result["outputs_written"] == []
    assert result["zip_path"] is None

    # Only pre-existing files exist in 06_exports
    exports = mission_dir / "06_exports"
    assert not (exports / "outputs_manifest.json").exists()
    assert not (exports / "final_package.zip").exists()
