from src.skill_execution.artifacts import SkillArtifact, ArtifactRegistry


class TestSkillArtifact:
    def test_default_artifact(self):
        a = SkillArtifact()
        assert a.artifact_id.startswith("saf_")

    def test_file_artifact(self):
        a = SkillArtifact(
            artifact_type="file",
            file_path="output/caption.txt",
            size_bytes=1024,
            mime_type="text/plain",
        )
        assert a.artifact_type == "file"
        assert a.file_path == "output/caption.txt"
        assert a.size_bytes == 1024

    def test_roundtrip(self):
        a = SkillArtifact(
            execution_result_id="srr_test",
            artifact_type="json",
            data={"caption": "hello"},
        )
        d = a.to_dict()
        a2 = SkillArtifact.from_dict(d)
        assert a2.execution_result_id == "srr_test"
        assert a2.data == {"caption": "hello"}


class TestArtifactRegistry:
    def test_register_and_get(self):
        reg = ArtifactRegistry()
        a = SkillArtifact(artifact_type="test")
        reg.register(a)
        assert reg.count == 1
        assert reg.get(a.artifact_id) is a

    def test_get_by_result(self):
        reg = ArtifactRegistry()
        a1 = SkillArtifact(execution_result_id="r1", artifact_type="a")
        a2 = SkillArtifact(execution_result_id="r1", artifact_type="b")
        a3 = SkillArtifact(execution_result_id="r2", artifact_type="c")
        reg.register(a1)
        reg.register(a2)
        reg.register(a3)
        assert len(reg.get_by_result("r1")) == 2
        assert len(reg.get_by_result("r2")) == 1
        assert len(reg.get_by_result("r3")) == 0

    def test_to_dict(self):
        reg = ArtifactRegistry()
        reg.register(SkillArtifact(execution_result_id="x"))
        d = reg.to_dict()
        assert "artifacts" in d
