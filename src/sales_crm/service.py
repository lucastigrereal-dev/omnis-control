"""P10 Sales/CRM — deterministic services (zero LLM, zero network, zero DB)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.sales_crm.errors import (
    ExternalContactBlockedError,
    InvalidDealError,
    InvalidFollowUpError,
    InvalidLeadError,
    InvalidObjectionError,
    InvalidPipelineError,
)
from src.sales_crm.models import (
    VALID_PACKAGES,
    ActivityType,
    Deal,
    DealPriority,
    FollowUpStatus,
    FollowUpTask,
    Lead,
    LeadSource,
    LeadStatus,
    ObjectionCategory,
    ObjectionRecord,
    PipelineStage,
    ProposalRecord,
    ProposalStatus,
    SalesActivity,
    SalesPipeline,
    _now_iso,
)


# ═══════════════════════════════════════════════════════════════
# PipelineSummary
# ═══════════════════════════════════════════════════════════════

@dataclass
class PipelineSummary:
    """Aggregated snapshot of the pipeline state."""

    pipeline_id: str
    pipeline_name: str
    total_deals: int
    active_deals: int
    total_value: float
    weighted_value: float
    won_deals: int
    won_value: float
    lost_deals: int
    lost_value: float
    stage_breakdown: dict[str, dict[str, Any]] = field(default_factory=dict)
    risks: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "pipeline_name": self.pipeline_name,
            "total_deals": self.total_deals,
            "active_deals": self.active_deals,
            "total_value": self.total_value,
            "weighted_value": self.weighted_value,
            "won_deals": self.won_deals,
            "won_value": self.won_value,
            "lost_deals": self.lost_deals,
            "lost_value": self.lost_value,
            "stage_breakdown": self.stage_breakdown,
            "risks": self.risks,
            "generated_at": self.generated_at,
        }


# ═══════════════════════════════════════════════════════════════
# ValidationResult
# ═══════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    """Result of a pipeline validation operation."""

    valid: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.valid and len(self.issues) == 0

    @classmethod
    def success(cls, warnings: list[str] | None = None) -> ValidationResult:
        return cls(valid=True, warnings=warnings or [])

    @classmethod
    def failure(cls, issues: list[str]) -> ValidationResult:
        return cls(valid=False, issues=issues)


# ═══════════════════════════════════════════════════════════════
# ScoreResult
# ═══════════════════════════════════════════════════════════════

@dataclass
class ScoreResult:
    """Result of a lead scoring operation."""

    lead_id: str
    score: float
    breakdown: dict[str, float] = field(default_factory=dict)
    qualifies: bool = False
    recommended_package: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "score": self.score,
            "breakdown": self.breakdown,
            "qualifies": self.qualifies,
            "recommended_package": self.recommended_package,
            "notes": self.notes,
        }


# ═══════════════════════════════════════════════════════════════
# SalesCRMPlanner
# ═══════════════════════════════════════════════════════════════

class SalesCRMPlanner:
    """Deterministic Sales/CRM planner — dry-run by default.

    Plans leads, deals, follow-ups, objections, proposals, and pipeline.
    Zero LLM. Zero network. Zero database. Zero real contact.
    """

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self._leads: dict[str, Lead] = {}
        self._deals: dict[str, Deal] = {}
        self._activities: list[SalesActivity] = []
        self._objections: list[ObjectionRecord] = []
        self._proposals: list[ProposalRecord] = []
        self._follow_ups: list[FollowUpTask] = []

    # ── Lead management ───────────────────────────────────────

    def create_lead(
        self,
        name: str,
        source: LeadSource = LeadSource.UNKNOWN,
        business_name: str | None = None,
        contact_phone: str | None = None,
        contact_email: str | None = None,
        instagram_handle: str | None = None,
        city: str | None = None,
        state: str | None = None,
        niche: str | None = None,
        follower_count: int | None = None,
        notes: str | None = None,
        tags: list[str] | None = None,
    ) -> Lead:
        lead = Lead.new(
            name=name,
            source=source,
            business_name=business_name,
            contact_phone=contact_phone,
            contact_email=contact_email,
            instagram_handle=instagram_handle,
            city=city,
            state=state,
            niche=niche,
            follower_count=follower_count,
            notes=notes,
            tags=tags,
        )
        self._leads[lead.id] = lead
        return lead

    # ── Lead scoring ──────────────────────────────────────────

    def score_lead(
        self,
        lead_id: str,
        qualification_threshold: float = 50.0,
    ) -> ScoreResult:
        lead = self._leads.get(lead_id)
        if lead is None:
            raise InvalidLeadError(f"Lead not found: {lead_id}")

        breakdown: dict[str, float] = {}
        notes: list[str] = []

        # Contact info availability (max 20)
        contact_score = 0.0
        if lead.contact_phone:
            contact_score += 10.0
            breakdown["has_phone"] = 10.0
        if lead.contact_email:
            contact_score += 5.0
            breakdown["has_email"] = 5.0
        if lead.instagram_handle:
            contact_score += 5.0
            breakdown["has_instagram"] = 5.0
        breakdown["contact_info"] = contact_score

        # Follower count signal (max 20)
        follower_score = 0.0
        if lead.follower_count:
            if lead.follower_count >= 100_000:
                follower_score = 20.0
                notes.append("High-authority account (100K+ followers)")
            elif lead.follower_count >= 10_000:
                follower_score = 15.0
                notes.append("Established account (10K+ followers)")
            elif lead.follower_count >= 1_000:
                follower_score = 10.0
                notes.append("Growing account (1K+ followers)")
            else:
                follower_score = 5.0
        else:
            notes.append("No follower data — lower confidence")
        breakdown["follower_signal"] = follower_score

        # Location data (max 15)
        location_score = 0.0
        if lead.city and lead.state:
            location_score = 15.0
        elif lead.city:
            location_score = 10.0
        elif lead.state:
            location_score = 5.0
        else:
            notes.append("No location data")
        breakdown["location"] = location_score

        # Niche fit (max 15)
        niche_score = 0.0
        tourism_niches = {"hotel", "restaurante", "pousada", "turismo",
                          "gastronomia", "viagem", "resort", "praia"}
        if lead.niche:
            if lead.niche.lower() in tourism_niches:
                niche_score = 15.0
                notes.append(f"Niche match: {lead.niche}")
            else:
                niche_score = 5.0
                notes.append(f"Niche '{lead.niche}' is not core tourism — lower fit")
        else:
            notes.append("No niche data")
        breakdown["niche_fit"] = niche_score

        # Business name (max 10)
        biz_score = 10.0 if lead.business_name else 0.0
        breakdown["has_business_name"] = biz_score

        # Contactability (max 20) — bonus for multiple channels
        channels = sum(1 for x in [lead.contact_phone, lead.contact_email,
                                   lead.instagram_handle] if x)
        channel_score = min(channels * 6.67, 20.0)
        breakdown["contact_channels"] = round(channel_score, 2)

        total = round(sum(breakdown.values()), 2)
        qualifies = total >= qualification_threshold

        # Recommended package based on score
        if total >= 80:
            recommended = "premium"
        elif total >= 60:
            recommended = "growth"
        elif total >= 40:
            recommended = "starter"
        else:
            recommended = None

        lead.score = total
        lead.updated_at = _now_iso()

        return ScoreResult(
            lead_id=lead_id,
            score=total,
            breakdown=breakdown,
            qualifies=qualifies,
            recommended_package=recommended,
            notes=notes,
        )

    # ── Deal management ───────────────────────────────────────

    def create_deal(
        self,
        lead_id: str,
        package: str = "growth",
        stage: PipelineStage = PipelineStage.PROSPECTING,
        priority: DealPriority = DealPriority.MEDIUM,
        probability: float | None = None,
        expected_close_date: str | None = None,
        tags: list[str] | None = None,
        notes: str | None = None,
    ) -> Deal:
        if lead_id not in self._leads:
            raise InvalidDealError(f"Lead not found: {lead_id}")
        deal = Deal.new(
            lead_id=lead_id,
            package=package,
            stage=stage,
            priority=priority,
            probability=probability,
            expected_close_date=expected_close_date,
            tags=tags,
            notes=notes,
        )
        self._deals[deal.id] = deal

        # Auto-advance lead status if creating a deal
        lead = self._leads[lead_id]
        if lead.status == LeadStatus.NEW:
            lead.status = LeadStatus.QUALIFIED
            lead.updated_at = _now_iso()

        return deal

    def advance_deal(self, deal_id: str, new_stage: PipelineStage) -> Deal:
        deal = self._deals.get(deal_id)
        if deal is None:
            raise InvalidDealError(f"Deal not found: {deal_id}")
        deal.stage = new_stage
        deal.probability = Deal._default_probability(new_stage)
        deal.updated_at = _now_iso()
        return deal

    # ── Activity logging (all dry-run) ─────────────────────────

    def log_activity(
        self,
        activity_type: ActivityType,
        description: str,
        lead_id: str | None = None,
        deal_id: str | None = None,
        outcome: str | None = None,
    ) -> SalesActivity:
        if activity_type in {ActivityType.CALL, ActivityType.WHATSAPP,
                             ActivityType.EMAIL, ActivityType.DM}:
            raise ExternalContactBlockedError(
                f"External contact via {activity_type.value} is blocked. "
                "Set approval_required=True and obtain approval before real contact."
            )
        activity = SalesActivity.new(
            activity_type=activity_type,
            description=description,
            lead_id=lead_id,
            deal_id=deal_id,
            outcome=outcome,
        )
        self._activities.append(activity)
        return activity

    # ── Objection recording ────────────────────────────────────

    def record_objection(
        self,
        category: ObjectionCategory,
        description: str,
        lead_id: str | None = None,
        deal_id: str | None = None,
        response: str | None = None,
    ) -> ObjectionRecord:
        if lead_id and lead_id not in self._leads:
            raise InvalidObjectionError(f"Lead not found: {lead_id}")
        if deal_id and deal_id not in self._deals:
            raise InvalidObjectionError(f"Deal not found: {deal_id}")
        record = ObjectionRecord.new(
            category=category,
            description=description,
            lead_id=lead_id,
            deal_id=deal_id,
            response=response,
        )
        self._objections.append(record)
        return record

    # ── Follow-up planning ─────────────────────────────────────

    def plan_follow_up(
        self,
        description: str,
        scheduled_at: str,
        lead_id: str | None = None,
        deal_id: str | None = None,
        notes: str | None = None,
    ) -> FollowUpTask:
        if lead_id and lead_id not in self._leads:
            raise InvalidFollowUpError(f"Lead not found: {lead_id}")
        if deal_id and deal_id not in self._deals:
            raise InvalidFollowUpError(f"Deal not found: {deal_id}")
        task = FollowUpTask.new(
            description=description,
            scheduled_at=scheduled_at,
            lead_id=lead_id,
            deal_id=deal_id,
            notes=notes,
        )
        self._follow_ups.append(task)
        return task

    # ── Proposal management ────────────────────────────────────

    def create_proposal(
        self,
        package: str,
        lead_id: str | None = None,
        deal_id: str | None = None,
        content_summary: str | None = None,
        valid_until: str | None = None,
    ) -> ProposalRecord:
        if lead_id and lead_id not in self._leads:
            raise InvalidDealError(f"Lead not found: {lead_id}")
        proposal = ProposalRecord.new(
            package=package,
            lead_id=lead_id,
            deal_id=deal_id,
            content_summary=content_summary,
            valid_until=valid_until,
        )
        self._proposals.append(proposal)
        return proposal

    # ── Pipeline summary ───────────────────────────────────────

    def build_pipeline_summary(self, pipeline: SalesPipeline) -> PipelineSummary:
        stage_breakdown: dict[str, dict[str, Any]] = {}
        for stage in PipelineStage:
            count = pipeline.count_by_stage(stage)
            value = pipeline.value_by_stage(stage)
            if count > 0:
                stage_breakdown[stage.value] = {
                    "count": count,
                    "value_brl": value,
                }

        risks: list[str] = []
        if pipeline.active_count == 0 and pipeline.deal_count > 0:
            risks.append("No active deals — all in terminal stages.")
        if pipeline.total_value == 0:
            risks.append("Pipeline has zero total value.")
        # Check for deals stuck in prospecting
        stuck_count = pipeline.count_by_stage(PipelineStage.PROSPECTING)
        if stuck_count > 5:
            risks.append(f"{stuck_count} deals stuck in prospecting — review needed.")

        return PipelineSummary(
            pipeline_id=pipeline.id,
            pipeline_name=pipeline.name,
            total_deals=pipeline.deal_count,
            active_deals=pipeline.active_count,
            total_value=pipeline.total_value,
            weighted_value=pipeline.weighted_value,
            won_deals=pipeline.count_by_stage(PipelineStage.CLOSED_WON),
            won_value=pipeline.value_by_stage(PipelineStage.CLOSED_WON),
            lost_deals=pipeline.count_by_stage(PipelineStage.CLOSED_LOST),
            lost_value=pipeline.value_by_stage(PipelineStage.CLOSED_LOST),
            stage_breakdown=stage_breakdown,
            risks=risks,
        )

    # ── Pipeline validation ────────────────────────────────────

    def validate_pipeline(self, pipeline: SalesPipeline) -> ValidationResult:
        issues: list[str] = []
        warnings: list[str] = []

        if not pipeline.deals:
            warnings.append("Pipeline has no deals.")

        # Check all deals reference known leads
        for deal in pipeline.deals:
            if deal.lead_id not in self._leads:
                issues.append(
                    f"Deal {deal.id} references unknown lead_id '{deal.lead_id}'."
                )

        # Check for duplicate deals on same lead (active)
        active_lead_ids: set[str] = set()
        for deal in pipeline.active_deals:
            if deal.lead_id in active_lead_ids:
                warnings.append(
                    f"Lead {deal.lead_id} has multiple active deals."
                )
            active_lead_ids.add(deal.lead_id)

        # Check probability consistency
        for deal in pipeline.deals:
            expected = Deal._default_probability(deal.stage)
            if abs(deal.probability - expected) > 0.01:
                warnings.append(
                    f"Deal {deal.id} probability {deal.probability} "
                    f"does not match stage default {expected}."
                )

        if issues:
            return ValidationResult.failure(issues)
        if warnings:
            return ValidationResult.success(warnings)
        return ValidationResult.success()

    # ── Inventory ──────────────────────────────────────────────

    def list_leads(self) -> list[Lead]:
        return list(self._leads.values())

    def list_deals(self) -> list[Deal]:
        return list(self._deals.values())

    def list_activities(self) -> list[SalesActivity]:
        return list(self._activities)

    def list_objections(self) -> list[ObjectionRecord]:
        return list(self._objections)

    def list_follow_ups(self) -> list[FollowUpTask]:
        return list(self._follow_ups)

    def list_proposals(self) -> list[ProposalRecord]:
        return list(self._proposals)

    @property
    def lead_count(self) -> int:
        return len(self._leads)

    @property
    def deal_count(self) -> int:
        return len(self._deals)
