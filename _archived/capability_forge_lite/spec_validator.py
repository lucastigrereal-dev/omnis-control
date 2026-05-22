"""Spec Validator — validates exported capability spec files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.capability_forge_real.errors import ProposalNotFoundError
from src.capability_forge_lite import store as store_mod
from src.capability_forge_real.store import ProposalStore
from src.capability_forge_real.spec_exporter import DEFAULT_SPECS_ROOT

REQUIRED_FILES = [
    "capability_manifest.json",
    "CAPABILITY_SPEC.md",
    "implementation_plan.md",
    "risk_assessment.md",
    "next_actions.md",
]

REQUIRED_MANIFEST_KEYS = [
    "proposal_id",
    "capability_name",
    "sector",
    "desired_output",
    "risk_level",
    "implementation_type",
    "status",
    "approval_required",
    "created_at",
    "spec_generated_at",
]

FORBIDDEN_MANIFEST_PREFIXES = (
    "meta_",
    "instagram_",
    "secret",
    "token",
    "password",
    "api_key",
    "client_secret",
)


def validate_spec(
    proposal_id: str,
    proposals_log=None,
    specs_root: Optional[Path] = None,
) -> dict:
    """Validate exported spec files for a proposal.

    Returns a dict with keys:
        valid (bool), proposal_id, spec_dir, files_present (list),
        files_missing (list), manifest_valid (bool), manifest_errors (list),
        no_secrets (bool)
    """
    log_path = proposals_log if proposals_log is not None else store_mod.DEFAULT_PROPOSALS_LOG
    proposal = ProposalStore(log_path).get(proposal_id)
    if proposal is None:
        raise ProposalNotFoundError(f"Proposal {proposal_id} not found")

    root = Path(specs_root) if specs_root is not None else DEFAULT_SPECS_ROOT
    spec_dir = root / proposal_id

    files_present = []
    files_missing = []
    for fname in REQUIRED_FILES:
        if (spec_dir / fname).exists():
            files_present.append(fname)
        else:
            files_missing.append(fname)

    manifest_errors = []
    manifest_valid = False
    no_secrets = True

    manifest_path = spec_dir / "capability_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for key in REQUIRED_MANIFEST_KEYS:
                if key not in manifest:
                    manifest_errors.append(f"Missing key: {key}")
            if manifest.get("status") != "spec_draft":
                manifest_errors.append(f"Expected status='spec_draft', got '{manifest.get('status')}'")
            if manifest.get("proposal_id") != proposal_id:
                manifest_errors.append("proposal_id mismatch in manifest")
            no_secrets = _no_secrets(manifest)
            if not no_secrets:
                manifest_errors.append("Forbidden secret key found in manifest")
            manifest_valid = len(manifest_errors) == 0
        except json.JSONDecodeError as e:
            manifest_errors.append(f"Invalid JSON: {e}")

    valid = (
        len(files_missing) == 0
        and manifest_valid
        and no_secrets
    )

    return {
        "valid": valid,
        "proposal_id": proposal_id,
        "spec_dir": str(spec_dir),
        "files_present": files_present,
        "files_missing": files_missing,
        "manifest_valid": manifest_valid,
        "manifest_errors": manifest_errors,
        "no_secrets": no_secrets,
    }


def _no_secrets(manifest: dict) -> bool:
    for key in manifest:
        if any(key.lower().startswith(prefix) for prefix in FORBIDDEN_MANIFEST_PREFIXES):
            return False
    return True
