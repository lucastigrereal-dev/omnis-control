"""App Factory Executable models."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum


class AppType(str, Enum):
    API_BACKEND = "api_backend"
    FULLSTACK = "fullstack"
    CLI_TOOL = "cli_tool"


@dataclass
class AppSpec:
    """Specification for a complete runnable app."""
    app_name: str
    app_type: AppType
    description: str
    entities: list[str] = field(default_factory=list)
    endpoints: list[str] = field(default_factory=list)
    target_dir: str = ""
    python_version: str = "3.12"
    port: int = 8000
    database: str = "sqlite"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["app_type"] = self.app_type.value
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "AppSpec":
        app_type = d.get("app_type", "api_backend")
        if isinstance(app_type, str):
            app_type = AppType(app_type)
        return cls(
            app_name=d.get("app_name", "my_app"),
            app_type=app_type,
            description=d.get("description", ""),
            entities=d.get("entities", []),
            endpoints=d.get("endpoints", []),
            target_dir=d.get("target_dir", ""),
            python_version=d.get("python_version", "3.12"),
            port=d.get("port", 8000),
            database=d.get("database", "sqlite"),
        )


@dataclass
class GeneratedFile:
    relative_path: str
    content: str
    is_executable: bool = False

    def to_dict(self) -> dict:
        return asdict(self)
