"""Render engine models."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RenderStatus(str, Enum):
    OK = "ok"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class RenderResult:
    render_id: str
    package_id: str
    status: RenderStatus
    html_path: Optional[str] = None
    render_manifest_path: Optional[str] = None
    files_generated: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "render_id": self.render_id,
            "package_id": self.package_id,
            "status": self.status.value,
            "html_path": self.html_path,
            "render_manifest_path": self.render_manifest_path,
            "files_generated": self.files_generated,
            "warnings": self.warnings,
            "errors": self.errors,
        }
