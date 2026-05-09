"""Roles loader — reads config/roles.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from src.role_registry.models import Role
from src.role_registry.errors import InvalidRolesConfigError

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_ROLES_PATH = BASE / "config" / "roles.yaml"


def load_roles(config_path: Optional[Path] = None) -> list[Role]:
    path = Path(config_path) if config_path else DEFAULT_ROLES_PATH
    if not path.exists():
        raise InvalidRolesConfigError(f"Roles config not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise InvalidRolesConfigError(f"Invalid YAML: {exc}") from exc

    if not isinstance(raw, dict) or "roles" not in raw:
        raise InvalidRolesConfigError("Missing 'roles' key")

    roles_data = raw["roles"]
    if not isinstance(roles_data, dict):
        raise InvalidRolesConfigError("'roles' must be a mapping")

    roles = []
    for role_id, data in roles_data.items():
        if not isinstance(data, dict):
            continue
        roles.append(Role(
            role_id=role_id,
            name=str(data.get("name", role_id)),
            sectors=[str(s) for s in data.get("sectors", [])],
            responsibilities=[str(r) for r in data.get("responsibilities", [])],
            outputs=[str(o) for o in data.get("outputs", [])],
            risk_level=str(data.get("risk_level", "low")),
        ))
    return roles
