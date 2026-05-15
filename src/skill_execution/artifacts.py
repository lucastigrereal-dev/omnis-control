import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@dataclass
class SkillArtifact:
    artifact_id: str = field(default_factory=lambda: _new_id("saf"))
    execution_result_id: str = ""
    artifact_type: str = ""
    data: dict = field(default_factory=dict)
    file_path: str = ""
    size_bytes: int = 0
    mime_type: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "artifact_id": self.artifact_id,
            "execution_result_id": self.execution_result_id,
            "artifact_type": self.artifact_type,
            "data": self.data,
            "file_path": self.file_path,
            "size_bytes": self.size_bytes,
            "mime_type": self.mime_type,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SkillArtifact":
        return cls(
            artifact_id=data.get("artifact_id", ""),
            execution_result_id=data.get("execution_result_id", ""),
            artifact_type=data.get("artifact_type", ""),
            data=data.get("data", {}),
            file_path=data.get("file_path", ""),
            size_bytes=data.get("size_bytes", 0),
            mime_type=data.get("mime_type", ""),
            created_at=data.get("created_at", ""),
        )


class ArtifactRegistry:
    def __init__(self):
        self._artifacts: dict[str, SkillArtifact] = {}
        self._index_by_result: dict[str, list[str]] = {}

    def register(self, artifact: SkillArtifact) -> None:
        self._artifacts[artifact.artifact_id] = artifact
        if artifact.execution_result_id not in self._index_by_result:
            self._index_by_result[artifact.execution_result_id] = []
        self._index_by_result[artifact.execution_result_id].append(artifact.artifact_id)

    def get(self, artifact_id: str) -> Optional[SkillArtifact]:
        return self._artifacts.get(artifact_id)

    def get_by_result(self, execution_result_id: str) -> list[SkillArtifact]:
        ids = self._index_by_result.get(execution_result_id, [])
        return [self._artifacts[a] for a in ids if a in self._artifacts]

    @property
    def count(self) -> int:
        return len(self._artifacts)

    def to_dict(self) -> dict:
        return {
            "artifacts": {k: v.to_dict() for k, v in self._artifacts.items()},
        }
