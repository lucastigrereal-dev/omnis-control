"""Capability Gap Detector — no LLM, no network. Deterministic."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.capability_gap.models import (
    CapabilityGap,
    GapDetectionResult,
    GAP_STATUS_COVERED,
)


def detect(
    request: str,
    caps_config: Optional[Path] = None,
    sectors_config: Optional[Path] = None,
) -> GapDetectionResult:
    """Detect capability gaps for a request.

    Returns GapDetectionResult with status:
    - "covered": at least one active capability matches
    - "gap_detected": sector known but no capability matches
    - "unknown_sector": no sector identified
    """
    from src.skill_matcher.matcher import match_capabilities
    from src.sector_registry.matcher import match_sector

    # Check skill matches first
    skill_results = match_capabilities(request, config_path=caps_config)
    if skill_results:
        sector_id = skill_results[0].sector
        return GapDetectionResult(
            request=request,
            status="covered",
            sector_id=sector_id,
            matched_capabilities=[r.capability_id for r in skill_results],
        )

    # Identify sector even without capability
    sector_result = match_sector(request, config_path=sectors_config)
    if sector_result is None:
        return GapDetectionResult(
            request=request,
            status="unknown_sector",
            sector_id="unknown",
            matched_capabilities=[],
            gaps=[
                CapabilityGap.new(
                    request=request,
                    sector="unknown",
                    missing_capability="unknown_sector_handler",
                    desired_output="sector_identification",
                    risk_level="low",
                    recommendation="Add keywords to sectors_registry.yaml or create a new sector",
                )
            ],
        )

    gap = CapabilityGap.new(
        request=request,
        sector=sector_result.sector_id,
        missing_capability=f"{sector_result.sector_id}_capability",
        desired_output=sector_result.default_outputs[0] if sector_result.default_outputs else "unknown_output",
        risk_level=sector_result.risk_level,
        recommendation=f"Create capability for sector '{sector_result.sector_id}' to handle: {request[:80]}",
    )

    return GapDetectionResult(
        request=request,
        status="gap_detected",
        sector_id=sector_result.sector_id,
        matched_capabilities=[],
        gaps=[gap],
    )
