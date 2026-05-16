"""W126 — Commercial Proposal & Objection Brief for hotel prospects.

Generates a complete proposal brief from a PackageMatch (W125), integrating
BANTResult risks (W124) as anticipated objections with pre-written responses.

All dry-run, template-based, zero API. Markdown output ready for human review.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path

from src.commercial.hotel_lead import HotelLead
from src.commercial.lead_qualifier import BANTResult
from src.commercial.package_matcher import PackageMatch


# ── Objection Map ─────────────────────────────────────────────────────────

OBJECTION_TYPES = frozenset({
    "preco", "timing", "autoridade", "concorrencia", "resultado", "urgencia",
})

# Pre-written responses by objection type and package tier
OBJECTION_RESPONSES = {
    "preco": {
        "Starter": (
            "Entendo a preocupacao com orcamento. O pacote Starter (R$350) e nosso "
            "modelo de entrada justamente para que voce teste o resultado sem risco. "
            "Se performar, o ROI e imediato — cada collab gera em media R$2K-5K em "
            "visibilidade organica. E se nao gostar, nao tem contrato longo."
        ),
        "Growth": (
            "O Growth (R$990/mes) entrega 3 collabs mensais com alcance de 2M+. "
            "Comparado a Meta Ads (CPM R$15-25), nosso CPM efetivo e R$0,15 — "
            "98%% mais barato. Alem disso, o SEO organico fica indexado pra sempre. "
            "O retorno medio dos nossos parceiros e 5-10x o investimento."
        ),
        "Premium": (
            "O Premium (R$1.200) e nosso pacote de dominio de nicho. 4 collabs + "
            "3 stories + SEOgram cobrem toda a jornada do cliente. O custo e fixo, "
            "sem leilao, sem algoritmo. E tem resultado garantido ou reembolso — "
            "zero risco pro seu negocio."
        ),
    },
    "timing": {
        "default": (
            "Se o timing nao e ideal agora, podemos comecar com um pacote Starter "
            "para manter presenca e escalar quando a janela abrir. Ou agendar para "
            "a proxima temporada — as condicoes comerciais ficam travadas por 30 dias."
        ),
    },
    "autoridade": {
        "default": (
            "Se voce precisa de aprovacao interna, posso preparar um resumo "
            "executivo de 1 pagina com numeros e cases para seu gestor. "
            "Tambem podemos fazer uma call rapida com o decisor para alinhar."
        ),
    },
    "concorrencia": {
        "default": (
            "Diferente de influenciadores que so postam foto, nosso metodo combina "
            "collab + SEO organico + multi-perfil. O concorrente X pode ter feito "
            "1 post — nos entregamos presenca consistente em 3+ perfis com alcance "
            "cumulativo. Alem disso, nosso publico e real — zero bots."
        ),
    },
    "resultado": {
        "default": (
            "Nosso modelo e resultado garantido. Se a collab nao performar dentro "
            "do esperado (alcance e engajamento), regravamos ou reembolsamos. "
            "Nao e fee de agencia — e investimento com risco controlado. "
            "Temos cases de hoteis que tiveram 300%% de aumento em mencoes organicas "
            "em 30 dias."
        ),
    },
    "urgencia": {
        "default": (
            "Sei que e uma decisao importante. Nao trabalho com pressao artificial "
            "de 'ultima vaga'. As condicoes ficam validas por 15 dias, e se voce "
            "precisar de mais tempo, e so avisar. O importante e a parceria certa, "
            "nao a parceria rapida."
        ),
    },
}


# ── Objection Entry ────────────────────────────────────────────────────────

@dataclass
class ObjectionEntry:
    """Single objection with pre-written response."""

    objection_type: str
    objection_text: str
    response: str
    source: str = ""  # "standard" or "bant_risk"

    def to_dict(self) -> dict:
        return {
            "objection_type": self.objection_type,
            "objection_text": self.objection_text,
            "response": self.response,
            "source": self.source,
        }


# ── Proposal Brief ─────────────────────────────────────────────────────────

@dataclass
class ProposalBrief:
    """Complete commercial proposal brief with objection mapping.

    Generated from PackageMatch (W125) + BANTResult (W124) + HotelLead (W121).
    Markdown output ready for human review before any send.
    """

    brief_id: str
    hotel_lead_id: str
    hotel_name: str
    recommended_package: str
    offer_summary: str = ""
    commercial_angle: str = ""
    talking_points: list[str] = field(default_factory=list)
    package_details: dict = field(default_factory=dict)
    expected_value: str = ""
    objection_map: list[ObjectionEntry] = field(default_factory=list)
    bant_risks_as_objections: list[ObjectionEntry] = field(default_factory=list)
    recommended_next_step: str = ""
    markdown_output: str = ""
    dry_run: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def total_objections(self) -> int:
        return len(self.objection_map) + len(self.bant_risks_as_objections)

    def to_dict(self) -> dict:
        return {
            "brief_id": self.brief_id,
            "hotel_lead_id": self.hotel_lead_id,
            "hotel_name": self.hotel_name,
            "recommended_package": self.recommended_package,
            "offer_summary": self.offer_summary,
            "commercial_angle": self.commercial_angle,
            "talking_points": self.talking_points,
            "package_details": self.package_details,
            "expected_value": self.expected_value,
            "objection_map": [o.to_dict() for o in self.objection_map],
            "bant_risks_as_objections": [o.to_dict() for o in self.bant_risks_as_objections],
            "recommended_next_step": self.recommended_next_step,
            "markdown_output": self.markdown_output,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ProposalBrief":
        obj_map = [ObjectionEntry(**o) for o in d.get("objection_map", [])]
        bant_objs = [ObjectionEntry(**o) for o in d.get("bant_risks_as_objections", [])]
        return cls(
            brief_id=d["brief_id"],
            hotel_lead_id=d.get("hotel_lead_id", ""),
            hotel_name=d.get("hotel_name", ""),
            recommended_package=d.get("recommended_package", ""),
            offer_summary=d.get("offer_summary", ""),
            commercial_angle=d.get("commercial_angle", ""),
            talking_points=d.get("talking_points", []),
            package_details=d.get("package_details", {}),
            expected_value=d.get("expected_value", ""),
            objection_map=obj_map,
            bant_risks_as_objections=bant_objs,
            recommended_next_step=d.get("recommended_next_step", ""),
            markdown_output=d.get("markdown_output", ""),
            dry_run=d.get("dry_run", True),
            created_at=d.get("created_at", ""),
        )


# ── Commercial Angles by niche ─────────────────────────────────────────────

def _commercial_angle(hl: HotelLead) -> str:
    """Generate commercial angle contextualized by niche and region."""
    hotel = hl.hotel_name or hl.name
    niche = hl.niche
    region = hl.region
    city = hl.city
    state = hl.state
    loc = f"{city}/{state}" if city and state else (city or state or "sua regiao")

    angles = {
        "resort": (
            f"O {hotel} em {loc} tem o produto que nosso publico de alta renda busca: "
            f"experiencia premium em destino paradisiaco. Uma collab aqui nao e publi — "
            f"e curadoria de viagem. Nosso publico confia na nossa recomendacao e "
            f"viaja com base nela."
        ),
        "pousada": (
            f"O {hotel} representa o charme e a autenticidade que nosso publico familia "
            f"adora. Pousadas sao o tipo de hospedagem que mais gera engajamento organico "
            f"nos nossos perfis — o publico se ve la."
        ),
        "boutique": (
            f"O {hotel} e exatamente o tipo de experiencia aspiracional que performa "
            f"bem com nossa audiencia. Hoteis boutique geram desejo e salvamento — "
            f"o ROI organico e excepcional."
        ),
        "fazenda": (
            f"O {hotel} conecta com o turismo rural e familiar — nicho em crescimento "
            f"acelerado no Brasil. Nosso perfil @afamiliatigrereal (320K familias) "
            f"e o canal perfeito para esse tipo de experiencia."
        ),
        "eco_resort": (
            f"O {hotel} combina sustentabilidade com experiencia — o publico de viagem "
            f"consciente e um dos que mais cresce. Nossa audiencia busca exatamente "
            f"esse equilibrio entre conforto e natureza."
        ),
        "glamping": (
            f"O {hotel} e tendencia pura — glamping e o segmento que mais cresce em "
            f"engajamento no Instagram de viagem. Nosso publico ama novidade e "
            f"experiencia diferenciada."
        ),
    }

    if niche in angles:
        return angles[niche]

    return (
        f"O {hotel} em {loc} tem potencial de se destacar no nicho de {niche} "
        f"com nossa audiencia qualificada de viagem. A combinacao de alcance "
        f"organico + SEO organico gera resultado de longo prazo."
    )


# ── Talking Points ─────────────────────────────────────────────────────────

def _talking_points(hl: HotelLead, package: str) -> list[str]:
    """Generate tier-appropriate talking points."""
    hotel = hl.hotel_name or hl.name
    niche = hl.niche
    is_premium = package == "Premium"
    is_growth = package == "Growth"

    points = [
        f"2.3M+ seguidores em 6 perfis — alcance organico real, sem bots",
        f"CPM R$0,15 vs R$15-25 Meta Ads — 98%% mais barato que trafego pago",
        f"Audiencia 100%% organica no nicho de viagem — seguidor que viaja",
    ]

    if is_premium:
        points.append(f"4 collabs + 3 stories + SEO indexado — cobertura completa em 30 dias")
        points.append(f"Dominio do nicho {niche} no Instagram — {hotel} vira referencia")
    elif is_growth:
        points.append(f"3 collabs mensais + SEOgram — presenca consistente, nao pontual")
        points.append(f"Multi-perfil: alcance cruzado entre 3 perfis complementares")
    else:
        points.append(f"1 collab estrategica — formato simples, resultado medido")
        points.append(f"Porta de entrada para parceria de longo prazo — teste sem risco")

    points.append(f"Resultado garantido ou reembolso — risco zero para {hotel}")
    return points


# ── Expected Value ─────────────────────────────────────────────────────────

def _expected_value(hl: HotelLead, package: str) -> str:
    """Generate expected value statement by package tier."""
    if package == "Premium":
        return (
            f"Alcance estimado: 1.5M-2.5M+ organicos em 30 dias. "
            f"Visibilidade equivalente a R$22K-37K em Meta Ads. "
            f"Custo real: R$1.200 — economia de ~95%%."
        )
    elif package == "Growth":
        return (
            f"Alcance estimado: 800K-1.5M organicos por mes. "
            f"Visibilidade equivalente a R$12K-22K em Meta Ads. "
            f"Custo real: R$990/mes — economia de ~92%%."
        )
    else:
        return (
            f"Alcance estimado: 300K-800K organicos. "
            f"Visibilidade equivalente a R$4.5K-12K em Meta Ads. "
            f"Custo real: R$350 — economia de ~92%%."
        )


# ── Proposal Brief Builder ─────────────────────────────────────────────────

class ProposalBriefBuilder:
    """Builds complete commercial proposal briefs with objection mapping.

    Consumes PackageMatch (W125) + BANTResult (W124) + HotelLead (W121).
    All output is template-based, dry-run, markdown formatted.
    """

    def build(self, package_match: PackageMatch, bant_result: BANTResult,
              hotel_lead: HotelLead) -> ProposalBrief:
        """Build a full proposal brief from a package match.

        Args:
            package_match: Package match result from PackageMatcher
            bant_result: Pre-computed BANT qualification
            hotel_lead: The HotelLead prospect

        Returns:
            ProposalBrief with offer, angles, talking points, and objection map
        """
        import uuid

        hl = hotel_lead
        package = package_match.recommended_package
        hotel = hl.hotel_name or hl.name

        if not package:
            return ProposalBrief(
                brief_id=str(uuid.uuid4())[:12],
                hotel_lead_id=hl.hotel_lead_id,
                hotel_name=hotel,
                recommended_package="",
                offer_summary="Sem recomendacao de pacote — lead nao qualificado.",
                markdown_output=f"# No Proposal — {hotel}\n\nLead nao atende criterios minimos.",
                dry_run=True,
            )

        # ── Build components ───────────────────────────────────────────────
        angle = _commercial_angle(hl)
        points = _talking_points(hl, package)
        value = _expected_value(hl, package)

        # ── Standard objections ────────────────────────────────────────────
        objections = []
        for otype in ("preco", "timing", "autoridade", "concorrencia", "resultado", "urgencia"):
            resp_map = OBJECTION_RESPONSES.get(otype, {})
            if package in resp_map:
                resp = resp_map[package]
            else:
                resp = resp_map.get("default", "Resposta nao disponivel — preparar manualmente.")

            obj_texts = {
                "preco": f"'{package} e caro para nosso orcamento'",
                "timing": "'Nao e o momento certo para investir nisso'",
                "autoridade": "'Preciso falar com meu gestor/socio'",
                "concorrencia": "'Ja trabalhamos com outro influenciador/agencia'",
                "resultado": "'Como vou saber se funciona?'",
                "urgencia": "'Vou pensar e te retorno'",
            }

            objections.append(ObjectionEntry(
                objection_type=otype,
                objection_text=obj_texts.get(otype, ""),
                response=resp,
                source="standard",
            ))

        # ── BANT risks as objections ───────────────────────────────────────
        bant_objs = []
        for risk in bant_result.risks:
            bant_objs.append(ObjectionEntry(
                objection_type="bant_risk",
                objection_text=risk,
                response=(
                    f"Risco mapeado pelo qualificador BANT. Abordar com transparencia. "
                    f"Se o lead levantar este ponto, reconhecer e oferecer solucao especifica "
                    f"baseada no pacote {package}."
                ),
                source="bant_risk",
            ))

        # ── Next step ──────────────────────────────────────────────────────
        next_step = package_match.next_action

        # ── Offer summary ──────────────────────────────────────────────────
        offer = (
            f"Pacote {package} — {package_match.package_details.get('price', '')} — "
            f"para {hotel} ({hl.city}/{hl.state}). "
            f"Publico-alvo: viajantes qualificados do Nordeste e Brasil. "
            f"Formato: {' '.join(package_match.package_details.get('scope', [])[:2])}."
        )

        # ── Build markdown ─────────────────────────────────────────────────
        md = self._render_markdown(
            brief_id="",  # filled after object creation
            hotel=hotel,
            package=package,
            offer_summary=offer,
            angle=angle,
            points=points,
            details=package_match.package_details,
            value=value,
            objections=objections,
            bant_objs=bant_objs,
            channels=package_match.recommended_channels,
            profiles=package_match.suggested_profiles,
            next_step=next_step,
            bant_tier=bant_result.qualification_tier,
            bant_total=bant_result.total_score,
        )

        brief_id = str(uuid.uuid4())[:12]
        md = md.replace("**Brief ID:** ", f"**Brief ID:** {brief_id}")

        return ProposalBrief(
            brief_id=brief_id,
            hotel_lead_id=hl.hotel_lead_id,
            hotel_name=hotel,
            recommended_package=package,
            offer_summary=offer,
            commercial_angle=angle,
            talking_points=points,
            package_details=package_match.package_details,
            expected_value=value,
            objection_map=objections,
            bant_risks_as_objections=bant_objs,
            recommended_next_step=next_step,
            markdown_output=md,
            dry_run=True,
        )

    def _render_markdown(
        self, brief_id: str, hotel: str, package: str, offer_summary: str,
        angle: str, points: list[str], details: dict, value: str,
        objections: list[ObjectionEntry], bant_objs: list[ObjectionEntry],
        channels: list[str], profiles: list[str], next_step: str,
        bant_tier: str, bant_total: int,
    ) -> str:
        lines = [
            f"# Commercial Proposal Brief — {hotel}",
            f"**Brief ID:** {brief_id}",
            f"**Package:** {package} | **BANT:** {bant_tier} ({bant_total}/100)",
            "",
            "---",
            "",
            "## 1. Offer Summary",
            offer_summary,
            "",
            "## 2. Commercial Angle",
            angle,
            "",
            "## 3. Talking Points",
            "",
        ]
        for p in points:
            lines.append(f"- {p}")

        lines.extend([
            "",
            "## 4. Package Details",
            f"**Tier:** {package}",
            f"**Price:** {details.get('price', '—')}",
            f"**Scope:**",
        ])
        for s in details.get("scope", []):
            lines.append(f"  - {s}")
        lines.append(f"**Ideal for:** {details.get('ideal_for', '—')}")

        lines.extend([
            "",
            f"## 5. Expected Value",
            value,
            "",
            "## 6. Recommended Channels",
        ])
        for ch in channels:
            lines.append(f"- {ch}")
        lines.append("")
        lines.append("## 7. Suggested Profiles")
        for p in profiles:
            lines.append(f"- {p}")

        lines.extend([
            "",
            "## 8. Objection Map",
            "",
            "Pre-wired responses for common objections during negotiation:",
            "",
        ])
        for i, obj in enumerate(objections, 1):
            lines.extend([
                f"### 8.{i} {obj.objection_type.upper()}",
                f"**Objeção:** {obj.objection_text}",
                f"**Resposta:** {obj.response}",
                "",
            ])

        if bant_objs:
            lines.extend([
                "## 9. Anticipated Objections (from BANT risks)",
                "",
            ])
            for i, obj in enumerate(bant_objs, 1):
                lines.extend([
                    f"### 9.{i} BANT Risk",
                    f"**Risco detectado:** {obj.objection_text}",
                    f"**Resposta sugerida:** {obj.response}",
                    "",
                ])

        sec_num = 10 if bant_objs else 9
        lines.extend([
            f"## {sec_num}. Next Step",
            next_step,
            "",
            "---",
            "",
            "**Disclaimer:** Brief gerado automaticamente pelo OMNIS Commercial SDR.",
            "Revisar antes de qualquer envio. Nenhuma mensagem foi enviada.",
            f"**dry_run:** True",
        ])
        return "\n".join(lines)

    def build_for_disqualified(self, hotel_lead: HotelLead,
                               bant_result: BANTResult) -> ProposalBrief:
        """Generate a brief for disqualified/low-fit leads — no recommendation."""
        import uuid
        hotel = hotel_lead.hotel_name or hotel_lead.name
        md = (
            f"# No Proposal — {hotel}\n\n"
            f"**BANT Tier:** {bant_result.qualification_tier} ({bant_result.total_score}/100)\n\n"
            f"Lead nao atende criterios minimos para proposta comercial.\n\n"
            f"**Riscos:**\n"
        )
        for r in bant_result.risks:
            md += f"- {r}\n"
        md += f"\n**Recomendacao:** {bant_result.recommended_next_action}\n"

        return ProposalBrief(
            brief_id=str(uuid.uuid4())[:12],
            hotel_lead_id=hotel_lead.hotel_lead_id,
            hotel_name=hotel,
            recommended_package="",
            markdown_output=md,
            recommended_next_step=bant_result.recommended_next_action,
            dry_run=True,
        )

    def export_batch(self, briefs: list[ProposalBrief]) -> str:
        """Export multiple briefs as a single summary markdown report."""
        lines = [
            "# Proposal Brief Batch Report",
            f"**Total briefs:** {len(briefs)}",
            f"**With recommendation:** {sum(1 for b in briefs if b.recommended_package)}",
            "",
            "## Index",
            "",
        ]
        for i, brief in enumerate(briefs, 1):
            pkg = brief.recommended_package or "No Match"
            lines.append(f"{i}. **{brief.hotel_name}** → {pkg} ({brief.total_objections} objections)")

        lines.append("")
        lines.append("---")
        lines.append("")

        for brief in briefs:
            lines.append(brief.markdown_output)
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)
