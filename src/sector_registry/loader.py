"""Sector Registry Loader — reads config/sectors_registry.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from src.sector_registry.models import Sector
from src.sector_registry.errors import InvalidSectorConfigError

BASE = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = BASE / "config" / "sectors_registry.yaml"


def load_sectors(config_path: Optional[Path] = None) -> list[Sector]:
    """Load sectors from YAML config. Returns list of Sector."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.exists():
        raise InvalidSectorConfigError(f"Sectors config not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise InvalidSectorConfigError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(raw, dict) or "sectors" not in raw:
        raise InvalidSectorConfigError(f"Missing 'sectors' key in {path}")

    sectors_data = raw["sectors"]
    if not isinstance(sectors_data, dict):
        raise InvalidSectorConfigError("'sectors' must be a mapping")

    sectors = []
    for sector_id, data in sectors_data.items():
        if not isinstance(data, dict):
            raise InvalidSectorConfigError(f"Sector '{sector_id}' must be a mapping")
        required = ("name", "keywords", "default_outputs", "risk_level")
        for field in required:
            if field not in data:
                raise InvalidSectorConfigError(f"Sector '{sector_id}' missing field '{field}'")
        sectors.append(Sector(
            sector_id=sector_id,
            name=data["name"],
            keywords=[str(k) for k in data["keywords"]],
            default_outputs=[str(o) for o in data["default_outputs"]],
            risk_level=str(data["risk_level"]),
        ))
    return sectors
