"""P22 Capability Forge Real models — build results, states, templates."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from src.capability_forge_lite.models import (
    CapabilityProposal,
    PROPOSAL_STATUS_APPROVED,
    IMPL_TYPE_MANUAL_PROCESS,
    IMPL_TYPE_CLI_WRAPPER,
    IMPL_TYPE_OFFLINE_PACKAGE,
    IMPL_TYPE_EXTERNAL_FUTURE,
    IMPL_TYPE_APP_FACTORY_FUTURE,
    VALID_IMPL_TYPES,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── Build State ──────────────────────────────────────────────────────────────

class BuildState(str, Enum):
    PROPOSAL_APPROVED = "proposal_approved"
    SCAFFOLDING = "scaffolding"
    POLICY_SCANNING = "policy_scanning"
    TEST_GENERATING = "test_generating"
    VALIDATING = "validating"
    REGISTERING = "registering"
    DONE = "done"
    POLICY_FAILED = "policy_failed"
    TEST_FAILED = "test_failed"


TERMINAL_STATES = {BuildState.DONE, BuildState.POLICY_FAILED, BuildState.TEST_FAILED}


# ── Build Result ─────────────────────────────────────────────────────────────

@dataclass
class BuildResult:
    """Resultado de build de uma capability."""
    build_id: str
    proposal_id: str
    capability_name: str
    implementation_type: str
    files_created: list[str] = field(default_factory=list)
    test_count: int = 0
    policy_scan: dict = field(default_factory=dict)
    state: str = ""
    dry_run: bool = True
    generated_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        proposal: CapabilityProposal,
        dry_run: bool = True,
    ) -> "BuildResult":
        return cls(
            build_id=_new_id("bld"),
            proposal_id=proposal.proposal_id,
            capability_name=proposal.capability_name,
            implementation_type=proposal.implementation_type,
            policy_scan={"passed": True, "violations": []},
            state=BuildState.PROPOSAL_APPROVED.value,
            dry_run=dry_run,
        )

    @property
    def is_terminal(self) -> bool:
        return self.state in {s.value for s in TERMINAL_STATES}

    @property
    def is_success(self) -> bool:
        return self.state == BuildState.DONE.value

    def transition(self, new_state: BuildState) -> None:
        """Transiciona para novo estado com validacao."""
        valid_transitions = {
            BuildState.PROPOSAL_APPROVED: [BuildState.SCAFFOLDING],
            BuildState.SCAFFOLDING: [BuildState.POLICY_SCANNING, BuildState.REGISTERING],
            BuildState.POLICY_SCANNING: [BuildState.TEST_GENERATING, BuildState.POLICY_FAILED, BuildState.REGISTERING],
            BuildState.TEST_GENERATING: [BuildState.VALIDATING],
            BuildState.VALIDATING: [BuildState.REGISTERING, BuildState.TEST_FAILED],
            BuildState.REGISTERING: [BuildState.DONE],
        }
        current = BuildState(self.state)
        allowed = valid_transitions.get(current, [])
        if new_state not in allowed:
            raise ValueError(
                f"Transicao invalida: {self.state} -> {new_state.value}. "
                f"Permitidas: {[s.value for s in allowed]}"
            )
        self.state = new_state.value

    def to_dict(self) -> dict:
        return {
            "build_id": self.build_id,
            "proposal_id": self.proposal_id,
            "capability_name": self.capability_name,
            "implementation_type": self.implementation_type,
            "files_created": self.files_created,
            "test_count": self.test_count,
            "policy_scan": self.policy_scan,
            "state": self.state,
            "dry_run": self.dry_run,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BuildResult":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Skill Template Config ────────────────────────────────────────────────────

@dataclass
class SkillTemplateConfig:
    """Configuracao de template para geracao de skill."""
    template_id: str
    implementation_type: str
    target_dir: str              # relative to src/
    filename: str                # e.g. "run.py"
    class_prefix: str            # prefixo para nomes de classe
    test_dir: str                # relative to tests/
    test_filename: str           # e.g. "test_run.py"
    min_tests: int = 3

    @classmethod
    def new(
        cls,
        implementation_type: str,
        target_dir: str,
        filename: str = "run.py",
        class_prefix: str = "",
        test_dir: str = "",
        test_filename: str = "test_run.py",
        min_tests: int = 3,
    ) -> "SkillTemplateConfig":
        return cls(
            template_id=_new_id("tpl"),
            implementation_type=implementation_type,
            target_dir=target_dir,
            filename=filename,
            class_prefix=class_prefix,
            test_dir=test_dir,
            test_filename=test_filename,
            min_tests=min_tests,
        )

    def to_dict(self) -> dict:
        return {
            "template_id": self.template_id,
            "implementation_type": self.implementation_type,
            "target_dir": self.target_dir,
            "filename": self.filename,
            "class_prefix": self.class_prefix,
            "test_dir": self.test_dir,
            "test_filename": self.test_filename,
            "min_tests": self.min_tests,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SkillTemplateConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
