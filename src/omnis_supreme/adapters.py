"""P20 OMNIS Supreme Activation — Adapter registry (thin lambda bridges)."""
from __future__ import annotations

from typing import Callable

from src.marketing.models import CampaignBrief
from src.marketing.service import MarketingPlanner
from src.campaign_manager.service import CampaignOrchestrator
from src.publisher_argos.models import PublisherHandoff
from src.publisher_argos.planner import PublisherArgosPlanner
from src.delivery_portal.models import Deal
from src.delivery_portal.service import DeliveryPlanner

AdapterFn = Callable[[dict, dict], dict]

_DEF_CH = [{"profile": "lucastigrereal", "role": "primary", "slot_count": 1}]
_BGT = 1000.0


def _any_brief(name: str = "default") -> CampaignBrief:
    return CampaignBrief.from_dict({"id": "brf_0000", "name": name, "objective_id": "obj_0000", "audience_id": "aud_0000", "budget": _BGT})


ADAPTER_REGISTRY: dict[tuple[str, str], AdapterFn] = {
    ("P5", "build_campaign_brief"): lambda c, x: (
        lambda mp: mp.build_campaign_brief(
            name=c.get("name", "campaign"),
            objective_id=mp.define_objective("growth", "Growth objective", "awareness").id,
            audience_id=mp.define_audience("travelers", "Travel audience").id,
        ).to_dict()
    )(MarketingPlanner(dry_run=c.get("dry_run", True))),

    ("P19", "orchestrate_campaign"): lambda c, x: CampaignOrchestrator.orchestrate_campaign(
        CampaignBrief.from_dict(c["brief"]) if "brief" in c else _any_brief(c.get("name", "default")),
        channels=c.get("channels", _DEF_CH),
        budget_total=c.get("budget_total", _BGT),
        dry_run=c.get("dry_run", True),
    ).to_dict(),

    ("P19", "allocate_budget"): lambda c, x: CampaignOrchestrator.allocate_budget(
        CampaignOrchestrator.orchestrate_campaign(
            _any_brief(c.get("name", "bgt")), channels=_DEF_CH, budget_total=_BGT, dry_run=True,
        ),
        total_budget_brl=c.get("total_budget_brl", _BGT),
    ).to_dict(),

    ("P19", "calculate_roi"): lambda c, x: CampaignOrchestrator.calculate_roi(
        CampaignOrchestrator.orchestrate_campaign(
            _any_brief(c.get("name", "roi")), channels=_DEF_CH, budget_total=_BGT, dry_run=True,
        ),
    ).to_dict(),

    ("P19", "build_publish_queue_plan"): lambda c, x: CampaignOrchestrator.build_publish_queue_plan(
        CampaignOrchestrator.orchestrate_campaign(
            _any_brief(c.get("name", "def")), channels=_DEF_CH, budget_total=_BGT, dry_run=True,
        ),
    ),

    ("P8", "validate_publish_readiness"): lambda c, x: (
        lambda pp: pp.validate_publish_readiness(
            pp.build_export_item(caption=c.get("caption", "Test caption"))
        ).to_dict()
    )(PublisherArgosPlanner(dry_run=c.get("dry_run", True))),

    ("P17", "build_delivery_package"): lambda c, x: (
        lambda pp: DeliveryPlanner(dry_run=True).build_delivery_package(
            handoff=PublisherHandoff(
                package=pp.build_argos_export_package(pp.build_queue_plan([pp.build_export_item(caption="Delivery")])),
                dry_run=False,
                approved_by="supreme",
            ),
            deal=Deal.from_dict({"id": "deal_0001", "lead_id": c.get("lead_id", "lead_0000"), "stage": "closed_won"}),
        ).to_dict()
    )(PublisherArgosPlanner(dry_run=False)),

    ("P19", "generate_manifest"): lambda c, x: CampaignOrchestrator.generate_manifest(
        CampaignOrchestrator.orchestrate_campaign(
            _any_brief(c.get("name", "def")), channels=_DEF_CH, budget_total=_BGT, dry_run=True,
        ),
    ),
}
