"""Role Matcher — sector and output based matching."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.role_registry.loader import load_roles, DEFAULT_ROLES_PATH
from src.role_registry.models import Role, RoleMatchResult
from src.role_registry.errors import RoleNotFoundError


def match_roles_by_sector(
    sector: str,
    config_path: Optional[Path] = None,
) -> list[RoleMatchResult]:
    """Return all roles that cover the given sector."""
    roles = load_roles(config_path)
    results = []
    for role in roles:
        if role.matches_sector(sector):
            results.append(RoleMatchResult(
                role_id=role.role_id,
                name=role.name,
                sectors=role.sectors,
                outputs=role.outputs,
                risk_level=role.risk_level,
                reason=f"covers sector '{sector}'",
            ))
    return results


def match_roles_by_output(
    output: str,
    config_path: Optional[Path] = None,
) -> list[RoleMatchResult]:
    """Return all roles that produce the given output."""
    roles = load_roles(config_path)
    results = []
    for role in roles:
        if role.matches_output(output):
            results.append(RoleMatchResult(
                role_id=role.role_id,
                name=role.name,
                sectors=role.sectors,
                outputs=role.outputs,
                risk_level=role.risk_level,
                reason=f"produces output '{output}'",
            ))
    return results


def get_role(role_id: str, config_path: Optional[Path] = None) -> Role:
    """Return a specific role by ID. Raises RoleNotFoundError if missing."""
    for role in load_roles(config_path):
        if role.role_id == role_id:
            return role
    raise RoleNotFoundError(f"Role '{role_id}' not found")


def list_all_roles(config_path: Optional[Path] = None) -> list[Role]:
    return load_roles(config_path)
