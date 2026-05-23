"""Tests for output versioning engine."""

import tempfile
from pathlib import Path

import pytest

from src.output_versioning.versioning import OutputVersioner


@pytest.fixture
def versioner():
    with tempfile.TemporaryDirectory() as tmp:
        yield OutputVersioner(store_dir=Path(tmp))


@pytest.fixture
def sample_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        f1 = root / "carrossel.md"
        f1.write_text("# Carrossel v1\n\n10 slides sobre hoteis.", encoding="utf-8")
        f2 = root / "caption.txt"
        f2.write_text("Descubra os melhores hoteis do nordeste!", encoding="utf-8")
        yield [str(f1), str(f2)]


class TestOutputVersionerSnapshot:
    def test_first_snapshot(self, versioner, sample_files):
        vo = versioner.snapshot("campanha_01", sample_files, "Initial version")
        assert vo.output_id == "campanha_01"
        assert vo.current_version == 1
        assert vo.version_count == 1
        assert vo.latest.version == 1

    def test_multiple_versions(self, versioner, sample_files):
        versioner.snapshot("campanha_01", sample_files, "v1")
        versioner.snapshot("campanha_01", sample_files[:1], "v2 - only carrossel")
        vo = versioner.get("campanha_01")
        assert vo.current_version == 2
        assert vo.version_count == 2

    def test_version_files_copied(self, versioner, sample_files):
        versioner.snapshot("campanha_01", sample_files, "v1")
        vo = versioner.get("campanha_01")
        vdir = versioner.store_dir / "campanha_01" / "v1"
        assert vdir.is_dir()
        files = list(vdir.iterdir())
        assert len(files) == 2

    def test_different_hashes_for_different_content(self, versioner, sample_files):
        versioner.snapshot("out1", sample_files, "v1")
        # Modify a file
        Path(sample_files[0]).write_text("# Modified content", encoding="utf-8")
        versioner.snapshot("out1", sample_files, "v2")
        vo = versioner.get("out1")
        assert vo.versions[0].hash != vo.versions[1].hash

    def test_same_content_same_hash(self, versioner, sample_files):
        versioner.snapshot("out1", sample_files, "v1")
        versioner.snapshot("out1", sample_files, "v2 - unchanged")
        vo = versioner.get("out1")
        assert vo.versions[0].hash == vo.versions[1].hash


class TestOutputVersionerDiff:
    def test_diff_identical(self, versioner, sample_files):
        versioner.snapshot("out1", sample_files, "v1")
        versioner.snapshot("out1", sample_files, "v2")
        d = versioner.diff("out1", 1, 2)
        assert d.is_identical

    def test_diff_after_change(self, versioner, sample_files):
        versioner.snapshot("out1", sample_files, "v1")
        Path(sample_files[0]).write_text("# Much bigger content here now", encoding="utf-8")
        versioner.snapshot("out1", sample_files, "v2")
        d = versioner.diff("out1", 1, 2)
        assert not d.is_identical
        assert d.size_delta != 0

    def test_diff_nonexistent_output(self, versioner):
        with pytest.raises(FileNotFoundError):
            versioner.diff("nonexistent", 1, 2)


class TestOutputVersionerRollback:
    def test_rollback_creates_new_version(self, versioner, sample_files):
        versioner.snapshot("out1", sample_files, "v1")
        Path(sample_files[0]).write_text("# v2 content", encoding="utf-8")
        versioner.snapshot("out1", sample_files, "v2")
        Path(sample_files[0]).write_text("# v3 content", encoding="utf-8")
        versioner.snapshot("out1", sample_files, "v3")

        vo = versioner.rollback("out1", 1)
        assert vo.current_version == 4  # rolled back from v3 → creates v4 with v1 content
        assert vo.status == "rolled_back"
        assert vo.latest.changelog == "Rollback to v1"


class TestOutputVersionerQuery:
    def test_get_missing(self, versioner):
        assert versioner.get("nonexistent") is None

    def test_list_all(self, versioner, sample_files):
        versioner.snapshot("out1", sample_files, "v1")
        versioner.snapshot("out2", sample_files, "v1")
        all_outputs = versioner.list_all()
        assert len(all_outputs) == 2

    def test_changelog(self, versioner, sample_files):
        versioner.snapshot("out1", sample_files, "Initial version")
        versioner.snapshot("out1", sample_files, "Added slide")
        cl = versioner.changelog("out1")
        assert len(cl.entries) == 2
        assert cl.entries[0]["message"] == "Initial version"
        assert cl.entries[1]["message"] == "Added slide"

    def test_changelog_empty_for_missing(self, versioner):
        cl = versioner.changelog("nonexistent")
        assert len(cl.entries) == 0
