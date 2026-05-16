"""W129 — SDR Metrics & Dashboard Summary.

Computes aggregated metrics from the Commercial SDR pipeline (W121-W128).
Reads outputs from all prior waves and generates:
- Stage distribution counts
- Conversion indicators
- Package distribution
- Outreach readiness
- Follow-up overdue summary
- Dashboard summary markdown

Data-model only — no visual dashboard. All local, dry-run, zero API.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.commercial.lead_qualifier import QUALIFIED, NURTURE, LOW_FIT, DISQUALIFIED
from src.commercial.pipeline_sync import SyncStage


# ── SDR Metrics Summary ─────────────────────────────────────────────────────

@dataclass
class SDRMetricsSummary:
    """Aggregated SDR commercial pipeline metrics."""

    # Totals
    total_leads: int = 0
    total_qualified: int = 0  # BANT qualified + nurture
    total_disqualified: int = 0
    total_with_package: int = 0
    total_with_proposal: int = 0
    total_in_outreach: int = 0

    # Pipeline stage distribution
    stage_distribution: dict[str, int] = field(default_factory=dict)

    # Package distribution
    package_distribution: dict[str, int] = field(default_factory=dict)

    # Conversion indicators
    bant_to_package_rate: float = 0.0  # qualified → has package
    package_to_proposal_rate: float = 0.0  # has package → has proposal
    qualification_rate: float = 0.0  # total → qualified

    # Outreach readiness
    outreach_active: int = 0
    outreach_completed: int = 0
    followup_actions_total: int = 0
    followup_overdue: int = 0
    followup_critical: int = 0

    # Actionable
    actionable_leads: int = 0
    non_actionable_leads: int = 0

    # Scores
    avg_fit_score: float = 0.0
    avg_bant_score: float = 0.0

    # Metadata
    dashboard_summary: str = ""
    computed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def pipeline_health(self) -> str:
        """Qualitative pipeline health indicator."""
        if self.actionable_leads == 0:
            return "empty"
        if self.followup_critical > 0:
            return "attention"
        rate = self.bant_to_package_rate
        if rate >= 0.7:
            return "strong"
        if rate >= 0.4:
            return "healthy"
        return "weak"

    def to_dict(self) -> dict:
        return {
            "total_leads": self.total_leads,
            "total_qualified": self.total_qualified,
            "total_disqualified": self.total_disqualified,
            "total_with_package": self.total_with_package,
            "total_with_proposal": self.total_with_proposal,
            "total_in_outreach": self.total_in_outreach,
            "stage_distribution": self.stage_distribution,
            "package_distribution": self.package_distribution,
            "bant_to_package_rate": self.bant_to_package_rate,
            "package_to_proposal_rate": self.package_to_proposal_rate,
            "qualification_rate": self.qualification_rate,
            "outreach_active": self.outreach_active,
            "outreach_completed": self.outreach_completed,
            "followup_actions_total": self.followup_actions_total,
            "followup_overdue": self.followup_overdue,
            "followup_critical": self.followup_critical,
            "actionable_leads": self.actionable_leads,
            "non_actionable_leads": self.non_actionable_leads,
            "avg_fit_score": self.avg_fit_score,
            "avg_bant_score": self.avg_bant_score,
            "pipeline_health": self.pipeline_health,
            "dashboard_summary": self.dashboard_summary,
            "computed_at": self.computed_at,
        }


# ── SDR Metrics Computer ────────────────────────────────────────────────────

class SDRMetricsComputer:
    """Computes SDR metrics from Commercial SDR pipeline data.

    Consumes outputs from W121-W128. All local computation, zero API.
    """

    def compute(
        self,
        bant_results: list | None = None,
        package_matches: list | None = None,
        proposal_briefs: list | None = None,
        pipeline_sync_entries: list | None = None,
        outreach_sequences: list | None = None,
        followup_entries: list | None = None,
    ) -> SDRMetricsSummary:
        """Compute aggregated SDR metrics.

        All input lists are optional. Only provided data contributes to metrics.

        Args:
            bant_results: W124 BANTResult list
            package_matches: W125 PackageMatch list
            proposal_briefs: W126 ProposalBrief list
            pipeline_sync_entries: W127 PipelineSyncEntry list
            outreach_sequences: W123 OutreachSequence list
            followup_entries: W128 FollowUpEntry list
        """
        m = SDRMetricsSummary()

        # ── BANT metrics ──────────────────────────────────────────────────
        if bant_results:
            m.total_leads = len(bant_results)
            qualified = [b for b in bant_results
                         if b.qualification_tier in (QUALIFIED, NURTURE)]
            m.total_qualified = len(qualified)
            m.total_disqualified = sum(
                1 for b in bant_results if b.qualification_tier == DISQUALIFIED
            )
            m.qualification_rate = (
                m.total_qualified / m.total_leads if m.total_leads else 0.0
            )
            scores = [b.total_score for b in bant_results if b.total_score > 0]
            m.avg_bant_score = sum(scores) / len(scores) if scores else 0.0

        # ── Package metrics ───────────────────────────────────────────────
        if package_matches:
            m.total_with_package = sum(1 for pm in package_matches if pm.has_recommendation)
            pkg_dist: dict[str, int] = {}
            for pm in package_matches:
                if pm.recommended_package:
                    pkg_dist[pm.recommended_package] = pkg_dist.get(pm.recommended_package, 0) + 1
            m.package_distribution = pkg_dist

            if m.total_qualified > 0:
                m.bant_to_package_rate = m.total_with_package / m.total_qualified

        # ── Proposal metrics ──────────────────────────────────────────────
        if proposal_briefs:
            m.total_with_proposal = sum(1 for pb in proposal_briefs if pb.recommended_package)
            if m.total_with_package > 0:
                m.package_to_proposal_rate = m.total_with_proposal / m.total_with_package

        # ── Pipeline stage distribution ───────────────────────────────────
        if pipeline_sync_entries:
            stage_dist: dict[str, int] = {}
            fit_scores = []
            for se in pipeline_sync_entries:
                stage_dist[se.suggested_stage] = stage_dist.get(se.suggested_stage, 0) + 1
                if se.fit_score > 0:
                    fit_scores.append(se.fit_score)
                if se.is_actionable:
                    m.actionable_leads += 1
                else:
                    m.non_actionable_leads += 1
            m.stage_distribution = stage_dist
            m.avg_fit_score = sum(fit_scores) / len(fit_scores) if fit_scores else 0.0

        # ── Outreach metrics ──────────────────────────────────────────────
        if outreach_sequences:
            m.total_in_outreach = len(outreach_sequences)
            m.outreach_active = sum(1 for s in outreach_sequences if s.status == "active")
            m.outreach_completed = sum(1 for s in outreach_sequences if s.status == "completed")

        # ── Follow-up metrics ─────────────────────────────────────────────
        if followup_entries:
            m.followup_actions_total = len(followup_entries)
            m.followup_overdue = sum(1 for fe in followup_entries if fe.is_overdue)
            m.followup_critical = sum(
                1 for fe in followup_entries if fe.is_overdue and fe.overdue_days >= 5
            )

        # ── Generate dashboard summary ────────────────────────────────────
        m.dashboard_summary = self._render_summary(m)
        return m

    def _render_summary(self, m: SDRMetricsSummary) -> str:
        def pct(v: float) -> str:
            return f"{v:.0%}"

        lines = [
            "# SDR Pipeline Dashboard Summary",
            f"**Health:** {m.pipeline_health.upper()}",
            f"**Computed:** {m.computed_at[:19]}",
            "",
            "## Pipeline Overview",
            f"**Total Leads:** {m.total_leads}",
            f"**Qualified:** {m.total_qualified} ({pct(m.qualification_rate)})",
            f"**Disqualified:** {m.total_disqualified}",
            f"**Actionable:** {m.actionable_leads} | **Non-Actionable:** {m.non_actionable_leads}",
            "",
            "## Conversion Funnel",
            f"**Qualified → Package:** {m.total_with_package} ({pct(m.bant_to_package_rate)})",
            f"**Package → Proposal:** {m.total_with_proposal} ({pct(m.package_to_proposal_rate)})",
            "",
            "## Package Distribution",
        ]
        for pkg, count in sorted(m.package_distribution.items()):
            lines.append(f"- **{pkg}:** {count}")

        lines.extend([
            "",
            "## Pipeline by Stage",
        ])
        for stage in [SyncStage.NOVO, SyncStage.QUALIFICADO, SyncStage.PROPOSTA,
                       SyncStage.NEGOCIACAO, SyncStage.FECHADO, SyncStage.PERDIDO,
                       SyncStage.ARQUIVADO]:
            count = m.stage_distribution.get(stage, 0)
            if count > 0:
                lines.append(f"- **{stage}:** {count}")

        lines.extend([
            "",
            "## Outreach Status",
            f"**Total in Outreach:** {m.total_in_outreach}",
            f"**Active:** {m.outreach_active} | **Completed:** {m.outreach_completed}",
            f"**Follow-Up Actions:** {m.followup_actions_total}",
            f"**Overdue:** {m.followup_overdue} | **Critical:** {m.followup_critical}",
            "",
            "## Averages",
            f"**Avg Fit Score:** {m.avg_fit_score:.1f}",
            f"**Avg BANT Score:** {m.avg_bant_score:.1f}",
            "",
            "---",
            "",
            "**Disclaimer:** Metrics computed locally by OMNIS Commercial SDR.",
            "Data reflects dry-run pipeline state — not production CRM.",
            "**dry_run:** True",
        ])
        return "\n".join(lines)

    def export_summary_dict(self, m: SDRMetricsSummary) -> dict:
        """Export metrics as dict for dashboard integration."""
        return m.to_dict()
