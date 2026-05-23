"""P26 App Factory Supreme — models extending src/app_factory/."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── Build status constants ──────────────────────────────────────────────────

BUILD_PLANNED = "planned"
BUILD_BLUEPRINTING = "blueprinting"
BUILD_GENERATING = "generating"
BUILD_TESTING = "testing"
BUILD_SCANNING = "scanning"
BUILD_PACKAGING = "packaging"
BUILD_COMPLETE = "complete"
BUILD_FAILED = "failed"
BUILD_ROLLED_BACK = "rolled_back"

VALID_BUILD_STATUSES = {
    BUILD_PLANNED, BUILD_BLUEPRINTING, BUILD_GENERATING, BUILD_TESTING,
    BUILD_SCANNING, BUILD_PACKAGING, BUILD_COMPLETE, BUILD_FAILED, BUILD_ROLLED_BACK,
}

TERMINAL_BUILD_STATUSES = {BUILD_COMPLETE, BUILD_FAILED, BUILD_ROLLED_BACK}

# ── App type constants ──────────────────────────────────────────────────────

APP_TYPE_WEB = "web"
APP_TYPE_CLI = "cli"
APP_TYPE_API = "api"
APP_TYPE_LIBRARY = "library"


# ── ModuleBuild ─────────────────────────────────────────────────────────────

@dataclass
class ModuleBuild:
    module_name: str
    files_generated: list[str] = field(default_factory=list)
    build_result_id: str = ""
    tests_pass: bool = False
    test_count: int = 0
    test_pass_rate: float = 0.0
    policy_scan_pass: bool = False
    policy_violations: int = 0
    errors: list[str] = field(default_factory=list)
    status: str = BUILD_PLANNED

    @classmethod
    def new(cls, module_name: str) -> "ModuleBuild":
        return cls(module_name=module_name)

    def to_dict(self) -> dict:
        return {
            "module_name": self.module_name,
            "files_generated": self.files_generated,
            "build_result_id": self.build_result_id,
            "tests_pass": self.tests_pass,
            "test_count": self.test_count,
            "test_pass_rate": self.test_pass_rate,
            "policy_scan_pass": self.policy_scan_pass,
            "policy_violations": self.policy_violations,
            "errors": self.errors,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ModuleBuild":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    @property
    def is_success(self) -> bool:
        return self.status == BUILD_COMPLETE and len(self.errors) == 0


# ── AppBuild ────────────────────────────────────────────────────────────────

@dataclass
class AppBuild:
    build_id: str
    idea_id: str = ""
    title: str = ""
    status: str = BUILD_PLANNED
    modules: list[ModuleBuild] = field(default_factory=list)
    test_results: dict = field(default_factory=dict)
    policy_violations: list[dict] = field(default_factory=list)
    output_dir: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blueprint_approved: bool = False
    security_approved: bool = False
    package_approved: bool = False
    started_at: str = field(default_factory=_now_iso)
    completed_at: str = ""

    @classmethod
    def new(cls, idea_id: str = "", title: str = "") -> "AppBuild":
        return cls(
            build_id=_new_id("apb"),
            idea_id=idea_id,
            title=title,
        )

    def to_dict(self) -> dict:
        return {
            "build_id": self.build_id,
            "idea_id": self.idea_id,
            "title": self.title,
            "status": self.status,
            "modules": [m.to_dict() for m in self.modules],
            "test_results": self.test_results,
            "policy_violations": self.policy_violations,
            "output_dir": self.output_dir,
            "errors": self.errors,
            "warnings": self.warnings,
            "blueprint_approved": self.blueprint_approved,
            "security_approved": self.security_approved,
            "package_approved": self.package_approved,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AppBuild":
        modules_data = d.get("modules", [])
        modules = [ModuleBuild.from_dict(m) if isinstance(m, dict) else ModuleBuild.new(str(m)) for m in modules_data]
        return cls(
            build_id=d.get("build_id", _new_id("apb")),
            idea_id=d.get("idea_id", ""),
            title=d.get("title", ""),
            status=d.get("status", BUILD_PLANNED),
            modules=modules,
            test_results=d.get("test_results", {}),
            policy_violations=d.get("policy_violations", []),
            output_dir=d.get("output_dir", ""),
            errors=d.get("errors", []),
            warnings=d.get("warnings", []),
            blueprint_approved=d.get("blueprint_approved", False),
            security_approved=d.get("security_approved", False),
            package_approved=d.get("package_approved", False),
            started_at=d.get("started_at", ""),
            completed_at=d.get("completed_at", ""),
        )

    @property
    def is_complete(self) -> bool:
        return self.status == BUILD_COMPLETE

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_BUILD_STATUSES

    @property
    def module_count(self) -> int:
        return len(self.modules)

    @property
    def modules_passing(self) -> int:
        return sum(1 for m in self.modules if m.tests_pass)

    @property
    def overall_pass_rate(self) -> float:
        if not self.modules:
            return 0.0
        return self.modules_passing / len(self.modules)
