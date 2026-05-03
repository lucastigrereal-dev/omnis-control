"""Sectors Checker — Le sectors.yaml e expoe status dos setores."""

import os
import re
from typing import Optional

import yaml

SECTORS_PATH = os.path.expanduser("~/omnis-control/config/sectors.yaml")


def _load_yaml_block() -> dict:
    """Extrai o bloco ```yaml ... ``` do arquivo markdown."""
    path = os.path.expanduser(SECTORS_PATH)
    if not os.path.isfile(path):
        return {}
    text = open(path, encoding="utf-8").read()
    # Extract content between ```yaml and ```
    match = re.search(r"```yaml\s*\n(.*?)```", text, re.DOTALL)
    if not match:
        return {}
    try:
        return yaml.safe_load(match.group(1)) or {}
    except Exception:
        return {}


def check() -> dict:
    """Retorna dict com setores e status."""
    data = _load_yaml_block()
    raw = data.get("sectors", [])
    sectors = []
    for s in raw:
        sectors.append({
            "id": s.get("id", "?"),
            "objective": s.get("objective", ""),
            "status": s.get("status", "unknown"),
            "implementation_phase": s.get("implementation_phase", ""),
            "available_skills": s.get("available_skills", []),
            "next_action": s.get("next_action", s.get("next_steps", [None])[0] if s.get("next_steps") else ""),
            "risks": s.get("risks", []),
        })

    return {"sectors": sectors, "total": len(sectors)}


def by_status() -> dict[str, list]:
    """Agrupa setores por status."""
    result = check()
    grouped: dict[str, list] = {}
    for s in result.get("sectors", []):
        st = s["status"]
        grouped.setdefault(st, []).append(s["id"])
    return grouped


def get_sector(sector_id: str) -> Optional[dict]:
    """Retorna um setor especifico por ID."""
    result = check()
    for s in result.get("sectors", []):
        if s["id"] == sector_id:
            return s
    return None
