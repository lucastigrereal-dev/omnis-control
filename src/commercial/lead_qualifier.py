"""W124 — Lead Qualifier BANT for HotelLead qualification.

Deterministic BANT scoring: Budget, Authority, Need, Timing.
Each dimension 0-25, total 0-100. Qualification tiers with explicit reasoning.
Zero external API, dry-run only, all data from HotelLead fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path

from src.commercial.hotel_lead import HotelLead


# ── Qualification Tiers ────────────────────────────────────────────────────

QUALIFIED = "qualified"
NURTURE = "nurture"
LOW_FIT = "low_fit"
DISQUALIFIED = "disqualified"
MISSING_INFO = "missing_information"

QUALIFICATION_TIERS = frozenset({QUALIFIED, NURTURE, LOW_FIT, DISQUALIFIED, MISSING_INFO})

TIER_THRESHOLDS = {
    QUALIFIED: 70,
    NURTURE: 45,
    LOW_FIT: 20,
    DISQUALIFIED: 0,
}

TIER_NEXT_ACTIONS = {
    QUALIFIED: "Avancar para proposta/brief comercial — lead pronto para outreach",
    NURTURE: "Seguir cadencia de relacionamento — nutrir com conteudo antes de propor",
    LOW_FIT: "Manter em lista fria — revisitar em 90 dias ou se houver novo sinal",
    DISQUALIFIED: "Nao priorizar — fora do perfil ou sem potencial comercial",
    MISSING_INFO: "Coletar dados antes de decidir — completar campos faltantes do HotelLead",
}


# ── Budget Scoring ─────────────────────────────────────────────────────────

def _score_budget(hl: HotelLead) -> dict:
    """Score budget dimension (0-25) from hotel_tier and ADR placeholder.

    Premium tier suggests higher budget. ADR placeholder adds granularity.
    """
    reasons: list[str] = []
    risks: list[str] = []
    missing: list[str] = []

    score = 0

    # hotel_tier is the primary budget signal
    tier = hl.hotel_tier
    if tier == "Premium":
        score += 18
        reasons.append(f"Hotel tier Premium — indica orcamento comercial elevado")
    elif tier == "Growth":
        score += 12
        reasons.append(f"Hotel tier Growth — orcamento comercial moderado")
    elif tier == "Starter":
        score += 6
        reasons.append(f"Hotel tier Starter — orcamento comercial basico (R$350 entry)")
    else:
        missing.append("hotel_tier")

    # ADR placeholder refines budget estimate
    adr = hl.average_daily_rate_placeholder
    if adr >= 800:
        score += 5
        reasons.append(f"ADR placeholder R${adr:.0f} — diaria alta, budget consistente")
    elif adr >= 400:
        score += 3
        reasons.append(f"ADR placeholder R${adr:.0f} — diaria media")
    elif adr > 0:
        score += 1
        reasons.append(f"ADR placeholder R${adr:.0f} — diaria baixa")

    # room count as secondary signal
    rooms = hl.room_count_placeholder
    if rooms >= 50:
        score += 2
        reasons.append(f"{rooms} quartos — escala comercial significativa")
    elif rooms > 0:
        score += 1

    score = min(score, 25)

    if score < 8:
        risks.append("Orcamento comercial baixo — risco de objecao por preco")
    if not adr:
        missing.append("average_daily_rate_placeholder")
    if not rooms:
        missing.append("room_count_placeholder")

    return {
        "dimension": "budget",
        "score": score,
        "max": 25,
        "reasons": reasons,
        "risks": risks,
        "missing": missing,
    }


# ── Authority Scoring ──────────────────────────────────────────────────────

def _score_authority(hl: HotelLead) -> dict:
    """Score authority dimension (0-25) from decision maker fields and channel.

    Named decision maker with clear role = strong authority signal.
    Contact channel availability adds confidence.
    """
    reasons: list[str] = []
    risks: list[str] = []
    missing: list[str] = []

    score = 0
    dm_name = hl.decision_maker_name.strip()
    dm_role = hl.decision_maker_role.strip().lower()

    # Decision maker presence
    if dm_name:
        score += 10
        reasons.append(f"Decisor identificado: {dm_name}")

        # Role clarity
        high_authority_roles = {"proprietario", "proprietaria", "dono", "dona",
                                 "ceo", "diretor", "diretor(a)", "director",
                                 "gerente geral", "general manager", "socio", "socia"}
        medium_authority_roles = {"gerente", "gerente de marketing",
                                   "coordenador", "coordenador(a)",
                                   "supervisor", "supervisor(a)", "head"}
        low_authority_roles = {"assistente", "analista", "recepcionista",
                                "reservas", "comercial", "vendas", "marketing"}

        if dm_role in high_authority_roles:
            score += 10
            reasons.append(f"Cargo de alta autoridade: {hl.decision_maker_role}")
        elif dm_role in medium_authority_roles:
            score += 7
            reasons.append(f"Cargo de autoridade media: {hl.decision_maker_role}")
        elif dm_role in low_authority_roles:
            score += 3
            reasons.append(f"Cargo operacional: {hl.decision_maker_role} — pode precisar escalar")
            risks.append("Contato operacional — necessario identificar decisor final")
        elif dm_role:
            score += 5  # Has role but not categorized
            reasons.append(f"Cargo: {hl.decision_maker_role}")
        else:
            missing.append("decision_maker_role")
            risks.append("Cargo do decisor nao informado — autoridade incerta")
    else:
        missing.append("decision_maker_name")
        missing.append("decision_maker_role")
        risks.append("Sem decisor identificado — necessario descobrir quem decide")

    # Contact channel bonus
    channel = hl.base_lead.contact_channel
    if channel in ("whatsapp", "telegram"):
        score += 3
        reasons.append(f"Canal direto disponivel: {channel}")
    elif channel in ("instagram", "email"):
        score += 2
        reasons.append(f"Canal de contato: {channel}")
    elif channel:
        score += 1
        reasons.append(f"Canal: {channel}")
    else:
        missing.append("contact_channel")

    score = min(score, 25)

    if score < 8:
        risks.append("Autoridade decisoria fraca — alto risco de falta de poder de decisao")

    return {
        "dimension": "authority",
        "score": score,
        "max": 25,
        "reasons": reasons,
        "risks": risks,
        "missing": missing,
    }


# ── Need Scoring ───────────────────────────────────────────────────────────

def _score_need(hl: HotelLead) -> dict:
    """Score need dimension (0-25) from fit_score, niche, and interest.

    High fit_score + aligned niche = strong need for tourism marketing.
    Explicit interest in package/collab signals active need.
    """
    reasons: list[str] = []
    risks: list[str] = []
    missing: list[str] = []

    score = 0

    # fit_score is the primary need signal
    fs = hl.fit_score
    if fs >= 80:
        score += 12
        reasons.append(f"Fit score alto ({fs}/100) — forte alinhamento com midia de viagem")
    elif fs >= 50:
        score += 7
        reasons.append(f"Fit score medio ({fs}/100)")
    elif fs > 0:
        score += 3
        reasons.append(f"Fit score baixo ({fs}/100)")
    else:
        missing.append("fit_score")

    # Niche indicates need type
    high_need_niches = {"resort", "pousada", "boutique", "eco_resort", "fazenda"}
    medium_need_niches = {"hotel", "apart_hotel", "glamping"}
    low_need_niches = {"urbano", "hostel"}

    niche = hl.niche
    if niche in high_need_niches:
        score += 8
        reasons.append(f"Niche '{niche}' — alta necessidade de marketing experiencial")
    elif niche in medium_need_niches:
        score += 5
        reasons.append(f"Niche '{niche}' — necessidade moderada de promocao")
    elif niche in low_need_niches:
        score += 2
        reasons.append(f"Niche '{niche}' — necessidade de marketing mais transacional")

    # Interest signals active need
    interest = hl.base_lead.interest
    high_need_interests = {"pacote", "collab"}
    medium_need_interests = {"publi", "permuta"}

    if interest in high_need_interests:
        score += 5
        reasons.append(f"Interesse em '{interest}' — necessidade ativa de parceria")
    elif interest in medium_need_interests:
        score += 3
        reasons.append(f"Interesse em '{interest}' — abertura para parceria")
    elif interest:
        score += 1
    else:
        missing.append("interest (base_lead)")

    # Region bonus — nordeste is core market
    region = hl.region.lower()
    if region == "nordeste":
        score += 2
        reasons.append("Regiao Nordeste — mercado core da operacao")
    elif region in ("sudeste", "sul"):
        score += 1
        reasons.append(f"Regiao {region} — mercado de expansao")

    score = min(score, 27)  # Allow small overshoot then cap
    score = min(score, 25)

    if score < 8:
        risks.append("Necessidade de marketing nao evidenciada — lead pode nao ver valor")

    return {
        "dimension": "need",
        "score": score,
        "max": 25,
        "reasons": reasons,
        "risks": risks,
        "missing": missing,
    }


# ── Timing Scoring ─────────────────────────────────────────────────────────

def _score_timing(hl: HotelLead) -> dict:
    """Score timing dimension (0-25) from priority_tier and source.

    Hot priority = active window. Source via referral/inbound = warmer timing.
    Season/tags can add urgency signals.
    """
    reasons: list[str] = []
    risks: list[str] = []
    missing: list[str] = []

    score = 0

    # priority_tier is the primary timing signal
    pt = hl.priority_tier
    if pt == "hot":
        score += 18
        reasons.append("Priority 'hot' — janela de oportunidade ativa, agir rapido")
    elif pt == "warm":
        score += 12
        reasons.append("Priority 'warm' — timing moderado, sem urgencia critica")
    elif pt == "cold":
        score += 5
        reasons.append("Priority 'cold' — sem janela de oportunidade detectada")
    elif pt == "disqualified":
        score += 0
        reasons.append("Priority 'disqualified' — sem timing viavel")
    else:
        missing.append("priority_tier")

    # Source indicates timing warmth
    source = hl.base_lead.source
    hot_sources = {"indicacao", "evento"}
    warm_sources = {"instagram", "site"}
    cold_sources = {"prospeccao", "outro"}

    if source in hot_sources:
        score += 4
        reasons.append(f"Source '{source}' — lead quente, veio por confianca")
    elif source in warm_sources:
        score += 3
        reasons.append(f"Source '{source}' — interesse inbound detectado")
    elif source in cold_sources:
        score += 1
        reasons.append(f"Source '{source}' — prospeccao fria")
    elif source:
        score += 2

    # Tags with urgency keywords
    urgency_keywords = {"urgente", "agora", "quente", "hoje", "rapido", "oportunidade",
                         "alta_temporada", "ferias", "verao", "reveillon", "carnaval"}
    base_tags = set(t.lower() for t in hl.base_lead.tags)
    matches = urgency_keywords & base_tags
    if matches:
        score += 3
        reasons.append(f"Tags de urgencia: {', '.join(sorted(matches))}")

    score = min(score, 25)

    if score < 5:
        risks.append("Sem urgencia — lead pode esfriar antes do fechamento")

    return {
        "dimension": "timing",
        "score": score,
        "max": 25,
        "reasons": reasons,
        "risks": risks,
        "missing": missing,
    }


# ── Qualification Result ───────────────────────────────────────────────────

def _determine_tier(total: int, missing_count: int) -> str:
    """Determine qualification tier from total score and missing info count.

    If 3+ dimensions have missing critical info → MISSING_INFO regardless of score.
    Otherwise use score thresholds.
    """
    if missing_count >= 3:
        return MISSING_INFO
    if total >= 70:
        return QUALIFIED
    if total >= 45:
        return NURTURE
    if total >= 20:
        return LOW_FIT
    return DISQUALIFIED


@dataclass
class BANTResult:
    """Full BANT qualification result for a HotelLead."""

    qualifier_id: str
    hotel_lead_id: str
    hotel_name: str
    budget_score: int
    authority_score: int
    need_score: int
    timing_score: int
    total_score: int
    qualification_tier: str
    reasons: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    recommended_next_action: str = ""
    dimension_details: dict = field(default_factory=dict)
    dry_run: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def is_actionable(self) -> bool:
        return self.qualification_tier in (QUALIFIED, NURTURE)

    @property
    def max_score(self) -> int:
        return 100

    def to_dict(self) -> dict:
        return {
            "qualifier_id": self.qualifier_id,
            "hotel_lead_id": self.hotel_lead_id,
            "hotel_name": self.hotel_name,
            "budget_score": self.budget_score,
            "authority_score": self.authority_score,
            "need_score": self.need_score,
            "timing_score": self.timing_score,
            "total_score": self.total_score,
            "qualification_tier": self.qualification_tier,
            "reasons": self.reasons,
            "risks": self.risks,
            "missing_information": self.missing_information,
            "recommended_next_action": self.recommended_next_action,
            "dimension_details": self.dimension_details,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BANTResult":
        return cls(
            qualifier_id=d["qualifier_id"],
            hotel_lead_id=d.get("hotel_lead_id", ""),
            hotel_name=d.get("hotel_name", ""),
            budget_score=d.get("budget_score", 0),
            authority_score=d.get("authority_score", 0),
            need_score=d.get("need_score", 0),
            timing_score=d.get("timing_score", 0),
            total_score=d.get("total_score", 0),
            qualification_tier=d.get("qualification_tier", MISSING_INFO),
            reasons=d.get("reasons", []),
            risks=d.get("risks", []),
            missing_information=d.get("missing_information", []),
            recommended_next_action=d.get("recommended_next_action", ""),
            dimension_details=d.get("dimension_details", {}),
            dry_run=d.get("dry_run", True),
            created_at=d.get("created_at", ""),
        )

    def to_markdown(self) -> str:
        scores = (
            f"B={self.budget_score}/25 | A={self.authority_score}/25 | "
            f"N={self.need_score}/25 | T={self.timing_score}/25"
        )
        lines = [
            f"# BANT Qualification: {self.hotel_name}",
            f"**ID:** {self.qualifier_id}",
            f"**Hotel Lead:** {self.hotel_lead_id}",
            f"**Tier:** {self.qualification_tier} | **Score:** {self.total_score}/100 ({scores})",
            f"**Actionable:** {self.is_actionable}",
            "",
            "## Reasons",
            "",
        ]
        for r in self.reasons:
            lines.append(f"- {r}")
        if self.risks:
            lines.append("")
            lines.append("## Risks")
            lines.append("")
            for r in self.risks:
                lines.append(f"- **RISK:** {r}")
        if self.missing_information:
            lines.append("")
            lines.append("## Missing Information")
            lines.append("")
            for m in self.missing_information:
                lines.append(f"- [ ] {m}")
        lines.append("")
        lines.append(f"## Next Action")
        lines.append(f"{self.recommended_next_action}")
        lines.append("")
        lines.append(f"**dry_run:** {self.dry_run}")
        return "\n".join(lines)


# ── Lead Qualifier ─────────────────────────────────────────────────────────

class LeadQualifier:
    """Deterministic BANT lead qualifier for hotel prospecting.

    Scores each BANT dimension 0-25 from HotelLead fields.
    Produces BANTResult with tier, reasons, risks, and next action recommendation.

    All scoring is deterministic — no ML, no randomness, no external API.
    Handles placeholder/missing data gracefully without fabricating values.
    """

    def qualify(self, hotel_lead: HotelLead) -> BANTResult:
        """Run full BANT qualification on a HotelLead.

        Args:
            hotel_lead: HotelLead to qualify

        Returns:
            BANTResult with scores, tier, reasons, risks, missing info
        """
        import uuid

        dims = [
            _score_budget(hotel_lead),
            _score_authority(hotel_lead),
            _score_need(hotel_lead),
            _score_timing(hotel_lead),
        ]

        total = sum(d["score"] for d in dims)
        budget_s, auth_s, need_s, timing_s = [d["score"] for d in dims]

        all_reasons = []
        all_risks = []
        all_missing = []

        for d in dims:
            all_reasons.extend(d["reasons"])
            all_risks.extend(d["risks"])
            all_missing.extend(d["missing"])

        missing_count = sum(1 for d in dims if d["missing"])
        tier = _determine_tier(total, missing_count)

        # If missing info tier, override next action regardless of score
        if missing_count >= 3:
            tier = MISSING_INFO

        return BANTResult(
            qualifier_id=str(uuid.uuid4())[:12],
            hotel_lead_id=hotel_lead.hotel_lead_id,
            hotel_name=hotel_lead.hotel_name or hotel_lead.name,
            budget_score=budget_s,
            authority_score=auth_s,
            need_score=need_s,
            timing_score=timing_s,
            total_score=total,
            qualification_tier=tier,
            reasons=all_reasons,
            risks=all_risks,
            missing_information=all_missing,
            recommended_next_action=TIER_NEXT_ACTIONS.get(tier, ""),
            dimension_details={
                "budget": dims[0],
                "authority": dims[1],
                "need": dims[2],
                "timing": dims[3],
            },
            dry_run=True,
        )

    def qualify_batch(self, hotel_leads: list[HotelLead]) -> list[BANTResult]:
        """Qualify multiple HotelLeads, sorted by total_score descending."""
        results = [self.qualify(hl) for hl in hotel_leads]
        return sorted(results, key=lambda r: r.total_score, reverse=True)

    def qualify_from_prospect_list(self, prospect_list) -> list[BANTResult]:
        """Qualify all HotelLeads in a ProspectList."""
        from src.commercial.prospect_list import ProspectList
        results = []
        for entry in prospect_list.list_all():
            result = self.qualify(entry.hotel_lead)
            results.append(result)
        return sorted(results, key=lambda r: r.total_score, reverse=True)

    def summary_by_tier(self, results: list[BANTResult]) -> dict:
        """Count results by qualification tier."""
        tiers = {QUALIFIED: 0, NURTURE: 0, LOW_FIT: 0, DISQUALIFIED: 0, MISSING_INFO: 0}
        for r in results:
            tiers[r.qualification_tier] = tiers.get(r.qualification_tier, 0) + 1
        return tiers

    def export_report(self, results: list[BANTResult]) -> str:
        """Generate markdown report for batch qualification results."""
        lines = [
            "# BANT Qualification Report",
            f"**Total qualified:** {len(results)}",
            "",
            "## Summary by Tier",
            "",
        ]
        tier_counts = self.summary_by_tier(results)
        for tier, count in tier_counts.items():
            if count > 0:
                lines.append(f"- **{tier}:** {count}")

        lines.append("")
        lines.append("## Detailed Results")
        lines.append("")

        for r in results:
            lines.append(
                f"### {r.hotel_name} — {r.qualification_tier} ({r.total_score}/100)"
            )
            lines.append(
                f"Budget={r.budget_score}/25 | Authority={r.authority_score}/25 | "
                f"Need={r.need_score}/25 | Timing={r.timing_score}/25"
            )
            lines.append(f"**Action:** {r.recommended_next_action}")
            if r.risks:
                lines.append(f"**Risks:** {'; '.join(r.risks[:3])}")
            lines.append("")

        return "\n".join(lines)
