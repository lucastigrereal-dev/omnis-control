"""FIO 3 — activator: bridge Forge DONE → SkillCatalog active.

activate_capability() flips capabilities.yaml status planned→active and
writes the derived SkillDefinition to the SkillCatalog (skills.json).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import yaml

from src.skills_bridge.models import SkillDefinition, SkillRisk


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", name.lower()).strip("_")


def capability_to_skill_definition(cap_id: str, cap_data: dict) -> SkillDefinition:
    """Convert a capabilities.yaml entry to a SkillDefinition with status='active'."""
    risk_raw = cap_data.get("risk_level", "low").upper()
    try:
        risk = SkillRisk(risk_raw)
    except ValueError:
        risk = SkillRisk.LOW

    return SkillDefinition(
        skill_id=cap_id,
        name=cap_id.replace("_", " ").title(),
        description=cap_data.get("output", ""),
        tier="generated",
        risk=risk,
        requires_approval=risk in (SkillRisk.MEDIUM, SkillRisk.HIGH, SkillRisk.CRITICAL),
        category=cap_data.get("sector", ""),
        tags=list(cap_data.get("keywords", [])),
        intents=[],
        status="active",
    )


def activate_capability(
    cap_id: str,
    caps_path: Path,
    catalog_path: Optional[Path] = None,
    dry_run: bool = True,
) -> Optional[SkillDefinition]:
    """Flip capability status planned→active and write to SkillCatalog.

    Returns the SkillDefinition that was (or would be) activated.
    Returns None if cap_id is not found in capabilities.yaml.

    dry_run=True: computes and returns the SkillDefinition without writing to disk.
    dry_run=False: flips yaml status AND appends to catalog if catalog_path provided.
    """
    if not caps_path.exists():
        return None

    raw = yaml.safe_load(caps_path.read_text(encoding="utf-8")) or {}
    caps_data: dict = raw.get("capabilities", {})

    if cap_id not in caps_data:
        return None

    skill_def = capability_to_skill_definition(cap_id, caps_data[cap_id])

    if not dry_run:
        caps_data[cap_id]["status"] = "active"
        raw["capabilities"] = caps_data
        caps_path.write_text(
            yaml.dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8"
        )

        if catalog_path is not None:
            from src.skills_bridge.skill_catalog import SkillCatalog
            SkillCatalog(catalog_path=str(catalog_path)).write_skill(skill_def)

    return skill_def
