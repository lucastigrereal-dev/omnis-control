"""Capabilities loader — reads config/capabilities.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from src.skill_matcher.models import Capability
from src.skill_matcher.errors import InvalidCapabilitiesConfigError

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = BASE / "config" / "capabilities.yaml"


def load_capabilities(config_path: Optional[Path] = None) -> list[Capability]:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.exists():
        raise InvalidCapabilitiesConfigError(f"Capabilities config not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise InvalidCapabilitiesConfigError(f"Invalid YAML: {exc}") from exc

    if not isinstance(raw, dict) or "capabilities" not in raw:
        raise InvalidCapabilitiesConfigError("Missing 'capabilities' key")

    caps_data = raw["capabilities"]
    if not isinstance(caps_data, dict):
        raise InvalidCapabilitiesConfigError("'capabilities' must be a mapping")

    caps = []
    for cap_id, data in caps_data.items():
        if not isinstance(data, dict):
            continue
        caps.append(Capability(
            capability_id=cap_id,
            sector=str(data.get("sector", "unknown")),
            command=str(data.get("command", "")),
            output=str(data.get("output", "")),
            risk_level=str(data.get("risk_level", "low")),
            status=str(data.get("status", "active")),
            keywords=[str(k) for k in data.get("keywords", [])],
        ))
    return caps
