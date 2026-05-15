"""Tests for Artifact model + ArtifactRegistry."""
from __future__ import annotations

import pytest

from src.missions.artifacts import (
    Artifact,
    ArtifactKind,
    ArtifactRegistry,
    ArtifactStatus,
    PathTraversalError,
)


class TestArtifact:
    def test_creation_defaults(self):
        a = Artifact(path="reports/test.md")
        assert a.path == "reports/test.md"
        assert a.kind == ArtifactKind.OTHER
        assert a.status == ArtifactStatus.CREATED
        assert a.sha256 == ""

    def test_compute_hash(self):
        a = Artifact(path="reports/test.md", kind=ArtifactKind.REPORT, size_bytes=100)
        h = a.compute_hash()
        assert len(h) == 64
        assert a.compute_hash() == a.compute_hash()  # deterministic

    def test_to_dict_roundtrip(self):
        a = Artifact(
            path="reports/test.md",
            kind=ArtifactKind.REPORT,
            sha256="abc123",
            size_bytes=100,
            metadata={"author": "omnis"},
        )
        d = a.to_dict()
        b = Artifact.from_dict(d)
        assert b.path == a.path
        assert b.kind == a.kind
        assert b.sha256 == a.sha256
        assert b.metadata == a.metadata

    def test_frozen(self):
        a = Artifact(path="reports/test.md")
        with pytest.raises(Exception):
            a.path = "other.md"


class TestArtifactRegistry:
    def test_register_and_list(self, tmp_path):
        mission_dir = tmp_path / "mission-test"
        mission_dir.mkdir()
        reg = ArtifactRegistry(str(mission_dir))

        a = Artifact(path="reports/r1.md", kind=ArtifactKind.REPORT)
        reg.register(a)

        all = reg.list_all()
        assert len(all) == 1
        assert all[0].path == "reports/r1.md"
        assert all[0].sha256 != ""

    def test_register_file_computes_hash(self, tmp_path):
        mission_dir = tmp_path / "mission-test"
        mission_dir.mkdir()
        (mission_dir / "data").mkdir()
        (mission_dir / "data" / "file.txt").write_text("hello omnis", encoding="utf-8")

        reg = ArtifactRegistry(str(mission_dir))
        a = reg.register_file("data/file.txt", kind=ArtifactKind.LOG)
        assert a.sha256 != ""
        assert a.size_bytes > 0

    def test_list_by_kind(self, tmp_path):
        mission_dir = tmp_path / "mission-test"
        mission_dir.mkdir()
        reg = ArtifactRegistry(str(mission_dir))

        reg.register(Artifact(path="r1.md", kind=ArtifactKind.REPORT))
        reg.register(Artifact(path="img1.png", kind=ArtifactKind.IMAGE))
        reg.register(Artifact(path="r2.md", kind=ArtifactKind.REPORT))

        reports = reg.list_by_kind(ArtifactKind.REPORT)
        images = reg.list_by_kind(ArtifactKind.IMAGE)
        assert len(reports) == 2
        assert len(images) == 1

    def test_find_by_path(self, tmp_path):
        mission_dir = tmp_path / "mission-test"
        mission_dir.mkdir()
        reg = ArtifactRegistry(str(mission_dir))
        reg.register(Artifact(path="reports/final.md"))

        found = reg.find_by_path("reports/final.md")
        assert found is not None
        assert found.path == "reports/final.md"

        not_found = reg.find_by_path("missing.md")
        assert not_found is None

    def test_verify_all(self, tmp_path):
        mission_dir = tmp_path / "mission-test"
        mission_dir.mkdir()
        (mission_dir / "reports").mkdir(parents=True)
        (mission_dir / "reports" / "ok.md").write_text("hello", encoding="utf-8")

        reg = ArtifactRegistry(str(mission_dir))
        reg.register_file("reports/ok.md", kind=ArtifactKind.REPORT)

        # Register an artifact whose file doesn't exist (missing)
        reg.register(Artifact(path="reports/missing.md", kind=ArtifactKind.REPORT, sha256="deadbeef"))

        result = reg.verify_all()
        assert "reports/ok.md" in result["verified"]
        assert "reports/missing.md" in result["missing"]

    def test_corruption_detected(self, tmp_path):
        mission_dir = tmp_path / "mission-test"
        mission_dir.mkdir()
        (mission_dir / "reports").mkdir(parents=True)
        f = mission_dir / "reports" / "fragile.md"
        f.write_text("original", encoding="utf-8")

        reg = ArtifactRegistry(str(mission_dir))
        reg.register_file("reports/fragile.md", kind=ArtifactKind.REPORT)

        f.write_text("tampered", encoding="utf-8")
        result = reg.verify_all()
        assert "reports/fragile.md" in result["corrupted"]

    def test_path_traversal_blocked(self, tmp_path):
        mission_dir = tmp_path / "mission-test"
        mission_dir.mkdir()
        reg = ArtifactRegistry(str(mission_dir))

        with pytest.raises(PathTraversalError):
            reg.register(Artifact(path="../../../etc/passwd"))

        with pytest.raises(PathTraversalError):
            reg.register_file("../../../etc/passwd")

    def test_count(self, tmp_path):
        mission_dir = tmp_path / "mission-test"
        mission_dir.mkdir()
        reg = ArtifactRegistry(str(mission_dir))

        assert reg.count() == 0
        reg.register(Artifact(path="a.md"))
        reg.register(Artifact(path="b.md"))
        assert reg.count() == 2
