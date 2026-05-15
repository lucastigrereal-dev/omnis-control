"""W116 — Proposal Generator for Sales/CRM."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum


class ProposalTier(str, Enum):
    STARTER = "Starter"
    GROWTH = "Growth"
    PREMIUM = "Premium"


TIER_DETAILS = {
    ProposalTier.STARTER.value: {
        "price": "R$ 350",
        "scope": [
            "1 collab (feed ou reels)",
            "1 perfil Instagram",
            "Prazo: 7 dias úteis",
        ],
        "ideal_for": "Hotéis e restaurantes que querem testar collab",
    },
    ProposalTier.GROWTH.value: {
        "price": "R$ 990/mês",
        "scope": [
            "3 collabs por mês",
            "3 perfis Instagram",
            "SEOgram incluso",
            "Prazo: 15 dias úteis",
        ],
        "ideal_for": "Negócios que buscam presença consistente",
    },
    ProposalTier.PREMIUM.value: {
        "price": "R$ 1.200",
        "scope": [
            "4 collabs (feed + reels)",
            "3+ perfis Instagram",
            "SEOgram + 3 stories",
            "Prazo: 20 dias úteis",
        ],
        "ideal_for": "Marcas que querem domínio de nicho",
    },
}


@dataclass
class Proposal:
    """Proposal comercial — template-based, zero real send."""

    proposal_id: str
    lead_id: str = ""
    deal_id: str = ""
    client_name: str = ""
    client_company: str = ""
    tier: str = ProposalTier.GROWTH.value
    offer: str = ""
    scope: list[str] = field(default_factory=list)
    price: str = ""
    payment_terms: str = "50% na assinatura, 50% na entrega"
    expiration_days: int = 15
    next_step: str = "Assinar contrato e realizar pagamento inicial"
    additional_notes: str = ""
    dry_run: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str = ""

    def __post_init__(self):
        if not self.expires_at:
            created = datetime.fromisoformat(self.created_at)
            self.expires_at = (created + timedelta(days=self.expiration_days)).isoformat()

    def to_dict(self) -> dict:
        return {
            "proposal_id": self.proposal_id,
            "lead_id": self.lead_id,
            "deal_id": self.deal_id,
            "client_name": self.client_name,
            "client_company": self.client_company,
            "tier": self.tier,
            "offer": self.offer,
            "scope": self.scope,
            "price": self.price,
            "payment_terms": self.payment_terms,
            "expiration_days": self.expiration_days,
            "next_step": self.next_step,
            "additional_notes": self.additional_notes,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Proposal":
        return cls(
            proposal_id=d.get("proposal_id", ""),
            lead_id=d.get("lead_id", ""),
            deal_id=d.get("deal_id", ""),
            client_name=d.get("client_name", ""),
            client_company=d.get("client_company", ""),
            tier=d.get("tier", ProposalTier.GROWTH.value),
            offer=d.get("offer", ""),
            scope=d.get("scope", []),
            price=d.get("price", ""),
            payment_terms=d.get("payment_terms", "50% na assinatura, 50% na entrega"),
            expiration_days=d.get("expiration_days", 15),
            next_step=d.get("next_step", ""),
            additional_notes=d.get("additional_notes", ""),
            dry_run=d.get("dry_run", True),
            created_at=d.get("created_at", ""),
            expires_at=d.get("expires_at", ""),
        )

    def to_markdown(self) -> str:
        scope_md = "\n".join(f"- {s}" for s in self.scope)
        return "\n".join([
            f"# Proposta Comercial",
            f"**ID:** {self.proposal_id}",
            "",
            f"## Cliente",
            f"**Nome:** {self.client_name or '—'}",
            f"**Empresa:** {self.client_company or '—'}",
            "",
            f"## Pacote: {self.tier}",
            f"**Preço:** {self.price}",
            f"**Prazo de pagamento:** {self.payment_terms}",
            "",
            f"## Escopo",
            scope_md,
            "",
            f"## Oferta",
            f"{self.offer or 'Conforme escopo acima.'}",
            "",
            f"## Condições",
            f"**Validade:** {self.expiration_days} dias (expira em {self.expires_at[:10]})",
            f"**Próximo passo:** {self.next_step}",
            "",
            f"**dry_run:** {self.dry_run} — proposta gerada localmente, nenhum envio real.",
        ])

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_pdf_placeholder(self) -> dict:
        """Placeholder — PDF generation requires external library."""
        return {
            "format": "pdf_placeholder",
            "proposal_id": self.proposal_id,
            "title": f"Proposta_{self.tier}_{self.client_company or self.client_name}",
            "note": "PDF generation requires weasyprint or similar. Use to_markdown() or to_json() for now.",
        }


class ProposalGenerator:
    """Generates template-based proposals — zero real sends, no external APIs."""

    def generate(
        self,
        tier: str = ProposalTier.GROWTH.value,
        client_name: str = "",
        client_company: str = "",
        lead_id: str = "",
        deal_id: str = "",
        **kwargs,
    ) -> Proposal:
        import uuid

        details = TIER_DETAILS.get(tier, TIER_DETAILS[ProposalTier.GROWTH.value])

        offer = kwargs.pop("offer", None) or f"Pacote {tier} — {details.get('ideal_for', '')}"
        return Proposal(
            proposal_id=str(uuid.uuid4())[:12],
            lead_id=lead_id,
            deal_id=deal_id,
            client_name=client_name,
            client_company=client_company,
            tier=tier,
            price=details["price"],
            scope=list(details["scope"]),
            offer=offer,
            **{k: v for k, v in kwargs.items() if hasattr(Proposal, k)},
        )

    def generate_all_tiers(self, client_name: str = "", lead_id: str = "") -> list[Proposal]:
        return [
            self.generate(tier=ProposalTier.STARTER.value, client_name=client_name, lead_id=lead_id),
            self.generate(tier=ProposalTier.GROWTH.value, client_name=client_name, lead_id=lead_id),
            self.generate(tier=ProposalTier.PREMIUM.value, client_name=client_name, lead_id=lead_id),
        ]
