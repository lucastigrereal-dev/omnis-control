"""Squad Templates — predefined squad configurations for common business functions."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SquadTemplateType(str, Enum):
    MARKETING = "marketing"
    SALES = "sales"
    APP_FACTORY = "app_factory"
    OPS = "ops"
    SECURITY = "security"


@dataclass
class SquadTemplate:
    template_id: str = ""
    template_type: SquadTemplateType = SquadTemplateType.MARKETING
    name: str = ""
    description: str = ""
    roles: list[str] = field(default_factory=list)
    required_outputs: list[str] = field(default_factory=list)
    risk_level: str = "low"
    approval_required: bool = False
    sector: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "template_type": self.template_type.value,
            "name": self.name,
            "description": self.description,
            "roles": self.roles,
            "required_outputs": self.required_outputs,
            "risk_level": self.risk_level,
            "approval_required": self.approval_required,
            "sector": self.sector,
        }


PREDEFINED_TEMPLATES: dict[SquadTemplateType, SquadTemplate] = {
    SquadTemplateType.MARKETING: SquadTemplate(
        template_id="tpl_marketing_001",
        template_type=SquadTemplateType.MARKETING,
        name="Marketing Content Squad",
        description="Creates marketing campaigns, content calendars, captions, and visual briefs for Instagram publishing",
        roles=["marketing_strategist", "copywriter", "visual_director", "video_planner", "qa_auditor"],
        required_outputs=["strategy_brief", "caption", "visual_brief", "video_plan", "quality_report"],
        risk_level="low",
        approval_required=False,
        sector="marketing",
    ),
    SquadTemplateType.SALES: SquadTemplate(
        template_id="tpl_sales_001",
        template_type=SquadTemplateType.SALES,
        name="Sales Outreach Squad",
        description="Creates sales pitches, DM sequences, objection maps, and CRM pipeline strategies",
        roles=["sales_strategist", "copywriter", "qa_auditor"],
        required_outputs=["pitch", "dm_sequence", "objection_map", "quality_report"],
        risk_level="medium",
        approval_required=True,
        sector="sales",
    ),
    SquadTemplateType.APP_FACTORY: SquadTemplate(
        template_id="tpl_app_factory_001",
        template_type=SquadTemplateType.APP_FACTORY,
        name="App Factory Squad",
        description="Designs and architects application specs, data models, and technical PRDs",
        roles=["app_architect", "qa_auditor", "operations_manager"],
        required_outputs=["prd", "technical_spec", "data_model", "quality_report", "runbook"],
        risk_level="high",
        approval_required=True,
        sector="apps",
    ),
    SquadTemplateType.OPS: SquadTemplate(
        template_id="tpl_ops_001",
        template_type=SquadTemplateType.OPS,
        name="Operations Squad",
        description="Creates SOPs, checklists, runbooks, and workflow tracking for operational excellence",
        roles=["operations_manager", "qa_auditor"],
        required_outputs=["sop", "checklist", "runbook", "quality_report"],
        risk_level="low",
        approval_required=False,
        sector="operations",
    ),
    SquadTemplateType.SECURITY: SquadTemplate(
        template_id="tpl_security_001",
        template_type=SquadTemplateType.SECURITY,
        name="Security Audit Squad",
        description="Audits code and configurations for secrets, forbidden patterns, path traversal, and policy violations",
        roles=["security_auditor", "qa_auditor"],
        required_outputs=["security_report", "vulnerability_list", "remediation_plan", "quality_report"],
        risk_level="high",
        approval_required=True,
        sector="operations",
    ),
}


class SquadTemplateRegistry:
    """Registry of predefined squad templates for rapid squad assembly."""

    @staticmethod
    def get(template_type: SquadTemplateType) -> SquadTemplate | None:
        return PREDEFINED_TEMPLATES.get(template_type)

    @staticmethod
    def get_by_sector(sector: str) -> SquadTemplate | None:
        for tmpl in PREDEFINED_TEMPLATES.values():
            if tmpl.sector == sector:
                return tmpl
        return None

    @staticmethod
    def list_all() -> list[SquadTemplate]:
        return list(PREDEFINED_TEMPLATES.values())

    @staticmethod
    def match(request: str) -> SquadTemplate | None:
        """Match a natural language request to the best squad template."""
        lower = request.lower()

        if any(kw in lower for kw in ("seguranca", "security", "vulnerability", "audit", "auditoria")):
            return PREDEFINED_TEMPLATES.get(SquadTemplateType.SECURITY)
        if any(kw in lower for kw in ("venda", "sales", "lead", "outreach", "dm ", "pitch", "prospeccao")):
            return PREDEFINED_TEMPLATES.get(SquadTemplateType.SALES)
        if any(kw in lower for kw in ("app", "aplicativo", "fabrica", "software", "system", "codigo")):
            return PREDEFINED_TEMPLATES.get(SquadTemplateType.APP_FACTORY)
        if any(kw in lower for kw in ("sop", "checklist", "operacao", "operacoes", "workflow")):
            return PREDEFINED_TEMPLATES.get(SquadTemplateType.OPS)
        if any(kw in lower for kw in ("marketing", "campanha", "conteudo", "post", "instagram", "caption")):
            return PREDEFINED_TEMPLATES.get(SquadTemplateType.MARKETING)

        return None

    @staticmethod
    def to_dict() -> dict[str, Any]:
        return {
            "templates": {k.value: v.to_dict() for k, v in PREDEFINED_TEMPLATES.items()},
            "count": len(PREDEFINED_TEMPLATES),
        }
