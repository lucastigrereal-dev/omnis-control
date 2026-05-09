"""Sector Matcher — keyword-based, deterministic, no LLM."""
from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Optional

from src.sector_registry.loader import load_sectors, DEFAULT_CONFIG_PATH
from src.sector_registry.models import Sector, SectorMatchResult


def _normalize(text: str) -> str:
    """Lowercase + remove accents."""
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in normalized if not unicodedata.combining(c))


def match_sector(
    text: str,
    config_path: Optional[Path] = None,
) -> Optional[SectorMatchResult]:
    """Return best sector match or None if no keywords hit.

    Scoring: count of matched keywords / total keywords in sector.
    Ties broken by sector order in config.
    """
    sectors = load_sectors(config_path)
    norm_text = _normalize(text)

    best: Optional[SectorMatchResult] = None
    best_score = 0.0

    for sector in sectors:
        matched = [kw for kw in sector.keywords if _normalize(kw) in norm_text]
        if not matched:
            continue
        score = len(matched) / max(len(sector.keywords), 1)
        if score > best_score:
            best_score = score
            best = SectorMatchResult(
                sector_id=sector.sector_id,
                sector_name=sector.name,
                matched_keywords=matched,
                confidence=round(score, 3),
                risk_level=sector.risk_level,
                default_outputs=sector.default_outputs,
            )

    return best


def list_sectors(config_path: Optional[Path] = None) -> list[Sector]:
    return load_sectors(config_path)


def get_sector(sector_id: str, config_path: Optional[Path] = None) -> Optional[Sector]:
    for s in load_sectors(config_path):
        if s.sector_id == sector_id:
            return s
    return None
