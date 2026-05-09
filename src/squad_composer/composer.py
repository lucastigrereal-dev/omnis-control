"""Squad Composer — deterministic, no LLM, no network."""
from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Optional

from src.squad_composer.models import SquadPlan, SquadRoleAssignment
from src.role_registry.matcher import match_roles_by_sector
from src.skill_matcher.matcher import match_capabilities
from src.sector_registry.matcher import match_sector

# Roles always added for any squad
_UNIVERSAL_ROLES = ["qa_auditor"]

# Sector → extra roles to always include
_SECTOR_ROLE_MAP: dict[str, list[str]] = {
    "marketing": ["marketing_strategist", "copywriter", "visual_director"],
    "sales": ["sales_strategist", "copywriter"],
    "apps": ["app_architect"],
    "operations": ["operations_manager"],
    "knowledge": [],
    "finance": [],
    "automation": [],
}

# Output keywords → roles that produce them
_OUTPUT_HINTS: dict[str, str] = {
    "video": "video_planner",
    "reels": "video_planner",
    "roteiro": "video_planner",
    "script": "copywriter",
    "caption": "copywriter",
    "legenda": "copywriter",
    "app": "app_architect",
    "crm": "app_architect",
    "dashboard": "app_architect",
    "sop": "operations_manager",
    "checklist": "operations_manager",
    "pitch": "sales_strategist",
    "oferta": "sales_strategist",
}


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in normalized if not unicodedata.combining(c))


def compose_squad(
    request: str,
    roles_config: Optional[Path] = None,
    caps_config: Optional[Path] = None,
    sector_config: Optional[Path] = None,
) -> SquadPlan:
    """Compose a SquadPlan from a plain-text request. Deterministic, no LLM."""
    norm_req = _normalize(request)

    # Detect sector
    sector_result = match_sector(request, config_path=sector_config)
    sector = sector_result.sector_id if sector_result else "unknown"

    # Detect capabilities
    cap_results = match_capabilities(request, config_path=caps_config)
    capabilities = [c.capability_id for c in cap_results]

    # Build role set
    role_ids: list[str] = list(_SECTOR_ROLE_MAP.get(sector, []))

    # Add output-hinted roles
    for keyword, role_id in _OUTPUT_HINTS.items():
        if keyword in norm_req and role_id not in role_ids:
            role_ids.append(role_id)

    # Always add universal roles
    for uid in _UNIVERSAL_ROLES:
        if uid not in role_ids:
            role_ids.append(uid)

    # Build SquadRoleAssignment from role_registry
    from src.role_registry.matcher import get_role
    from src.role_registry.errors import RoleNotFoundError

    assignments: list[SquadRoleAssignment] = []
    warnings: list[str] = []
    for rid in role_ids:
        try:
            role = get_role(rid, config_path=roles_config)
            assignments.append(SquadRoleAssignment(
                role_id=role.role_id,
                role_name=role.name,
                reason=f"assigned for sector '{sector}'",
                expected_outputs=role.outputs,
                risk_level=role.risk_level,
            ))
        except RoleNotFoundError:
            warnings.append(f"Role '{rid}' not found in registry — skipped")

    rationale = (
        f"Sector '{sector}' detected. "
        f"{len(assignments)} roles assigned. "
        f"{len(capabilities)} capabilities matched."
    )

    return SquadPlan.new(
        request=request,
        sector=sector,
        roles=assignments,
        capabilities=capabilities,
        rationale=rationale,
        warnings=warnings,
    )
