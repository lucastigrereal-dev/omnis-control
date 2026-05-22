"""Models for Capability Forge Real — merged from capabilityforge + capability_forge_lite."""
from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional

PROPOSAL_STATUS_DRAFT = "draft"
PROPOSAL_STATUS_NEEDS_APPROVAL = "needs_approval"
PROPOSAL_STATUS_APPROVED = "approved"
PROPOSAL_STATUS_REJECTED = "rejected"
PROPOSAL_STATUS_REGISTERED = "registered"

IMPL_TYPE_MANUAL_PROCESS = "manual_process"
IMPL_TYPE_CLI_WRAPPER = "cli_wrapper"
IMPL_TYPE_OFFLINE_PACKAGE = "offline_package"
IMPL_TYPE_EXTERNAL_FUTURE = "external_integration_future"
IMPL_TYPE_APP_FACTORY_FUTURE = "app_factory_future"

VALID_IMPL_TYPES = {
    IMPL_TYPE_MANUAL_PROCESS,
    IMPL_TYPE_CLI_WRAPPER,
    IMPL_TYPE_OFFLINE_PACKAGE,
    IMPL_TYPE_EXTERNAL_FUTURE,
    IMPL_TYPE_APP_FACTORY_FUTURE,
}


def _make_proposal_id() -> str:
    raw = os.urandom(8)
    return "prop_" + hashlib.sha256(raw).hexdigest()[:8]


@dataclass
class CapabilityProposal:
    proposal_id: str
    gap_id: str
    capability_name: str
    sector: str
    desired_output: str
    risk_level: str
    implementation_type: str
    approval_required: bool
    status: str
    created_at: str
    warnings: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    approval_id: Optional[str] = None

    @classmethod
    def from_gap(
        cls,
        gap_id: str,
        capability_name: str,
        sector: str,
        desired_output: str,
        risk_level: str = "medium",
        implementation_type: str = IMPL_TYPE_MANUAL_PROCESS,
    ) -> "CapabilityProposal":
        approval_required = risk_level in ("medium", "high")
        status = PROPOSAL_STATUS_NEEDS_APPROVAL if approval_required else PROPOSAL_STATUS_DRAFT
        now = datetime.now(timezone.utc).isoformat()
        warnings = []
        next_actions = []
        if implementation_type not in VALID_IMPL_TYPES:
            warnings.append(f"Unknown implementation_type: {implementation_type}")
        if approval_required:
            next_actions.append(f"jarvis forge-lite request-approval <proposal_id>")
        else:
            next_actions.append(f"jarvis forge-lite export-spec <proposal_id>")
        return cls(
            proposal_id=_make_proposal_id(),
            gap_id=gap_id,
            capability_name=capability_name,
            sector=sector,
            desired_output=desired_output,
            risk_level=risk_level,
            implementation_type=implementation_type,
            approval_required=approval_required,
            status=status,
            created_at=now,
            warnings=warnings,
            next_actions=next_actions,
        )

    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "gap_id": self.gap_id,
            "capability_name": self.capability_name,
            "sector": self.sector,
            "desired_output": self.desired_output,
            "risk_level": self.risk_level,
            "implementation_type": self.implementation_type,
            "approval_required": self.approval_required,
            "status": self.status,
            "created_at": self.created_at,
            "warnings": self.warnings,
            "next_actions": self.next_actions,
            "approval_id": self.approval_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CapabilityProposal":
        return cls(
            proposal_id=d["proposal_id"],
            gap_id=d["gap_id"],
            capability_name=d["capability_name"],
            sector=d["sector"],
            desired_output=d["desired_output"],
            risk_level=d.get("risk_level", "medium"),
            implementation_type=d.get("implementation_type", IMPL_TYPE_MANUAL_PROCESS),
            approval_required=d.get("approval_required", True),
            status=d["status"],
            created_at=d["created_at"],
            warnings=d.get("warnings", []),
            next_actions=d.get("next_actions", []),
            approval_id=d.get("approval_id"),
        )


# ── P22 BuildResult / BuildState / SkillTemplateConfig ──────────────────────

def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class BuildState(str, Enum):
    INIT = "init"
    SCAFFOLDING = "scaffolding"
    POLICY_SCANNING = "policy_scanning"
    POLICY_FAILED = "policy_failed"
    TEST_GENERATING = "test_generating"
    VALIDATING = "validating"
    TEST_FAILED = "test_failed"
    REGISTERING = "registering"
    DONE = "done"
    ROLLED_BACK = "rolled_back"


TERMINAL_STATES: set[BuildState] = {BuildState.DONE, BuildState.POLICY_FAILED, BuildState.TEST_FAILED, BuildState.ROLLED_BACK}


@dataclass
class BuildResult:
    build_id: str
    proposal: CapabilityProposal
    dry_run: bool = True
    state: BuildState = BuildState.INIT
    files_created: list[str] = field(default_factory=list)
    policy_scan: dict | None = None
    test_count: int = 0

    @classmethod
    def new(cls, proposal: CapabilityProposal, dry_run: bool = True) -> "BuildResult":
        return cls(build_id=_new_id(), proposal=proposal, dry_run=dry_run)

    def transition(self, state: BuildState) -> None:
        self.state = state

    def to_dict(self) -> dict:
        return {
            "build_id": self.build_id,
            "proposal": self.proposal.to_dict(),
            "dry_run": self.dry_run,
            "state": self.state.value,
            "files_created": self.files_created,
            "policy_scan": self.policy_scan,
            "test_count": self.test_count,
        }


@dataclass
class SkillTemplateConfig:
    implementation_type: str = IMPL_TYPE_CLI_WRAPPER
    target_dir: str = "skills"
    filename: str = "run.py"
    class_prefix: str = "Cli"
    test_dir: str = "skills"
    test_filename: str = "test_run.py"
    min_tests: int = 3
    requires_policy_scan: bool = True

    @classmethod
    def new(
        cls,
        implementation_type: str,
        target_dir: str = "skills",
        filename: str = "run.py",
        class_prefix: str = "",
        test_dir: str = "",
        test_filename: str = "",
        min_tests: int = 3,
        requires_policy_scan: bool = True,
    ) -> "SkillTemplateConfig":
        return cls(
            implementation_type=implementation_type,
            target_dir=target_dir,
            filename=filename,
            class_prefix=class_prefix,
            test_dir=test_dir,
            test_filename=test_filename,
            min_tests=min_tests,
            requires_policy_scan=requires_policy_scan,
        )


# ── Merged from capabilityforge/models.py ────────────────────────────────────

class CreationState(Enum):
    DISCOVERY = auto()
    GAP_CONFIRMED = auto()
    SPEC_READY = auto()
    BUILD = auto()
    BUILD_OK = auto()
    TESTS_PASSED = auto()
    TESTS_FAILED = auto()
    SCORE_OK = auto()
    SCORE_LOW = auto()
    APPROVED = auto()
    DUPLICATE_FOUND = auto()


@dataclass
class SkillSpec:
    name: str
    sector: str
    description: str
    problem_statement: str = ""
    inputs_schema: Dict[str, Any] = field(default_factory=dict)
    outputs_schema: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "low"
    owner: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class CreationContext:
    gap_description: str
    sector: str
    requested_name: str = ""
    state: CreationState = CreationState.DISCOVERY
    spec: Optional[SkillSpec] = None
    logs: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    scorecard: Optional[Dict[str, Any]] = None


@dataclass
class RegistryEntry:
    id: str
    name: str
    version: str = "0.1.0"
    description: str = ""
    status: str = "generated"
    risk_level: str = "low"
    owner: str = ""
    tags: List[str] = field(default_factory=list)
    path: Optional[Path] = None
    manifest_path: Optional[Path] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    usage_stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillManifest:
    name: str
    description: str
    sector: str
    mode: str = "readonly"
    risk: str = "low"
    requires: List[str] = field(default_factory=list)
