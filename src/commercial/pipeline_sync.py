"""W127 — Commercial Pipeline Sync Bridge.

Bridges the Commercial SDR layer (W121-W126) to the Sales/CRM pipeline (W111-W120).
Generates unified sync records per lead with suggested pipeline stage, meeting brief,
and batch export summary.

Unidirectional: Commercial → suggested stage. No data flows back to src/sales/.
PipelineStage mirrored as local constants — no import from src/sales/pipeline.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.commercial.hotel_lead import HotelLead
from src.commercial.lead_qualifier import (
    BANTResult, QUALIFIED, NURTURE, LOW_FIT, DISQUALIFIED, MISSING_INFO,
)
from src.commercial.package_matcher import PackageMatch
from src.commercial.proposal_brief import ProposalBrief


# ── Mirrored Pipeline Stages (read-only reference from src/sales/pipeline.py) ─

class SyncStage:
    """Pipeline stages mirrored from src/sales/pipeline.py::PipelineStage.
    Read-only reference — do NOT import PipelineStage directly.
    """
    NOVO = "novo"
    QUALIFICADO = "qualificado"
    PROPOSTA = "proposta"
    NEGOCIACAO = "negociacao"
    FECHADO = "fechado"
    PERDIDO = "perdido"
    ARQUIVADO = "arquivado"


STAGE_ORDER = [
    SyncStage.NOVO,
    SyncStage.QUALIFICADO,
    SyncStage.PROPOSTA,
    SyncStage.NEGOCIACAO,
    SyncStage.FECHADO,
]

# ── Stage Mapping ───────────────────────────────────────────────────────────

def _suggest_stage(
    bant_tier: str,
    has_package: bool,
    has_proposal: bool,
    priority_tier: str,
) -> str:
    """Map commercial status → suggested pipeline stage."""
    if bant_tier == DISQUALIFIED:
        return SyncStage.ARQUIVADO
    if bant_tier == MISSING_INFO:
        return SyncStage.NOVO
    if bant_tier == LOW_FIT:
        return SyncStage.NOVO

    # NURTURE or QUALIFIED
    if has_proposal:
        return SyncStage.NEGOCIACAO
    if has_package:
        return SyncStage.PROPOSTA
    if bant_tier == QUALIFIED:
        return SyncStage.QUALIFICADO
    if bant_tier == NURTURE:
        if priority_tier in ("hot", "warm"):
            return SyncStage.QUALIFICADO
        return SyncStage.NOVO

    return SyncStage.NOVO


# ── Pipeline Sync Entry ─────────────────────────────────────────────────────

@dataclass
class PipelineSyncEntry:
    """Unified record linking a HotelLead's commercial status to a pipeline stage."""

    sync_id: str
    hotel_lead_id: str
    hotel_name: str

    # Commercial status (W121-W126)
    priority_tier: str = "warm"
    fit_score: int = 0
    bant_tier: str = ""
    bant_score: int = 0
    recommended_package: str = ""
    has_proposal: bool = False
    has_package: bool = False

    # Suggested pipeline stage
    suggested_stage: str = SyncStage.NOVO

    # Meeting brief
    meeting_brief: str = ""

    # Rich context for reporting
    bant_risks: list[str] = field(default_factory=list)
    bant_reasons: list[str] = field(default_factory=list)
    package_rationale: list[str] = field(default_factory=list)
    recommended_channels: list[str] = field(default_factory=list)
    objection_count: int = 0
    next_action: str = ""
    dry_run: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def is_actionable(self) -> bool:
        return self.suggested_stage in (
            SyncStage.QUALIFICADO,
            SyncStage.PROPOSTA,
            SyncStage.NEGOCIACAO,
        )

    @property
    def stage_index(self) -> int:
        try:
            return STAGE_ORDER.index(self.suggested_stage)
        except ValueError:
            return -1

    def to_dict(self) -> dict:
        return {
            "sync_id": self.sync_id,
            "hotel_lead_id": self.hotel_lead_id,
            "hotel_name": self.hotel_name,
            "priority_tier": self.priority_tier,
            "fit_score": self.fit_score,
            "bant_tier": self.bant_tier,
            "bant_score": self.bant_score,
            "recommended_package": self.recommended_package,
            "has_proposal": self.has_proposal,
            "has_package": self.has_package,
            "suggested_stage": self.suggested_stage,
            "meeting_brief": self.meeting_brief,
            "bant_risks": self.bant_risks,
            "bant_reasons": self.bant_reasons,
            "package_rationale": self.package_rationale,
            "recommended_channels": self.recommended_channels,
            "objection_count": self.objection_count,
            "next_action": self.next_action,
            "dry_run": self.dry_run,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PipelineSyncEntry":
        return cls(
            sync_id=d["sync_id"],
            hotel_lead_id=d.get("hotel_lead_id", ""),
            hotel_name=d.get("hotel_name", ""),
            priority_tier=d.get("priority_tier", "warm"),
            fit_score=d.get("fit_score", 0),
            bant_tier=d.get("bant_tier", ""),
            bant_score=d.get("bant_score", 0),
            recommended_package=d.get("recommended_package", ""),
            has_proposal=d.get("has_proposal", False),
            has_package=d.get("has_package", False),
            suggested_stage=d.get("suggested_stage", SyncStage.NOVO),
            meeting_brief=d.get("meeting_brief", ""),
            bant_risks=d.get("bant_risks", []),
            bant_reasons=d.get("bant_reasons", []),
            package_rationale=d.get("package_rationale", []),
            recommended_channels=d.get("recommended_channels", []),
            objection_count=d.get("objection_count", 0),
            next_action=d.get("next_action", ""),
            dry_run=d.get("dry_run", True),
            created_at=d.get("created_at", ""),
        )


# ── Meeting Brief Generator ─────────────────────────────────────────────────

def _generate_meeting_brief(
    hotel_name: str,
    city: str,
    state: str,
    niche: str,
    bant_tier: str,
    bant_score: int,
    bant_reasons: list[str],
    bant_risks: list[str],
    recommended_package: str,
    package_rationale: list[str],
    recommended_channels: list[str],
    suggested_profiles: list[str],
    objection_count: int,
    objection_summary: str,
    commercial_angle: str,
    talking_points: list[str],
    expected_value: str,
    next_action: str,
) -> str:
    """Generate a 1-page SDR meeting brief in markdown."""
    location = f"{city}/{state}" if city and state else (city or state or "—")

    lines = [
        f"# SDR Meeting Brief — {hotel_name}",
        f"**Local:** {location} | **Nicho:** {niche} | **BANT:** {bant_tier} ({bant_score}/100)",
        "",
        "---",
        "",
        "## 1. Qualificacao BANT",
        "",
    ]
    for r in bant_reasons:
        lines.append(f"- {r}")

    if bant_risks:
        lines.append("")
        lines.append("**Atencoes:**")
        for r in bant_risks:
            lines.append(f"- ⚠ {r}")

    if recommended_package:
        lines.extend([
            "",
            "## 2. Pacote Recomendado",
            f"**{recommended_package}**",
        ])
        for r in package_rationale:
            lines.append(f"- {r}")

        lines.extend([
            "",
            "## 3. Angulo Comercial",
            commercial_angle,
            "",
            "## 4. Talking Points",
        ])
        for tp in talking_points:
            lines.append(f"- {tp}")

        lines.extend([
            "",
            "## 5. Valor Esperado",
            expected_value,
            "",
            "## 6. Canais Recomendados",
        ])
        for ch in recommended_channels:
            lines.append(f"- {ch}")

        if suggested_profiles:
            lines.append("")
            lines.append("**Perfis sugeridos:**")
            for p in suggested_profiles:
                lines.append(f"- {p}")

        lines.extend([
            "",
            "## 7. Objecoes Mapeadas",
            f"**{objection_count} objecoes** com respostas pre-escritas.",
            objection_summary,
        ])

    lines.extend([
        "",
        "## 8. Estrategia de Abordagem",
        f"**Proximo passo:** {next_action}",
        "",
        "---",
        "",
        "**Disclaimer:** Brief gerado pelo OMNIS Commercial Pipeline Sync.",
        "Revisar antes da reuniao. Nenhuma acao foi executada.",
        "**dry_run:** True",
    ])
    return "\n".join(lines)


# ── Pipeline Sync Bridge ────────────────────────────────────────────────────

class PipelineSyncBridge:
    """Bridges Commercial SDR (W121-W126) to Sales Pipeline stages.

    Generates PipelineSyncEntry per lead with suggested stage, meeting brief,
    and batch export summaries. Unidirectional — no data flows back to src/sales/.
    """

    def sync(
        self,
        hotel_lead: HotelLead,
        bant_result: BANTResult,
        package_match: PackageMatch | None = None,
        proposal_brief: ProposalBrief | None = None,
    ) -> PipelineSyncEntry:
        """Sync a single HotelLead to a pipeline stage suggestion.

        Args:
            hotel_lead: W121 HotelLead prospect
            bant_result: W124 BANT qualification
            package_match: W125 PackageMatch (optional — may not exist for all leads)
            proposal_brief: W126 ProposalBrief (optional — may not exist for all leads)

        Returns:
            PipelineSyncEntry with suggested stage and meeting brief
        """
        import uuid

        hl = hotel_lead
        has_package = package_match is not None and package_match.has_recommendation
        has_proposal = proposal_brief is not None and proposal_brief.recommended_package != ""

        suggested_stage = _suggest_stage(
            bant_result.qualification_tier,
            has_package,
            has_proposal,
            hl.priority_tier,
        )

        # ── Gather context for meeting brief ───────────────────────────────
        pkg = package_match.recommended_package if package_match else ""
        channels = package_match.recommended_channels if package_match else []
        profiles = package_match.suggested_profiles if package_match else []
        pkg_rationale = package_match.rationale if package_match else []
        pkg_next = package_match.next_action if package_match else bant_result.recommended_next_action

        # Talking points and angle from proposal brief if available
        if proposal_brief and proposal_brief.recommended_package:
            commercial_angle = proposal_brief.commercial_angle
            talking_points = proposal_brief.talking_points
            expected_value = proposal_brief.expected_value
            obj_count = proposal_brief.total_objections
            objection_types = sorted(
                set(o.objection_type for o in proposal_brief.objection_map)
            )
            objection_summary = (
                f"Tipos: {', '.join(objection_types)}. "
                f"Todas as objecoes tem respostas pre-escritas no Proposal Brief."
            )
            next_action = proposal_brief.recommended_next_step
        else:
            commercial_angle = ""
            talking_points = []
            expected_value = ""
            obj_count = 0
            objection_summary = "Nenhuma objecao mapeada — gerar Proposal Brief primeiro."
            next_action = pkg_next or bant_result.recommended_next_action

        # ── Generate meeting brief ─────────────────────────────────────────
        meeting_brief = _generate_meeting_brief(
            hotel_name=hl.hotel_name or hl.name,
            city=hl.city,
            state=hl.state,
            niche=hl.niche,
            bant_tier=bant_result.qualification_tier,
            bant_score=bant_result.total_score,
            bant_reasons=bant_result.reasons,
            bant_risks=bant_result.risks,
            recommended_package=pkg,
            package_rationale=pkg_rationale,
            recommended_channels=channels,
            suggested_profiles=profiles,
            objection_count=obj_count,
            objection_summary=objection_summary,
            commercial_angle=commercial_angle,
            talking_points=talking_points,
            expected_value=expected_value,
            next_action=next_action,
        )

        return PipelineSyncEntry(
            sync_id=str(uuid.uuid4())[:12],
            hotel_lead_id=hl.hotel_lead_id,
            hotel_name=hl.hotel_name or hl.name,
            priority_tier=hl.priority_tier,
            fit_score=hl.fit_score,
            bant_tier=bant_result.qualification_tier,
            bant_score=bant_result.total_score,
            recommended_package=pkg,
            has_proposal=has_proposal,
            has_package=has_package,
            suggested_stage=suggested_stage,
            meeting_brief=meeting_brief,
            bant_risks=bant_result.risks,
            bant_reasons=bant_result.reasons,
            package_rationale=pkg_rationale,
            recommended_channels=channels,
            objection_count=obj_count,
            next_action=next_action,
            dry_run=True,
        )

    def sync_batch(
        self,
        hotel_leads: list[HotelLead],
        bant_results: list[BANTResult],
        package_matches: list[PackageMatch] | None = None,
        proposal_briefs: list[ProposalBrief] | None = None,
    ) -> list[PipelineSyncEntry]:
        """Sync a batch of HotelLeads.

        Optional lists are matched by hotel_lead_id lookup.
        Results sorted by stage index (advanced stages first), then by fit_score desc.
        """
        # Build lookups
        pkg_by_id: dict[str, PackageMatch] = {}
        if package_matches:
            for pm in package_matches:
                pkg_by_id[pm.hotel_lead_id] = pm

        brief_by_id: dict[str, ProposalBrief] = {}
        if proposal_briefs:
            for pb in proposal_briefs:
                brief_by_id[pb.hotel_lead_id] = pb

        entries = []
        for hl, br in zip(hotel_leads, bant_results):
            pm = pkg_by_id.get(hl.hotel_lead_id)
            pb = brief_by_id.get(hl.hotel_lead_id)
            entries.append(self.sync(hl, br, pm, pb))

        # Sort: actionable first, then by stage index (advanced first), then fit_score desc
        entries.sort(key=lambda e: (
            0 if e.is_actionable else 1,
            -(e.stage_index),
            -e.fit_score,
        ))
        return entries

    def sync_from_prospect_list(
        self,
        prospect_list,
        bant_results: list[BANTResult],
        package_matches: list[PackageMatch] | None = None,
        proposal_briefs: list[ProposalBrief] | None = None,
    ) -> list[PipelineSyncEntry]:
        """Sync all HotelLeads in a ProspectList."""
        leads = [entry.hotel_lead for entry in prospect_list.list_all()]

        # Reorder bant_results to match lead order
        bant_by_id = {br.hotel_lead_id: br for br in bant_results}
        ordered_bant = [bant_by_id[hl.hotel_lead_id] for hl in leads
                        if hl.hotel_lead_id in bant_by_id]

        # If lengths mismatch, only sync leads that have BANT results
        if len(ordered_bant) != len(leads):
            matched_ids = {br.hotel_lead_id for br in bant_results}
            matched_leads = [hl for hl in leads if hl.hotel_lead_id in matched_ids]
            ordered_bant = [bant_by_id[hl.hotel_lead_id] for hl in matched_leads]
            return self.sync_batch(matched_leads, ordered_bant, package_matches, proposal_briefs)

        return self.sync_batch(leads, ordered_bant, package_matches, proposal_briefs)

    def summary_by_stage(self, entries: list[PipelineSyncEntry]) -> dict:
        """Count sync entries by suggested stage."""
        counts: dict[str, int] = {}
        for e in entries:
            counts[e.suggested_stage] = counts.get(e.suggested_stage, 0) + 1
        return counts

    def summary_actionable(self, entries: list[PipelineSyncEntry]) -> dict:
        """Count actionable vs non-actionable entries."""
        actionable = sum(1 for e in entries if e.is_actionable)
        return {
            "actionable": actionable,
            "non_actionable": len(entries) - actionable,
            "total": len(entries),
        }

    def export_report(self, entries: list[PipelineSyncEntry]) -> str:
        """Generate a markdown pipeline sync report for batch entries."""
        actionable = self.summary_actionable(entries)
        by_stage = self.summary_by_stage(entries)

        lines = [
            "# Commercial Pipeline Sync Report",
            f"**Total leads:** {len(entries)}",
            f"**Actionable:** {actionable['actionable']} | **Non-actionable:** {actionable['non_actionable']}",
            "",
            "## Pipeline por Estagio",
            "",
        ]
        for stage in STAGE_ORDER:
            count = by_stage.get(stage, 0)
            if count > 0:
                lines.append(f"- **{stage}:** {count}")
        archived = by_stage.get(SyncStage.ARQUIVADO, 0)
        if archived > 0:
            lines.append(f"- **{SyncStage.ARQUIVADO}:** {archived}")
        lines.append("")

        lines.append("## Leads por Estagio")
        lines.append("")

        for stage in STAGE_ORDER:
            stage_entries = [e for e in entries if e.suggested_stage == stage]
            if not stage_entries:
                continue
            lines.append(f"### {stage.upper()} ({len(stage_entries)})")
            lines.append("")
            for e in stage_entries:
                pkg = e.recommended_package or "—"
                lines.append(
                    f"- **{e.hotel_name}** — {e.bant_tier} ({e.bant_score}/100) "
                    f"→ {pkg} | Next: {e.next_action[:60]}..."
                )
            lines.append("")

        # Also include archived
        archived_entries = [e for e in entries if e.suggested_stage == SyncStage.ARQUIVADO]
        if archived_entries:
            lines.append(f"### {SyncStage.ARQUIVADO.upper()} ({len(archived_entries)})")
            lines.append("")
            for e in archived_entries:
                lines.append(f"- **{e.hotel_name}** — {e.bant_tier} ({e.bant_score}/100)")
            lines.append("")

        lines.extend([
            "---",
            "",
            "**Disclaimer:** Pipeline sync gerado pelo OMNIS Commercial Pipeline Sync Bridge.",
            "Estagios sao SUGESTOES baseadas em dados comerciais — nao refletem o pipeline real de vendas.",
            "**dry_run:** True",
        ])
        return "\n".join(lines)
