"""P9 Commercial SDR models — prospects, outreach sequences, opportunity scoring."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class LeadSource(str, Enum):
    INSTAGRAM = "instagram"
    REFERRAL = "referral"
    MANUAL_RESEARCH = "manual_research"
    INBOUND = "inbound"
    EVENT = "event"
    PARTNERSHIP = "partnership"


class OutreachChannel(str, Enum):
    EMAIL = "email"
    INSTAGRAM_DM = "instagram_dm"
    WHATSAPP = "whatsapp"
    LINKEDIN = "linkedin"
    PHONE = "phone"


class StepAction(str, Enum):
    RESEARCH = "research"
    CONNECT = "connect"
    INTRO_MESSAGE = "intro_message"
    VALUE_OFFER = "value_offer"
    FOLLOW_UP = "follow_up"
    PROPOSAL = "proposal"
    CLOSE_ASK = "close_ask"


class ScoreTier(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    DISQUALIFIED = "disqualified"


# ── helpers ──────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── Prospect Profile ─────────────────────────────────────────────────────────

@dataclass
class ProspectProfile:
    """Perfil de prospect B2B — hotel, restaurante, parceiro comercial."""
    profile_id: str
    company_name: str
    contact_name: str
    segment: str
    source: LeadSource
    instagram_handle: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    location: str = ""
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        company_name: str,
        contact_name: str,
        segment: str,
        source: LeadSource,
        instagram_handle: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        website: Optional[str] = None,
        location: str = "",
        notes: str = "",
        tags: Optional[list[str]] = None,
    ) -> "ProspectProfile":
        if not company_name.strip():
            raise ValueError("company_name nao pode ser vazio")
        if not contact_name.strip():
            raise ValueError("contact_name nao pode ser vazio")
        return cls(
            profile_id=_new_id("prospect"),
            company_name=company_name.strip(),
            contact_name=contact_name.strip(),
            segment=segment.strip(),
            source=source,
            instagram_handle=instagram_handle.strip() if instagram_handle else None,
            email=email.strip() if email else None,
            phone=phone.strip() if phone else None,
            website=website.strip() if website else None,
            location=location.strip(),
            notes=notes.strip(),
            tags=tags or [],
        )

    @property
    def has_instagram(self) -> bool:
        return self.instagram_handle is not None

    @property
    def has_email(self) -> bool:
        return self.email is not None

    @property
    def has_phone(self) -> bool:
        return self.phone is not None

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "company_name": self.company_name,
            "contact_name": self.contact_name,
            "segment": self.segment,
            "source": self.source.value,
            "instagram_handle": self.instagram_handle,
            "email": self.email,
            "phone": self.phone,
            "website": self.website,
            "location": self.location,
            "notes": self.notes,
            "tags": self.tags,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProspectProfile":
        source_raw = data.get("source", "manual_research")
        if isinstance(source_raw, str):
            data = {**data, "source": LeadSource(source_raw)}
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── SDR Message ──────────────────────────────────────────────────────────────

@dataclass
class SDRMessage:
    """Mensagem de outreach — template deterministico, nunca enviada."""
    message_id: str
    profile_id: str
    channel: OutreachChannel
    subject: str
    body: str
    call_to_action: str = ""
    approval_required: bool = True
    sent: bool = False
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        profile_id: str,
        channel: OutreachChannel,
        subject: str,
        body: str,
        call_to_action: str = "",
        approval_required: bool = True,
    ) -> "SDRMessage":
        if not body.strip():
            raise ValueError("body nao pode ser vazio")
        return cls(
            message_id=_new_id("msg"),
            profile_id=profile_id,
            channel=channel,
            subject=subject.strip(),
            body=body.strip(),
            call_to_action=call_to_action.strip(),
            approval_required=approval_required,
        )

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "profile_id": self.profile_id,
            "channel": self.channel.value,
            "subject": self.subject,
            "body": self.body,
            "call_to_action": self.call_to_action,
            "approval_required": self.approval_required,
            "sent": self.sent,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SDRMessage":
        channel_raw = data.get("channel", "email")
        if isinstance(channel_raw, str):
            data = {**data, "channel": OutreachChannel(channel_raw)}
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Outreach Step ────────────────────────────────────────────────────────────

@dataclass
class OutreachStep:
    """Passo individual em uma sequencia de outreach."""
    step_id: str
    sequence_id: str
    step_number: int
    action: StepAction
    channel: OutreachChannel
    message: Optional[SDRMessage] = None
    delay_days: int = 0
    requires_approval: bool = True
    completed: bool = False
    notes: str = ""
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        sequence_id: str,
        step_number: int,
        action: StepAction,
        channel: OutreachChannel,
        message: Optional[SDRMessage] = None,
        delay_days: int = 0,
        requires_approval: bool = True,
        notes: str = "",
    ) -> "OutreachStep":
        if step_number < 1:
            raise ValueError("step_number deve ser >= 1")
        if delay_days < 0:
            raise ValueError("delay_days nao pode ser negativo")
        return cls(
            step_id=_new_id("step"),
            sequence_id=sequence_id,
            step_number=step_number,
            action=action,
            channel=channel,
            message=message,
            delay_days=delay_days,
            requires_approval=requires_approval,
            notes=notes.strip(),
        )

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "sequence_id": self.sequence_id,
            "step_number": self.step_number,
            "action": self.action.value,
            "channel": self.channel.value,
            "message": self.message.to_dict() if self.message else None,
            "delay_days": self.delay_days,
            "requires_approval": self.requires_approval,
            "completed": self.completed,
            "notes": self.notes,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OutreachStep":
        action_raw = data.get("action", "research")
        channel_raw = data.get("channel", "email")
        msg_data = data.pop("message", None)
        if isinstance(action_raw, str):
            data["action"] = StepAction(action_raw)
        if isinstance(channel_raw, str):
            data["channel"] = OutreachChannel(channel_raw)
        step = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        if msg_data:
            step.message = SDRMessage.from_dict(msg_data)
        return step


# ── Outreach Sequence ────────────────────────────────────────────────────────

@dataclass
class OutreachSequence:
    """Sequencia completa de outreach para um prospect."""
    sequence_id: str
    profile_id: str
    steps: list[OutreachStep] = field(default_factory=list)
    status: str = "draft"
    dry_run: bool = True
    risk_flags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(cls, profile_id: str) -> "OutreachSequence":
        return cls(
            sequence_id=_new_id("seq"),
            profile_id=profile_id,
            risk_flags=["dry_run_active", "no_real_delivery", "approval_gated"],
        )

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    @property
    def total_delay_days(self) -> int:
        return sum(s.delay_days for s in self.steps)

    @property
    def pending_approvals(self) -> int:
        return sum(1 for s in self.steps if s.requires_approval and not s.completed)

    def to_dict(self) -> dict:
        return {
            "sequence_id": self.sequence_id,
            "profile_id": self.profile_id,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status,
            "dry_run": self.dry_run,
            "risk_flags": self.risk_flags,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OutreachSequence":
        steps_data = data.pop("steps", [])
        seq = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        seq.steps = [OutreachStep.from_dict(s) for s in steps_data]
        return seq


# ── Opportunity Score ────────────────────────────────────────────────────────

@dataclass
class OpportunityScore:
    """Classificacao de oportunidade — score composto deterministico."""
    score_id: str
    profile_id: str
    segment_fit: float
    engagement_signal: float
    budget_indicator: float
    urgency: float
    composite: float
    tier: ScoreTier
    reasoning: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)

    @classmethod
    def new(
        cls,
        profile_id: str,
        segment_fit: float,
        engagement_signal: float,
        budget_indicator: float,
        urgency: float,
        reasoning: Optional[list[str]] = None,
    ) -> "OpportunityScore":
        for val, name in [
            (segment_fit, "segment_fit"),
            (engagement_signal, "engagement_signal"),
            (budget_indicator, "budget_indicator"),
            (urgency, "urgency"),
        ]:
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{name} deve estar entre 0.0 e 1.0, recebeu {val}")

        composite = (segment_fit * 0.35 + engagement_signal * 0.25 +
                     budget_indicator * 0.25 + urgency * 0.15)

        if composite >= 0.70:
            tier = ScoreTier.HOT
        elif composite >= 0.40:
            tier = ScoreTier.WARM
        elif composite >= 0.15:
            tier = ScoreTier.COLD
        else:
            tier = ScoreTier.DISQUALIFIED

        return cls(
            score_id=_new_id("score"),
            profile_id=profile_id,
            segment_fit=segment_fit,
            engagement_signal=engagement_signal,
            budget_indicator=budget_indicator,
            urgency=urgency,
            composite=round(composite, 4),
            tier=tier,
            reasoning=reasoning or [],
        )

    @property
    def is_pursuable(self) -> bool:
        return self.tier in (ScoreTier.HOT, ScoreTier.WARM)

    def to_dict(self) -> dict:
        return {
            "score_id": self.score_id,
            "profile_id": self.profile_id,
            "segment_fit": self.segment_fit,
            "engagement_signal": self.engagement_signal,
            "budget_indicator": self.budget_indicator,
            "urgency": self.urgency,
            "composite": self.composite,
            "tier": self.tier.value,
            "reasoning": self.reasoning,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OpportunityScore":
        tier_raw = data.get("tier", "cold")
        if isinstance(tier_raw, str):
            data = {**data, "tier": ScoreTier(tier_raw)}
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── SDR Plan ─────────────────────────────────────────────────────────────────

@dataclass
class SDRPlan:
    """Plano SDR completo — prospeccao, scoring e sequencia."""
    plan_id: str
    title: str
    description: str
    prospects: list[ProspectProfile] = field(default_factory=list)
    scores: list[OpportunityScore] = field(default_factory=list)
    sequences: list[OutreachSequence] = field(default_factory=list)
    status: str = "draft"
    dry_run: bool = True
    risk_flags: list[str] = field(default_factory=list)
    safety_rules: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    finalized_at: Optional[str] = None

    @classmethod
    def new(cls, title: str, description: str) -> "SDRPlan":
        return cls(
            plan_id=_new_id("plan"),
            title=title.strip(),
            description=description.strip(),
            risk_flags=[
                "all_messages_dry_run",
                "approval_required_for_external_send",
                "no_real_delivery",
            ],
            safety_rules=[
                "no_real_message_sending",
                "no_external_api_calls",
                "human_approval_for_all_outreach",
                "deterministic_scoring_only",
            ],
        )

    @property
    def total_prospects(self) -> int:
        return len(self.prospects)

    @property
    def hot_count(self) -> int:
        return sum(1 for s in self.scores if s.tier == ScoreTier.HOT)

    @property
    def warm_count(self) -> int:
        return sum(1 for s in self.scores if s.tier == ScoreTier.WARM)

    @property
    def pursuable_count(self) -> int:
        return self.hot_count + self.warm_count

    def add_prospect(self, prospect: ProspectProfile) -> None:
        self.prospects.append(prospect)

    def add_score(self, score: OpportunityScore) -> None:
        self.scores.append(score)

    def add_sequence(self, sequence: OutreachSequence) -> None:
        self.sequences.append(sequence)

    def finalize(self) -> None:
        self.status = "final"
        self.finalized_at = _now_iso()

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "title": self.title,
            "description": self.description,
            "prospects": [p.to_dict() for p in self.prospects],
            "scores": [s.to_dict() for s in self.scores],
            "sequences": [s.to_dict() for s in self.sequences],
            "status": self.status,
            "dry_run": self.dry_run,
            "risk_flags": self.risk_flags,
            "safety_rules": self.safety_rules,
            "created_at": self.created_at,
            "finalized_at": self.finalized_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SDRPlan":
        prospects_data = data.pop("prospects", [])
        scores_data = data.pop("scores", [])
        sequences_data = data.pop("sequences", [])
        plan = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        plan.prospects = [ProspectProfile.from_dict(p) for p in prospects_data]
        plan.scores = [OpportunityScore.from_dict(s) for s in scores_data]
        plan.sequences = [OutreachSequence.from_dict(s) for s in sequences_data]
        return plan
