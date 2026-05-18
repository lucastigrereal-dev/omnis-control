"""Lead Pipeline — qualifica e ranqueia leads usando BANT + busca semântica.

Integra LeadQualifier (BANT scoring) com SemanticMemoryProvider (ranking semântico).
Grava leads qualificados no Akasha para memória persistente.

Uso:
    pipeline = LeadPipeline()
    report = pipeline.run(leads, dry_run=True)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.commercial.lead_qualifier import LeadQualifier, BANTResult, QUALIFIED, NURTURE
from src.commercial.hotel_lead import HotelLead


@dataclass
class LeadPipelineReport:
    total: int = 0
    qualified: int = 0
    nurture: int = 0
    low_fit: int = 0
    disqualified: int = 0
    missing_info: int = 0
    top_leads: list[BANTResult] = field(default_factory=list)
    semantic_ranked: list[tuple[str, float]] = field(default_factory=list)
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "qualified": self.qualified,
            "nurture": self.nurture,
            "low_fit": self.low_fit,
            "disqualified": self.disqualified,
            "missing_info": self.missing_info,
            "top_leads": [r.to_dict() for r in self.top_leads[:10]],
            "semantic_ranked": [(name, round(score, 3)) for name, score in self.semantic_ranked[:10]],
            "dry_run": self.dry_run,
        }

    def to_markdown(self) -> str:
        lines = [
            "# Lead Pipeline Report",
            f"**Total:** {self.total} | **Qualified:** {self.qualified} | **Nurture:** {self.nurture}",
            f"**Low Fit:** {self.low_fit} | **Disqualified:** {self.disqualified} | **Missing Info:** {self.missing_info}",
            "",
            "## Top 10 Leads (BANT Score)",
            "",
        ]
        for r in self.top_leads[:10]:
            lines.append(f"- **{r.hotel_name}** — {r.qualification_tier} ({r.total_score}/100)")
            lines.append(f"  {r.recommended_next_action}")
        if self.semantic_ranked:
            lines.append("")
            lines.append("## Semantic Ranking (similarity to ideal profile)")
            lines.append("")
            for name, score in self.semantic_ranked[:10]:
                lines.append(f"- {name}: {score:.3f}")
        return "\n".join(lines)


class LeadPipeline:
    """Qualifica leads via BANT + ranqueia semanticamente + persiste no Akasha."""

    def __init__(self, registry=None):
        self._registry = registry
        self._qualifier = LeadQualifier()

    def _get_memory(self):
        if self._registry:
            try:
                return self._registry.get("memory")
            except Exception:
                pass
        try:
            from src.providers.registry import ProviderRegistry
            return ProviderRegistry.production().get("memory")
        except Exception:
            return None

    def _get_embedder(self):
        if self._registry:
            try:
                return self._registry.get("embedding")
            except Exception:
                pass
        try:
            from src.providers.registry import ProviderRegistry
            return ProviderRegistry.production().get("embedding")
        except Exception:
            return None

    def run(self, leads: list[HotelLead], *, dry_run: bool = True) -> LeadPipelineReport:
        """Qualifica batch de leads, ranqueia semanticamente, persiste no Akasha."""
        bant_results = self._qualifier.qualify_batch(leads)
        summary = self._qualifier.summary_by_tier(bant_results)

        report = LeadPipelineReport(
            total=len(leads),
            qualified=summary.get("qualified", 0),
            nurture=summary.get("nurture", 0),
            low_fit=summary.get("low_fit", 0),
            disqualified=summary.get("disqualified", 0),
            missing_info=summary.get("missing_information", 0),
            top_leads=bant_results[:10],
            dry_run=dry_run,
        )

        # Semantic ranking — ideal profile = hotel de praia nordeste premium collab
        ideal_profile = "hotel resort pousada nordeste praia premium collab parceria influenciador Instagram"
        embedder = self._get_embedder()
        if embedder and leads:
            try:
                candidates = [f"{hl.hotel_name} {hl.niche} {hl.region} {hl.priority_tier}" for hl in leads]
                ranked = embedder.rank(ideal_profile, candidates, k=min(10, len(leads)))
                report.semantic_ranked = [(text, score) for text, score in ranked]
            except Exception:
                pass

        # Persist actionable leads to Akasha
        if not dry_run:
            memory = self._get_memory()
            if memory:
                for r in bant_results:
                    if r.qualification_tier in (QUALIFIED, NURTURE):
                        try:
                            memory.write(
                                f"lead:{r.hotel_name} tier:{r.qualification_tier} score:{r.total_score} "
                                f"action:{r.recommended_next_action}",
                                id=f"lead_{r.hotel_lead_id}",
                                metadata={"tier": r.qualification_tier, "score": r.total_score,
                                          "hotel": r.hotel_name},
                            )
                        except Exception:
                            pass

        return report

    def qualify_interior_sp(self, *, dry_run: bool = True) -> LeadPipelineReport:
        """Pipeline específico para os 150 leads de Interior SP."""
        from src.commercial.prospect_list import ProspectList
        pl = ProspectList()
        leads = [entry.hotel_lead for entry in pl.list_all()
                 if "sp" in entry.hotel_lead.region.lower() or
                    "sao paulo" in entry.hotel_lead.region.lower() or
                    "interior" in getattr(entry.hotel_lead, "city", "").lower()]
        if not leads:
            # Fall back to all leads if no SP filter matches
            leads = [entry.hotel_lead for entry in pl.list_all()]
        return self.run(leads, dry_run=dry_run)
