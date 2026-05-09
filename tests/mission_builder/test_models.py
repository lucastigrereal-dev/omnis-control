"""Tests for MissionPlan and MissionPackageManifest models."""
import pytest
from src.mission_builder.models import MissionPlan, MissionPackageManifest


def test_mission_plan_new_creates_unique_ids():
    p1 = MissionPlan.new(
        request_text="cria carrossel",
        intent="carousel",
        deliverable="carousel_package",
        description="Carrossel de fotos",
        account_handle="afamiliatigrereal",
        format="carrossel",
        objective="engajamento",
        estimated_slots=5,
    )
    p2 = MissionPlan.new(
        request_text="cria carrossel",
        intent="carousel",
        deliverable="carousel_package",
        description="Carrossel de fotos",
        account_handle="afamiliatigrereal",
        format="carrossel",
        objective="engajamento",
        estimated_slots=5,
    )
    assert p1.mission_id.startswith("mb_")
    assert p2.mission_id.startswith("mb_")
    assert p1.mission_id != p2.mission_id


def test_mission_plan_to_dict_roundtrip():
    plan = MissionPlan.new(
        request_text="cria campanha 10 posts",
        intent="campaign",
        deliverable="campaign_package",
        description="Campanha mensal",
        account_handle="oinatalrn",
        format="campanha",
        objective="vendas",
        estimated_slots=10,
        steps=["1. Definir tema", "2. Criar calendario"],
    )
    d = plan.to_dict()
    assert d["intent"] == "campaign"
    assert d["estimated_slots"] == 10
    assert len(d["steps"]) == 2
    assert d["dry_run"] is True
    assert "created_at" in d


def test_mission_plan_from_dict():
    plan = MissionPlan.new(
        request_text="teste",
        intent="post",
        deliverable="single_post_package",
        description="Post simples",
        account_handle="lucastigrereal",
        format="feed",
        objective="engajamento",
        estimated_slots=1,
    )
    restored = MissionPlan.from_dict(plan.to_dict())
    assert restored.mission_id == plan.mission_id
    assert restored.intent == plan.intent
    assert restored.account_handle == plan.account_handle


def test_mission_package_manifest_to_dict():
    manifest = MissionPackageManifest(
        mission_id="mb_abc12345",
        request_text="cria stories",
        intent="story",
        deliverable="story_package",
        account_handle="oinatalrn",
        package_dir="/some/path/mb_abc12345",
        files=["01_mission_brief.md", "mission_manifest.json"],
        dry_run=True,
    )
    d = manifest.to_dict()
    assert d["mission_id"] == "mb_abc12345"
    assert d["intent"] == "story"
    assert "01_mission_brief.md" in d["files"]
    assert d["dry_run"] is True
