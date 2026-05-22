"""Spec Exporter — generates capability spec files from a proposal."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.capability_forge_real.errors import ProposalNotFoundError
from src.capability_forge_real.models import CapabilityProposal
from src.capability_forge_lite import store as store_mod
from src.capability_forge_real.store import ProposalStore

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_SPECS_ROOT = BASE / "exports" / "capability_specs"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def export_spec(
    proposal_id: str,
    proposals_log=None,
    specs_root: Optional[Path] = None,
) -> Path:
    """Export capability spec files for a proposal. Returns spec directory path."""
    log_path = proposals_log if proposals_log is not None else store_mod.DEFAULT_PROPOSALS_LOG
    proposal = ProposalStore(log_path).get(proposal_id)
    if proposal is None:
        raise ProposalNotFoundError(f"Proposal {proposal_id} not found")

    root = Path(specs_root) if specs_root is not None else DEFAULT_SPECS_ROOT
    spec_dir = root / proposal_id
    spec_dir.mkdir(parents=True, exist_ok=True)

    _write(spec_dir / "capability_manifest.json", _build_manifest(proposal))
    _write(spec_dir / "CAPABILITY_SPEC.md", _build_spec_md(proposal))
    _write(spec_dir / "implementation_plan.md", _build_impl_plan_md(proposal))
    _write(spec_dir / "risk_assessment.md", _build_risk_md(proposal))
    _write(spec_dir / "next_actions.md", _build_next_actions_md(proposal))

    return spec_dir


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _build_manifest(p: CapabilityProposal) -> str:
    manifest = {
        "proposal_id": p.proposal_id,
        "capability_name": p.capability_name,
        "sector": p.sector,
        "desired_output": p.desired_output,
        "risk_level": p.risk_level,
        "implementation_type": p.implementation_type,
        "status": "spec_draft",
        "approval_required": p.approval_required,
        "created_at": p.created_at,
        "spec_generated_at": _now_iso(),
    }
    return json.dumps(manifest, indent=2, ensure_ascii=False)


def _build_spec_md(p: CapabilityProposal) -> str:
    return f"""# Capability Spec — {p.capability_name}

**Proposal ID:** {p.proposal_id}
**Sector:** {p.sector}
**Desired Output:** {p.desired_output}
**Risk Level:** {p.risk_level}
**Implementation Type:** {p.implementation_type}
**Status:** spec_draft

## Summary

This is a planned capability spec. It does NOT represent an active implementation.
No code is generated. No command is executable.

## Purpose

Gap detected for sector `{p.sector}`. This spec documents what would be needed
to implement `{p.capability_name}` as an OMNIS capability.

## Constraints

- Must not execute without human approval
- Must not call external APIs without OAuth setup
- Must not store sensitive data
"""


def _build_impl_plan_md(p: CapabilityProposal) -> str:
    steps = {
        "manual_process": [
            "1. Define SOP document for the process",
            "2. Create checklist template",
            "3. Assign responsible operator",
            "4. Create CLI wrapper when process is validated",
        ],
        "cli_wrapper": [
            "1. Define input/output contract",
            "2. Implement core logic in src/",
            "3. Add CLI command to appropriate cmd file",
            "4. Write tests (unit + integration)",
            "5. Register as active in capabilities.yaml",
        ],
        "offline_package": [
            "1. Define package structure",
            "2. Implement in src/offline_factory/",
            "3. Add to offline CLI",
            "4. Validate with quality checker",
        ],
        "external_integration_future": [
            "1. Document API contract",
            "2. Implement after OAuth is configured",
            "3. Test in staging environment",
        ],
        "app_factory_future": [
            "1. Define PRD",
            "2. Create repo plan",
            "3. Generate technical spec",
            "4. Implement via app factory pipeline",
        ],
    }.get(p.implementation_type, ["1. Define implementation approach"])

    lines = [f"# Implementation Plan — {p.capability_name}", ""]
    lines.append(f"**Type:** {p.implementation_type}")
    lines.append("")
    lines.append("## Steps")
    lines.extend(steps)
    lines.append("")
    lines.append("*This plan is speculative until implementation begins.*")
    return "\n".join(lines)


def _build_risk_md(p: CapabilityProposal) -> str:
    return f"""# Risk Assessment — {p.capability_name}

**Risk Level:** {p.risk_level}
**Approval Required:** {p.approval_required}

## Risk Factors

- Implementation type: {p.implementation_type}
- Sector risk baseline: {p.risk_level}

## Mitigations

- Capability registered as `planned`, not `active`
- Activation requires explicit human approval + real implementation
- No external calls until OAuth configured
"""


def _build_next_actions_md(p: CapabilityProposal) -> str:
    lines = [f"# Next Actions — {p.proposal_id}", ""]
    for action in p.next_actions:
        lines.append(f"- [ ] `{action}`")
    if p.approval_required and not p.approval_id:
        lines.append(f"- [ ] `jarvis forge-lite request-approval {p.proposal_id}`")
    lines.append(f"- [ ] `jarvis forge-lite register {p.proposal_id}` (after approval)")
    return "\n".join(lines)
