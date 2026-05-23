"""DeliverableMapper — define arquivos de saída esperados por tipo de missão."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.agentic.mission_intake import MissionIntakeResult


@dataclass
class DeliverableSpec:
    filename: str
    description: str
    format: str  # md, csv, json, png, pdf, zip
    required: bool = True
    target_subdir: str = "05_outputs"


@dataclass
class DeliverableManifest:
    mission_id: str | None
    setor: str
    tipo: str
    deliverables: list[DeliverableSpec] = field(default_factory=list)
    export_hint: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "mission_id": self.mission_id,
            "setor": self.setor,
            "tipo": self.tipo,
            "deliverables": [
                {"filename": d.filename, "description": d.description,
                 "format": d.format, "required": d.required,
                 "target_subdir": d.target_subdir}
                for d in self.deliverables
            ],
            "export_hint": self.export_hint,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "DeliverableManifest":
        specs = [
            DeliverableSpec(**d) for d in data.pop("deliverables", [])
        ]
        m = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        m.deliverables = specs
        return m


# ── deliverable templates by sector + type ──────────────────────────────

_DELIVERABLE_MAP: dict[str, dict[str, list[DeliverableSpec]]] = {
    "marketing": {
        "campaign": [
            DeliverableSpec("calendario_30_dias.csv", "Calendário editorial 30 dias", "csv", target_subdir="06_exports"),
            DeliverableSpec("legendas_batch.csv", "Lote de legendas SEO", "csv", target_subdir="06_exports"),
            DeliverableSpec("campaign_brief.md", "Briefing da campanha", "md"),
            DeliverableSpec("hashtags.json", "Hashtags por plataforma", "json", target_subdir="06_exports"),
        ],
        "content": [
            DeliverableSpec("legenda_final.md", "Legenda com hook + CTA", "md"),
            DeliverableSpec("caption_variants.csv", "Variantes de legenda", "csv", target_subdir="06_exports"),
            DeliverableSpec("carrossel_slides.json", "Roteiro de slides carrossel", "json"),
            DeliverableSpec("hashtags.json", "Hashtags recomendadas", "json", target_subdir="06_exports"),
        ],
    },
    "sales": {
        "sales": [
            DeliverableSpec("lead_list.csv", "Lista de leads qualificados", "csv", target_subdir="06_exports"),
            DeliverableSpec("dm_sequence.md", "Sequência de DM para outreach", "md"),
            DeliverableSpec("proposta_comercial.md", "Proposta comercial formatada", "md", target_subdir="06_exports"),
            DeliverableSpec("pipeline_status.json", "Status do pipeline CRM", "json"),
        ],
        "campaign": [
            DeliverableSpec("outreach_batch.csv", "Lote de outreach", "csv", target_subdir="06_exports"),
            DeliverableSpec("dm_sequence.md", "Sequência de DM para campanha", "md"),
            DeliverableSpec("follow_up_schedule.json", "Cronograma de follow-up", "json"),
        ],
    },
    "app_factory": {
        "dev": [
            DeliverableSpec("PRD.md", "Product Requirements Document", "md"),
            DeliverableSpec("schema.json", "Database schema JSON", "json"),
            DeliverableSpec("api_contract.yaml", "API contract OpenAPI", "json"),
            DeliverableSpec("test_plan.md", "Plano de testes", "md"),
            DeliverableSpec("package.zip", "Pacote completo da app", "zip", target_subdir="06_exports"),
        ],
    },
    "computer_ops": {
        "ops": [
            DeliverableSpec("audit_report.md", "Relatório de auditoria", "md"),
            DeliverableSpec("health_check.json", "Health check detalhado", "json"),
            DeliverableSpec("quarantine_plan.md", "Plano de quarentena", "md"),
            DeliverableSpec("disk_usage.csv", "Uso de disco por diretório", "csv", target_subdir="06_exports"),
        ],
    },
    "finance": {
        "finance": [
            DeliverableSpec("pricing_model.csv", "Modelo de precificação", "csv", target_subdir="06_exports"),
            DeliverableSpec("revenue_report.md", "Relatório de receita", "md"),
            DeliverableSpec("cost_breakdown.json", "Breakdown de custos", "json"),
            DeliverableSpec("roi_analysis.md", "Análise de ROI", "md"),
        ],
    },
}

_DEFAULT_DELIVERABLES = [
    DeliverableSpec("mission_brief.md", "Briefing da missão", "md"),
    DeliverableSpec("execution_log.md", "Log de execução", "md"),
    DeliverableSpec("next_action.md", "Próximo passo recomendado", "md"),
]


class DeliverableMapper:
    """Mapeia (setor, tipo) → lista de deliverables esperados."""

    def map(self, intake: MissionIntakeResult) -> DeliverableManifest:
        """Retorna o manifesto de deliverables para uma missão."""
        sector_deliverables = _DELIVERABLE_MAP.get(intake.setor, {})
        specific = sector_deliverables.get(intake.tipo, [])
        all_deliverables = specific if specific else list(_DEFAULT_DELIVERABLES)

        export_hint = self._build_export_hint(all_deliverables)

        return DeliverableManifest(
            mission_id=None,  # preenchido pelo MissionEngine
            setor=intake.setor,
            tipo=intake.tipo,
            deliverables=all_deliverables,
            export_hint=export_hint,
        )

    def _build_export_hint(self, deliverables: list[DeliverableSpec]) -> str:
        exports = [d for d in deliverables if d.target_subdir == "06_exports"]
        if not exports:
            return ""
        filenames = ", ".join(d.filename for d in exports)
        return f"Exportáveis em 06_exports/: {filenames}"
