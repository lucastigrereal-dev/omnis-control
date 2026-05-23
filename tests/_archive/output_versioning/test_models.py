"""Tests for output versioning models."""

from src.output_versioning.models import (
    VersionEntry,
    VersionedOutput,
    DiffResult,
    Changelog,
)


class TestVersionEntry:
    def test_construction(self):
        v = VersionEntry(version=1, path="output/carrossel.md", size=1024, hash="abc123")
        assert v.version == 1
        assert v.size == 1024
        assert v.hash == "abc123"

    def test_with_changelog(self):
        v = VersionEntry(version=2, path="output/v2.md", size=2048, hash="def456",
                         changelog="Adicionado slide extra", tags=["carrossel"])
        assert v.changelog == "Adicionado slide extra"
        assert v.tags == ["carrossel"]

    def test_to_dict_roundtrip(self):
        v = VersionEntry(version=3, path="a,b,c", size=100, hash="hhh",
                         changelog="v3", tags=["final"])
        d = v.to_dict()
        restored = VersionEntry.from_dict(d)
        assert restored.version == 3
        assert restored.hash == "hhh"


class TestVersionedOutput:
    def test_empty(self):
        vo = VersionedOutput(output_id="campanha_01", name="Campanha Nordeste")
        assert vo.current_version == 1
        assert vo.version_count == 0
        assert vo.latest is None

    def test_with_versions(self):
        vo = VersionedOutput(output_id="c1", name="Campanha")
        vo.versions = [
            VersionEntry(version=1, path="v1.md", size=100, hash="aaa"),
            VersionEntry(version=2, path="v2.md", size=200, hash="bbb"),
        ]
        assert vo.version_count == 2
        assert vo.latest.version == 2

    def test_to_dict_roundtrip(self):
        vo = VersionedOutput(output_id="c1", name="Campanha", current_version=3)
        vo.versions = [VersionEntry(version=1, path="v1.md", size=100, hash="aaa")]
        d = vo.to_dict()
        restored = VersionedOutput.from_dict(d)
        assert restored.output_id == "c1"
        assert restored.current_version == 3
        assert restored.version_count == 1
        assert restored.latest.hash == "aaa"


class TestDiffResult:
    def test_identical(self):
        d = DiffResult(output_id="o1", version_a=1, version_b=2, same_hash=True, size_delta=0)
        assert d.is_identical

    def test_different(self):
        d = DiffResult(output_id="o1", version_a=1, version_b=2, same_hash=False, size_delta=100)
        assert not d.is_identical


class TestChangelog:
    def test_add_entries(self):
        cl = Changelog(output_id="o1")
        cl.add(1, "Initial version")
        cl.add(2, "Added slide 10")
        assert len(cl.entries) == 2
        assert cl.entries[0]["version"] == 1
        assert cl.entries[1]["message"] == "Added slide 10"
