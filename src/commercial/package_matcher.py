"""W125 — Commercial Package Matcher for HotelLead prospects.

Matches qualified HotelLeads to commercial packages (Starter/Growth/Premium)
based on BANT tier, hotel_tier, fit_score, niche, and region.
Generates inline media kit brief — zero PDF generation, zero API.

Consumes HotelLead (W121), BANTResult (W124), ProspectList (W122).
References TIER_DETAILS from src/sales/proposals.py (read-only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path

from src.commercial.hotel_lead import HotelLead
from src.commercial.lead_qualifier import BANTResult, QUALIFIED, NURTURE, LOW_FIT, DISQUALIFIED


# ── Package Tiers (matches src/sales/proposals.py::ProposalTier) ────────────

class PackageTier(str, Enum):
    STARTER = "Starter"
    GROWTH = "Growth"
    PREMIUM = "Premium"


# Read-only reference — do NOT modify src/sales/proposals.py
PACKAGE_DETAILS = {
    PackageTier.STARTER.value: {
        "price": "R$ 350",
        "scope": ["1 collab (feed ou reels)", "1 perfil Instagram", "Prazo: 7 dias uteis"],
        "ideal_for": "Testar collab com baixo investimento",
    },
    PackageTier.GROWTH.value: {
        "price": "R$ 990/mes",
        "scope": ["3 collabs por mes", "3 perfis Instagram", "SEOgram incluso", "Prazo: 15 dias uteis"],
        "ideal_for": "Presenca consistente e crescimento organico",
    },
    PackageTier.PREMIUM.value: {
        "price": "R$ 1.200",
        "scope": ["4 collabs (feed + reels)", "3+ perfis Instagram", "SEOgram + 3 stories", "Prazo: 20 dias uteis"],
        "ideal_for": "Dominio de nicho com producao premium",
    },
}

# ── Profile suggestions by niche ───────────────────────────────────────────

NICHE_PROFILES = {
    "resort": ["@lucastigrereal (690K)", "@oinatalrn (630K)", "@afamiliatigrereal (320K)"],
    "pousada": ["@oinatalrn (630K)", "@afamiliatigrereal (320K)", "@agenteviajabrasil (452K)"],
    "boutique": ["@lucastigrereal (690K)", "@oquecomernatalrn (249K)", "@natalaivoueu (240K)"],
    "fazenda": ["@afamiliatigrereal (320K)", "@agenteviajabrasil (452K)"],
    "urbano": ["@oquecomernatalrn (249K)", "@natalaivoueu (240K)"],
    "hostel": ["@agenteviajabrasil (452K)"],
    "eco_resort": ["@lucastigrereal (690K)", "@afamiliatigrereal (320K)", "@agenteviajabrasil (452K)"],
    "glamping": ["@afamiliatigrereal (320K)", "@agenteviajabrasil (452K)"],
    "apart_hotel": ["@oinatalrn (630K)", "@oquecomernatalrn (249K)"],
    "hotel": ["@agenteviajabrasil (452K)", "@oinatalrn (630K)"],
}

CHANNEL_SUGGESTIONS = {
    PackageTier.STARTER.value: ["instagram_dm", "email"],
    PackageTier.GROWTH.value: ["email", "whatsapp", "instagram_dm"],
    PackageTier.PREMIUM.value: ["email", "whatsapp", "call"],
}


# ── Package Match ──────────────────────────────────────────────────────────

@dataclass
class PackageMatch:
    """Result of matching a HotelLead to a commercial package."""

    match_id: str
    hotel_lead_id: str
    hotel_name: str
    bant_tier: str
    recommended_package: str  # Starter, Growth, Premium, or "" for no match
    rationale: list[str] = field(default_factory=list)
    recommended_channels: list[str] = field(default_factory=list)
    suggested_profiles: list[str] = field(default_factory=list)
    package_details: dict = field(default_factory=dict)
    media_kit_brief: str = ""
    risk_notes: list[str] = field(default_factory=list)
    next_action: str = ""
    dry_run: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def has_recommendation(self) -> bool:
        return self.recommended_package != ""

    def to_dict(self) -> dict:
        return {
            "match_id": self.match_id,
            "hotel_lead_id": self.hotel_lead_id,
            "hotel_name": self.hotel_name,
            "bant_tier": self.bant_tier,
            "recommended_package": self.recommended_package,
            "rationale": self.rationale,
            "recommended_channels": self.recommended_channels,
            "suggested_profiles": self.suggested_profiles,
            "package_details": self.package_details,
            "media_kit_brief": self.media_kit_brief,
            "risk_notes": self.risk_notes,
            "next_action": self.next_action,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PackageMatch":
        return cls(
            match_id=d["match_id"],
            hotel_lead_id=d.get("hotel_lead_id", ""),
            hotel_name=d.get("hotel_name", ""),
            bant_tier=d.get("bant_tier", ""),
            recommended_package=d.get("recommended_package", ""),
            rationale=d.get("rationale", []),
            recommended_channels=d.get("recommended_channels", []),
            suggested_profiles=d.get("suggested_profiles", []),
            package_details=d.get("package_details", {}),
            media_kit_brief=d.get("media_kit_brief", ""),
            risk_notes=d.get("risk_notes", []),
            next_action=d.get("next_action", ""),
            dry_run=d.get("dry_run", True),
            created_at=d.get("created_at", ""),
        )

    def to_markdown(self) -> str:
        lines = [
            f"# Package Match: {self.hotel_name}",
            f"**Match ID:** {self.match_id} | **Hotel Lead:** {self.hotel_lead_id}",
            f"**BANT Tier:** {self.bant_tier} | **Recommended:** {self.recommended_package or 'NO MATCH'}",
            "",
            "## Rationale",
            "",
        ]
        for r in self.rationale:
            lines.append(f"- {r}")

        if not self.has_recommendation:
            lines.append("")
            lines.append("**No package recommended.** Lead does not meet minimum criteria.")
            return "\n".join(lines)

        lines.extend([
            "",
            "## Package Details",
            f"**Tier:** {self.recommended_package}",
            f"**Price:** {self.package_details.get('price', '—')}",
            f"**Scope:**",
        ])
        for s in self.package_details.get("scope", []):
            lines.append(f"  - {s}")
        lines.extend([
            f"**Ideal for:** {self.package_details.get('ideal_for', '—')}",
            "",
            "## Recommended Channels",
        ])
        for ch in self.recommended_channels:
            lines.append(f"- {ch}")
        lines.append("")
        lines.append("## Suggested Profiles")
        for p in self.suggested_profiles:
            lines.append(f"- {p}")
        lines.append("")
        lines.append("## Media Kit Brief")
        lines.append(self.media_kit_brief)

        if self.risk_notes:
            lines.append("")
            lines.append("## Risk Notes")
            for r in self.risk_notes:
                lines.append(f"- **RISK:** {r}")

        lines.extend([
            "",
            f"## Next Action",
            f"{self.next_action}",
            "",
            f"**dry_run:** {self.dry_run}",
        ])
        return "\n".join(lines)


# ── Media Kit Brief Generator ──────────────────────────────────────────────

def _generate_media_kit_brief(hl: HotelLead, package: str) -> str:
    """Generate inline media kit structure for a HotelLead.

    Contextualized by hotel name, niche, region, and package tier.
    """
    hotel = hl.hotel_name or hl.name
    city = hl.city
    state = hl.state
    niche = hl.niche
    region = hl.region
    tier = package

    location = f"{city}/{state}" if city and state else (city or state or "sua regiao")

    slides = [
        f"### Media Kit — {hotel}",
        "",
        "**Slide 1 — Capa:**",
        f"  - Logo ou foto de capa do {hotel}",
        f"  - Titulo: '{hotel} x Lucas Tigre — Parceria de Midia'",
        "",
        "**Slide 2 — Quem Somos:**",
        f"  - @lucastigrereal: 690K seguidores — autoridade em viagem e gastronomia",
        f"  - Rede de 6 perfis com 2.3M+ seguidores no nicho de turismo",
        f"  - Alcance organico de 2M+ mensais — CPM 98% menor que Meta Ads",
        "",
        "**Slide 3 — Oportunidade:**",
    ]

    if niche in ("resort", "eco_resort", "boutique"):
        slides.append(f"  - Publico de alta renda busca experiencias como {hotel} em {location}")
        slides.append(f"  - Tourism marketing organico com autoridade real — nao e ads")
    elif niche in ("pousada", "fazenda", "glamping"):
        slides.append(f"  - Publico familia busca hospedagens unicas como {hotel} em {location}")
        slides.append(f"  - Conexao emocional com a audiencia — 320K+ familias")
    else:
        slides.append(f"  - Publico qualificado busca {niche} em {location}")
        slides.append(f"  - Divulgacao organica com credibilidade de quem visita")

    slides.extend([
        "",
        "**Slide 4 — Pacote Recomendado:**",
        f"  - {tier}: {PACKAGE_DETAILS.get(tier, {}).get('price', '—')}",
    ])
    for s in PACKAGE_DETAILS.get(tier, {}).get("scope", []):
        slides.append(f"  - {s}")
    slides.append(f"  - Perfis sugeridos: {', '.join(NICHE_PROFILES.get(niche, NICHE_PROFILES['hotel'])[:2])}")

    slides.extend([
        "",
        "**Slide 5 — Cases & Resultados:**",
        f"  - Inserir 2-3 cases relevantes para {niche} em {location}",
        f"  - Metricas: alcance, engajamento, trafego gerado",
        "",
        "**Slide 6 — Proximos Passos:**",
        f"  - Call de 15min para alinhar expectativas",
        f"  - Contrato simples, sem burocracia",
        f"  - Resultado garantido ou reembolso",
        "",
        f"**Slide 7 — Contato:**",
        f"  - @lucastigrereal | lucastigrereal@gmail.com",
        f"  - JARVIS Commercial SDR | OMNIS Control",
    ])
    return "\n".join(slides)


# ── Package Matcher ────────────────────────────────────────────────────────

class PackageMatcher:
    """Deterministic commercial package matcher for HotelLead prospects.

    Consumes BANTResult (W124) as input — does NOT re-score.
    References PACKAGE_DETAILS inline (mirrors src/sales/proposals.py without importing).
    """

    def match(self, hotel_lead: HotelLead, bant_result: BANTResult) -> PackageMatch:
        """Match a HotelLead to the best commercial package.

        Uses BANT tier as primary signal, refined by hotel_tier, fit_score,
        niche, and region.

        Args:
            hotel_lead: HotelLead to match
            bant_result: Pre-computed BANT qualification result

        Returns:
            PackageMatch with recommendation, rationale, channels, and media kit brief
        """
        import uuid

        hl = hotel_lead
        rationale: list[str] = []
        risks: list[str] = []

        tier = bant_result.qualification_tier
        hotel_tier = hl.hotel_tier
        fit = hl.fit_score
        niche = hl.niche
        region = hl.region
        is_premium = hl.is_premium_candidate

        # ── Match decision tree ────────────────────────────────────────────

        package = ""
        if tier == DISQUALIFIED:
            rationale.append(f"Lead desqualificado (BANT={tier}) — nao recomendar pacote")
            risks.append("Lead nao atende criterios minimos de qualificacao")
            package = ""
        elif tier == LOW_FIT:
            if hotel_tier == "Premium" and fit >= 70:
                package = PackageTier.STARTER.value
                rationale.append(f"Low-fit mas hotel Premium com fit razoavel ({fit}) — oferecer Starter como teste")
                risks.append("Baixo fit BANT — expectativa deve ser gerenciada")
            else:
                rationale.append(f"Low-fit BANT + {hotel_tier}/{fit} — sem fit comercial claro")
                risks.append("Lead com baixa probabilidade de conversao")
                package = ""
        elif tier == NURTURE:
            if is_premium:
                package = PackageTier.GROWTH.value
                rationale.append(f"Nurture + Premium candidate — Growth como porta de entrada para upsell futuro")
                rationale.append(f"Hotel {hotel_tier} com fit_score={fit} — margem para evoluir para Premium")
            elif hotel_tier == "Growth" and fit >= 50:
                package = PackageTier.GROWTH.value
                rationale.append(f"Nurture Growth com fit ok ({fit}) — pacote Growth compativel")
            elif hotel_tier == "Premium":
                package = PackageTier.GROWTH.value
                rationale.append(f"Nurture Premium — Growth como entrada, upsell para Premium se performar")
            else:
                package = PackageTier.STARTER.value
                rationale.append(f"Nurture {hotel_tier} — Starter para testar sem compromisso")
                rationale.append("Objetivo: provar resultado e fazer upsell em 3 meses")
        elif tier == QUALIFIED:
            if is_premium and fit >= 85:
                package = PackageTier.PREMIUM.value
                rationale.append(f"Qualificado Premium + fit alto ({fit}) — pacote Premium recomendado")
                rationale.append(f"Hotel {hotel_tier} com alto potencial de receita")
            elif is_premium or (hotel_tier == "Premium" and fit >= 70):
                package = PackageTier.GROWTH.value
                rationale.append(f"Qualificado Premium — Growth como entrada, upgrade natural para Premium")
                rationale.append(f"fit_score={fit} — consistente com investimento Growth")
            elif hotel_tier == "Growth" or fit >= 60:
                package = PackageTier.GROWTH.value
                rationale.append(f"Qualificado {hotel_tier} — Growth como pacote padrao")
            else:
                package = PackageTier.GROWTH.value
                rationale.append(f"Qualificado — recomendar Growth como pacote de entrada")
                rationale.append("Starter e muito basico para lead qualificado — risco de sub-venda")

        # ── Missing info override ──────────────────────────────────────────
        if tier == "missing_information":
            rationale.append("Informacoes insuficientes para recomendar pacote — completar BANT primeiro")
            risks.append("Campos faltantes no HotelLead bloqueiam match confiavel")
            package = ""

        # ── Channels by package ────────────────────────────────────────────
        channels = CHANNEL_SUGGESTIONS.get(package, []) if package else []

        # ── Profiles by niche ──────────────────────────────────────────────
        profiles = NICHE_PROFILES.get(niche, NICHE_PROFILES["hotel"]) if package else []

        # ── Media kit brief ────────────────────────────────────────────────
        media_kit = _generate_media_kit_brief(hl, package) if package else ""

        # ── Next action ────────────────────────────────────────────────────
        if package:
            if tier == QUALIFIED:
                next_action = f"Enviar proposta {package} e agendar call de fechamento em 48h"
            elif tier == NURTURE:
                next_action = f"Enviar material introdutorio {package} e iniciar cadencia D+0/D+2/D+5"
            else:
                next_action = f"Enviar proposta {package} com ressalvas — follow-up manual"
        else:
            next_action = "Nao priorizar — revisitar lead se houver novos dados"

        return PackageMatch(
            match_id=str(uuid.uuid4())[:12],
            hotel_lead_id=hl.hotel_lead_id,
            hotel_name=hl.hotel_name or hl.name,
            bant_tier=tier,
            recommended_package=package,
            rationale=rationale,
            recommended_channels=channels,
            suggested_profiles=profiles,
            package_details=PACKAGE_DETAILS.get(package, {}),
            media_kit_brief=media_kit,
            risk_notes=risks,
            next_action=next_action,
            dry_run=True,
        )

    def match_batch(self, hotel_leads: list[HotelLead],
                    bant_results: list[BANTResult]) -> list[PackageMatch]:
        """Match multiple HotelLeads with their pre-computed BANT results.

        Returns matches sorted: with recommendation first, then by package (Premium > Growth > Starter).
        """
        tier_order = {PackageTier.PREMIUM.value: 0, PackageTier.GROWTH.value: 1,
                      PackageTier.STARTER.value: 2, "": 3}
        results = []
        for hl, br in zip(hotel_leads, bant_results):
            results.append(self.match(hl, br))

        results.sort(key=lambda m: (
            0 if m.has_recommendation else 1,
            tier_order.get(m.recommended_package, 3),
        ))
        return results

    def match_from_prospect_list(self, prospect_list, bant_results: list[BANTResult]
                                 ) -> list[PackageMatch]:
        """Match all HotelLeads in a ProspectList using pre-computed BANT results.

        Filters to qualified + nurture only for recommendations.
        """
        from src.commercial.prospect_list import ProspectList  # noqa: F811

        # Build lookup: hotel_lead_id → BANTResult
        bant_by_id = {br.hotel_lead_id: br for br in bant_results}

        matches = []
        for entry in prospect_list.list_all():
            hl = entry.hotel_lead
            br = bant_by_id.get(hl.hotel_lead_id)
            if br:
                matches.append(self.match(hl, br))

        tier_order = {PackageTier.PREMIUM.value: 0, PackageTier.GROWTH.value: 1,
                      PackageTier.STARTER.value: 2, "": 3}
        matches.sort(key=lambda m: (
            0 if m.has_recommendation else 1,
            tier_order.get(m.recommended_package, 3),
        ))
        return matches

    def summary_by_package(self, matches: list[PackageMatch]) -> dict:
        """Count matches by recommended package."""
        counts = {PackageTier.PREMIUM.value: 0, PackageTier.GROWTH.value: 0,
                  PackageTier.STARTER.value: 0, "no_match": 0}
        for m in matches:
            if m.has_recommendation:
                counts[m.recommended_package] += 1
            else:
                counts["no_match"] += 1
        return counts

    def export_report(self, matches: list[PackageMatch]) -> str:
        """Generate markdown summary report for batch matches."""
        lines = [
            "# Package Match Report",
            f"**Total matches:** {len(matches)}",
            "",
            "## Summary by Package",
            "",
        ]
        summary = self.summary_by_package(matches)
        for pkg, count in summary.items():
            if count > 0:
                lines.append(f"- **{pkg}:** {count}")

        lines.append("")
        lines.append("## Recommendations")
        lines.append("")

        for m in matches:
            if m.has_recommendation:
                lines.append(
                    f"### {m.hotel_name} → **{m.recommended_package}**"
                )
                lines.append(f"BANT: {m.bant_tier} | Channels: {', '.join(m.recommended_channels)}")
                lines.append(f"Next: {m.next_action}")
                lines.append("")
            else:
                lines.append(
                    f"### {m.hotel_name} → **NO MATCH** (BANT: {m.bant_tier})"
                )
                if m.risk_notes:
                    lines.append(f"Risks: {'; '.join(m.risk_notes)}")
                lines.append("")

        return "\n".join(lines)
