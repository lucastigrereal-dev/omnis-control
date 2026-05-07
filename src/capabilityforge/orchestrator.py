"""CapabilityForge — Super Skill que cria skills (proposal-only MVP).

build_skill() levanta NotImplementedError — apenas propose_skill() funcional.
"""
from __future__ import annotations
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .models import CreationContext, CreationState, SkillSpec, RegistryEntry
from .lifecycle import transition
from .registrymanager import RegistryManager
from .policy import PolicyEngine

logger = logging.getLogger("omnis.forge.orchestrator")
registry = RegistryManager()
policy_engine = PolicyEngine()

SKILL_REPORTS_DIR = Path(__file__).parent.parent.parent / "skill_reports"


class CapabilityForge:
    """Propoe skills (proposal-only). build_skill bloqueado para Fase 4."""

    async def propose_skill(
        self,
        gap_description: str,
        sector: str,
        requested_name: str = "",
    ) -> Dict[str, Any]:
        """Fase DISCOVERY: detecta gap e propoe spec."""
        ctx = CreationContext(
            gap_description=gap_description,
            sector=sector,
            requested_name=requested_name,
        )

        existing = registry.search(gap_description)
        if existing:
            ctx = transition(ctx, "duplicate_found")
            return {
                "state": ctx.state.name,
                "message": "Skill similar ja existe no registry.",
                "existing": existing[:3],
            }

        ctx = transition(ctx, "gap_confirmed")
        spec = SkillSpec(
            name=requested_name or f"skill_{uuid.uuid4().hex[:8]}",
            sector=sector,
            description=gap_description,
            problem_statement=gap_description,
        )
        ctx.spec = spec
        ctx = transition(ctx, "spec_ready")

        report = self._generate_proposal_report(ctx)
        logger.info("Skill proposta", extra={"sector": sector, "name": spec.name})

        return {
            "state": ctx.state.name,
            "spec": {
                "name": spec.name,
                "sector": spec.sector,
                "description": spec.description,
                "risk_level": spec.risk_level,
            },
            "report_path": str(report),
            "next_action": "Review o relatorio de proposta. build_skill() sera implementado na Fase 4.",
        }

    async def build_skill(
        self,
        spec_dict: Dict[str, Any],
        sector: str,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """BLOQUEADO — Fase 4."""
        raise NotImplementedError(
            "build_skill() nao implementado no MVP. "
            "Capability Forge esta em modo proposal-only. "
            "Use propose_skill() para gerar propostas."
        )

    async def approve_skill(self, skill_name: str, approver: str) -> Dict[str, Any]:
        """Aprova skill (modo proposal-only — registra no registry como 'approved')."""
        try:
            registry.update(skill_name, {"status": "approved", "approved_by": approver})
        except KeyError:
            # Criar entrada minima se nao existir
            entry = RegistryEntry(
                id=str(uuid.uuid4()),
                name=skill_name,
                status="approved",
                owner="unknown",
            )
            registry.add(entry)
        logger.info("Skill aprovada", extra={"skill": skill_name, "approver": approver})
        return {
            "message": f"Skill '{skill_name}' aprovada por {approver} (modo proposal-only).",
        }

    def _generate_proposal_report(self, ctx: CreationContext) -> Path:
        """Gera relatorio .md da proposta."""
        SKILL_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        path = SKILL_REPORTS_DIR / f"{ctx.spec.name}_proposal.md"
        content = f"""# Proposta de Skill: {ctx.spec.name}

**Setor:** {ctx.sector}
**Data:** {datetime.utcnow().strftime('%Y-%m-%d')}
**Estado:** {ctx.state.name}

## Descricao
{ctx.gap_description}

## Spec

| Campo | Valor |
|-------|-------|
| Nome | {ctx.spec.name} |
| Setor | {ctx.spec.sector} |
| Risk Level | {ctx.spec.risk_level} |

## Proximos Passos

1. Revisar esta proposta
2. Aguardar Fase 4 para build_skill()
3. Quando implementado: `omnis forge build --name {ctx.spec.name} --sector {ctx.sector}`
"""
        path.write_text(content, encoding="utf-8")
        return path
