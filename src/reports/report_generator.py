"""ReportGenerator — consolida dados da missão em relatorio_final.md."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.agentic.mission_engine import MissionContract
from src.agentic.mission_intake import MissionIntakeResult
from src.agentic.deliverable_mapper import DeliverableManifest


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class MissionReport:
    mission_id: str
    generated_at: str = field(default_factory=_now_iso)
    contract: Optional[MissionContract] = None
    intake: Optional[MissionIntakeResult] = None
    manifest: Optional[DeliverableManifest] = None
    execution_notes: str = ""
    next_action: str = ""
    status: str = "draft"

    def to_markdown(self) -> str:
        lines = [
            f"# Relatório Final — {self.mission_id}",
            "",
            f"**Gerado em:** {self.generated_at}",
            f"**Status:** {self.status}",
            "",
        ]

        if self.contract:
            lines.extend([
                "## Dados da Missão",
                "",
                f"- **Objetivo:** {self.contract.objetivo}",
                f"- **Setor:** {self.contract.setor}",
                f"- **Criado por:** {self.contract.criado_por}",
                f"- **Aberto em:** {self.contract.timestamp}",
                f"- **Fechado em:** {self.contract.closed_at or '—'}",
                "",
            ])

        if self.intake:
            lines.extend([
                "## Análise da Missão",
                "",
                f"- **Tipo detectado:** {self.intake.tipo}",
                f"- **Risco:** {self.intake.risco}",
                f"- **Prazo:** {self.intake.prazo or 'sem prazo definido'}",
            ])
            if self.intake.warnings:
                lines.append("- **Alertas:**")
                for w in self.intake.warnings:
                    lines.append(f"  - {w}")
            lines.append("")

        if self.manifest and self.manifest.deliverables:
            lines.extend([
                "## Entregáveis",
                "",
                "| Arquivo | Formato | Descrição | Status |",
                "|---|---|---|---|",
            ])
            for d in self.manifest.deliverables:
                badge = "obrigatório" if d.required else "opcional"
                lines.append(f"| `{d.filename}` | {d.format} | {d.description} | {badge} |")
            lines.append("")

            if self.manifest.export_hint:
                lines.append(f"**Export:** {self.manifest.export_hint}")
                lines.append("")

        if self.execution_notes:
            lines.extend([
                "## Resumo da Execução",
                "",
                self.execution_notes,
                "",
            ])

        if self.next_action:
            lines.extend([
                "## Próximo Passo",
                "",
                self.next_action,
                "",
            ])

        lines.extend([
            "---",
            f"*Relatório gerado por OMNIS Supreme em {self.generated_at}*",
        ])

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "generated_at": self.generated_at,
            "contract": self.contract.to_dict() if self.contract else None,
            "intake": self.intake.to_dict() if self.intake else None,
            "manifest": self.manifest.to_dict() if self.manifest else None,
            "execution_notes": self.execution_notes,
            "next_action": self.next_action,
            "status": self.status,
        }


class ReportGenerator:
    """Gera relatorio_final.md consolidado da missão."""

    def generate(
        self,
        contract: MissionContract,
        intake: Optional[MissionIntakeResult] = None,
        manifest: Optional[DeliverableManifest] = None,
        execution_notes: str = "",
        next_action: str = "",
    ) -> MissionReport:
        """Cria MissionReport e escreve relatorio_final.md no diretório da missão."""
        report = MissionReport(
            mission_id=contract.mission_id,
            contract=contract,
            intake=intake,
            manifest=manifest,
            execution_notes=execution_notes,
            next_action=next_action,
        )

        if contract.mission_path:
            mission_dir = Path(contract.mission_path)
            report_path = mission_dir / "relatorio_final.md"
            report_path.write_text(report.to_markdown(), encoding="utf-8")

        return report

    def generate_summary(self, contract: MissionContract) -> str:
        """Mini-relatório textual rápido."""
        parts = [
            f"Missão: {contract.mission_id}",
            f"Objetivo: {contract.objetivo}",
            f"Setor: {contract.setor}",
            f"Status: {contract.status}",
        ]
        if contract.closed_at:
            parts.append(f"Fechada: {contract.closed_at}")
        return " | ".join(parts)
