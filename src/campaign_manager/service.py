"""P19 Campaign Manager — CampaignOrchestrator service.

Static methods for campaign orchestration, budget allocation, ROI tracking,
state transitions, and manifest generation.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.campaign_manager.errors import BudgetError, CampaignError, ROIError, StateTransitionError
from src.campaign_manager.models import (
    ROICalculation,
    BudgetTracker,
    Campaign,
    CampaignStatus,
    VALID_TRANSITIONS,
    _now_iso,
    _new_id,
)

# Authorized upstream imports — P5 + P8 + P13 only
from src.marketing.models import CampaignBrief, CampaignPackage, MarketingObjective, AudienceProfile
from src.publisher_argos.models import PublisherHandoff, ArgosExportItem, ArgosExportPackage
from src.analytics.models import MetricDefinition
from src.analytics.service import MetricSummary

logger = logging.getLogger(__name__)


class CampaignOrchestrator:
    """Coordinates campaign lifecycle from brief through publishing to ROI analysis.

    All methods are @staticmethod — the orchestrator is stateless.
    """

    @staticmethod
    def orchestrate_campaign(
        brief: CampaignBrief,
        channels: Optional[list[dict]] = None,
        budget_total: Optional[float] = None,
        dry_run: bool = True,
    ) -> Campaign:
        """Create a Campaign from a CampaignBrief.

        Pipeline: validate contract → allocate budget → build publish plan.
        """
        if not brief.name:
            raise CampaignError("brief must have a name")

        if channels is None:
            raise CampaignError("brief must define at least 1 channel")

        if len(channels) == 0:
            raise CampaignError("brief must define at least 1 channel")

        total = budget_total if budget_total is not None else brief.budget
        if total <= 0:
            raise BudgetError("total_budget_brl must be > 0")

        budget = BudgetTracker.new(
            campaign_ref="pending",
            total_budget_brl=total,
        )

        roi = ROICalculation.new(
            campaign_ref="pending",
            projected_revenue_brl=total,
        )

        campaign = Campaign.new(
            campaign_name=brief.name,
            brief_ref=brief.id,
            channels=channels,
            budget=budget,
            roi=roi,
            metrics_plan={
                "target_metrics": [
                    {"metric_name": "total_likes", "target_min": 500, "unit": "count"},
                    {"metric_name": "total_comments", "target_min": 50, "unit": "count"},
                    {"metric_name": "total_saves", "target_min": 200, "unit": "count"},
                ]
            },
            deadline=brief.end_date if brief.end_date else None,
            tags=[brief.tone],
            dry_run=dry_run,
        )

        # Fix back-references after campaign_id is generated
        budget.campaign_ref = campaign.campaign_id
        roi.campaign_ref = campaign.campaign_id

        # Validate contract: transition draft → planned
        CampaignOrchestrator.transition_state(campaign, CampaignStatus.PLANNED)

        logger.info(
            "campaign.created",
            extra={"campaign_id": campaign.campaign_id, "status": campaign.status.value},
        )

        return campaign

    @staticmethod
    def allocate_budget(
        campaign: Campaign,
        total_budget_brl: float,
        breakdown: Optional[list[dict]] = None,
    ) -> BudgetTracker:
        """Allocate or reallocate budget for a campaign.

        Creates a new BudgetTracker, replacing the existing one if present.
        """
        if total_budget_brl <= 0:
            raise BudgetError("total_budget_brl must be > 0")

        if campaign.status == CampaignStatus.ARCHIVED:
            raise StateTransitionError("archived campaigns cannot be reopened")

        budget = BudgetTracker.new(
            campaign_ref=campaign.campaign_id,
            total_budget_brl=total_budget_brl,
            breakdown=breakdown,
        )

        campaign.budget = budget
        budget.updated_at = _now_iso()

        logger.info(
            "budget.allocated",
            extra={"campaign_id": campaign.campaign_id, "total": total_budget_brl},
        )

        return budget

    @staticmethod
    def calculate_roi(
        campaign: Campaign,
        metrics: Optional[MetricSummary] = None,
    ) -> ROICalculation:
        """Calculate ROI for a campaign, optionally incorporating actual metrics.

        With MetricSummary, populates actual_* fields.
        Without it, computes projected ROI only.
        """
        if campaign.budget is None:
            raise ROIError("cannot calculate ROI without budget")

        if metrics is not None and metrics.count == 0:
            raise ROIError("cannot calculate ROI without metrics")

        cost = campaign.budget.spent_brl if campaign.budget.spent_brl > 0 else campaign.budget.total_budget_brl
        revenue = campaign.roi.projected_revenue_brl if campaign.roi else campaign.budget.total_budget_brl

        roi = ROICalculation.new(
            campaign_ref=campaign.campaign_id,
            projected_revenue_brl=revenue,
            projected_cost_brl=cost,
        )

        if metrics is not None:
            roi.actual_revenue_brl = revenue
            roi.actual_cost_brl = cost
            if cost > 0:
                roi.actual_roi_percent = round((revenue - cost) / cost * 100, 2)
            roi.calculated_at = _now_iso()
            roi.notes = "ROI calculated from metrics summary"

        campaign.roi = roi

        logger.info(
            "roi.calculated",
            extra={
                "campaign_id": campaign.campaign_id,
                "projected_roi": roi.projected_roi_percent,
                "actual_roi": roi.actual_roi_percent,
            },
        )

        return roi

    @staticmethod
    def transition_state(
        campaign: Campaign,
        target: CampaignStatus,
    ) -> Campaign:
        """Transition a campaign to a new state with validation."""
        if campaign.status == CampaignStatus.ARCHIVED:
            raise StateTransitionError("archived campaigns cannot be reopened")

        campaign.transition_to(target)

        logger.info(
            "campaign.state_changed",
            extra={"campaign_id": campaign.campaign_id, "new_status": target.value},
        )

        return campaign

    @staticmethod
    def build_publish_queue_plan(campaign: Campaign) -> dict:
        """Build a publish queue plan from the campaign's channels.

        Uses topological sort (Kahn's algorithm with collections.deque)
        to order publish slots by channel priority.
        """
        if not campaign.channels:
            raise CampaignError("publish queue plan is empty")

        # Build DAG nodes from channels
        nodes: dict[str, dict] = {}
        edges: dict[str, list[str]] = {}

        for idx, channel in enumerate(campaign.channels):
            profile = channel.get("profile", f"unknown_{idx}")
            role = channel.get("role", "support")
            slot_count = channel.get("slot_count", 1)
            nodes[profile] = {
                "profile": profile,
                "role": role,
                "slot_count": slot_count,
            }
            edges[profile] = []

        # Primary channels must come before support channels (if any primary exists)
        primary_profiles = [p for p, n in nodes.items() if n["role"] == "primary_authority"]
        support_profiles = [p for p, n in nodes.items() if n["role"] != "primary_authority"]
        if primary_profiles:
            for sp in support_profiles:
                edges[sp] = []  # support nodes have no outgoing edges to primary
                for pp in primary_profiles:
                    if sp not in edges.get(pp, []):
                        edges.setdefault(pp, []).append(sp)

        # Kahn's algorithm with collections.deque (stdlib inline, no execution_graph import)
        in_degree: dict[str, int] = {n: 0 for n in nodes}
        for src, targets in edges.items():
            for tgt in targets:
                in_degree[tgt] = in_degree.get(tgt, 0) + 1

        queue: deque[str] = deque(n for n, d in in_degree.items() if d == 0)
        ordered: list[str] = []

        while queue:
            node = queue.popleft()
            ordered.append(node)
            for neighbor in edges.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered) != len(nodes):
            raise CampaignError("cycle detected in publish queue plan DAG")

        # Build plan items from ordered channels
        items: list[dict] = []
        for profile in ordered:
            node = nodes[profile]
            for slot_idx in range(node["slot_count"]):
                items.append(
                    {
                        "slot": slot_idx + 1,
                        "profile": node["profile"],
                        "role": node["role"],
                        "status": "planned",
                    }
                )

        plan = {
            "plan_id": _new_id("pqp_"),
            "campaign_ref": campaign.campaign_id,
            "items": items,
            "item_count": len(items),
            "channel_order": ordered,
            "dry_run": campaign.dry_run,
            "approval_required": campaign.approval_required,
            "generated_at": _now_iso(),
        }

        campaign.publish_queue_plan_ref = plan["plan_id"]

        logger.info(
            "publish_queue.built",
            extra={"campaign_id": campaign.campaign_id, "items": len(items)},
        )

        return plan

    @staticmethod
    def generate_manifest(campaign: Campaign) -> dict:
        """Generate a self-contained campaign manifest JSON.

        Output contract for P20 Supreme and other downstream consumers.
        """
        manifest = {
            "manifest_version": "1.0",
            "generated_by": "src/campaign_manager/",
            "campaign": campaign.to_dict(),
            "budget": campaign.budget.to_dict() if campaign.budget else None,
            "roi": campaign.roi.to_dict() if campaign.roi else None,
            "status": campaign.status.value,
            "checksum": None,
            "generated_at": _now_iso(),
        }

        # Deterministic checksum (SHA256 of JSON, sorted keys)
        raw = json.dumps(manifest, sort_keys=True, ensure_ascii=False, default=str)
        manifest["checksum"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        logger.info(
            "manifest.generated",
            extra={"campaign_id": campaign.campaign_id, "checksum": manifest["checksum"][:12]},
        )

        return manifest
