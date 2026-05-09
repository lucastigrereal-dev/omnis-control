"""Skill Matcher — keyword-based capability matching. No LLM. No network."""
from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Optional

from src.skill_matcher.loader import load_capabilities, DEFAULT_CONFIG_PATH
from src.skill_matcher.models import Capability, SkillMatchResult


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in normalized if not unicodedata.combining(c))


def match_capabilities(
    text: str,
    config_path: Optional[Path] = None,
    sector_filter: Optional[str] = None,
    limit: int = 5,
    include_planned: bool = False,
) -> list[SkillMatchResult]:
    """Return top matching active (and optionally planned) capabilities for a request text.

    Returns up to `limit` results sorted by confidence descending.
    """
    caps = load_capabilities(config_path)
    norm_text = _normalize(text)
    results = []
    allowed_statuses = {"active", "planned"} if include_planned else {"active"}

    for cap in caps:
        if cap.status not in allowed_statuses:
            continue
        if sector_filter and cap.sector != sector_filter:
            continue
        matched = [kw for kw in cap.keywords if _normalize(kw) in norm_text]
        if not matched:
            continue
        score = len(matched) / max(len(cap.keywords), 1)
        results.append(SkillMatchResult(
            capability_id=cap.capability_id,
            sector=cap.sector,
            command=cap.command,
            output=cap.output,
            risk_level=cap.risk_level,
            matched_keywords=matched,
            confidence=round(score, 3),
            requires_approval=cap.risk_level == "high",
        ))

    results.sort(key=lambda r: r.confidence, reverse=True)
    return results[:limit]


def list_capabilities(
    config_path: Optional[Path] = None,
    active_only: bool = True,
    include_planned: bool = False,
) -> list[Capability]:
    caps = load_capabilities(config_path)
    if active_only and not include_planned:
        return [c for c in caps if c.status == "active"]
    if include_planned:
        return [c for c in caps if c.status in ("active", "planned")]
    return caps


def get_capability(
    capability_id: str,
    config_path: Optional[Path] = None,
) -> Optional[Capability]:
    for c in load_capabilities(config_path):
        if c.capability_id == capability_id:
            return c
    return None
