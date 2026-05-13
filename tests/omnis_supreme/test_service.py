"""Tests for P20 service layer (Intake, ContextBuilder, Planner, Orchestrator)."""
from __future__ import annotations

import pytest

from src.omnis_supreme.errors import UnknownIntentError, PlanError
from src.omnis_supreme.models import SupremeMission, SupremePlan, SupremeStatus, SupremeStep
from src.omnis_supreme.service import (
    INTENT_PATTERNS,
    INTENT_TO_PIPELINE,
    SupremeContextBuilder,
    SupremeIntake,
    SupremeOrchestrator,
    SupremePlanner,
)


class TestSupremeIntake:
    def test_parse_returns_mission(self):
        intake = SupremeIntake()
        mission = intake.parse("criar campanha para hotel X")
        assert isinstance(mission, SupremeMission)
        assert mission.request_text == "criar campanha para hotel X"
        assert mission.status == SupremeStatus.INTAKE

    def test_classify_create_campaign_keyword_campanha(self):
        intake = SupremeIntake()
        assert intake._classify_intent("criar campanha de marketing") == "create_campaign"

    def test_classify_create_campaign_keyword_briefing(self):
        intake = SupremeIntake()
        assert intake._classify_intent("fazer briefing do cliente") == "create_campaign"

    def test_classify_publish_content_keyword_publicar(self):
        intake = SupremeIntake()
        assert intake._classify_intent("publicar conteúdo amanhã") == "publish_content"

    def test_classify_publish_content_keyword_post(self):
        intake = SupremeIntake()
        assert intake._classify_intent("post no feed principal") == "publish_content"

    def test_classify_deliver_to_client(self):
        intake = SupremeIntake()
        assert intake._classify_intent("entregar material ao cliente") == "deliver_to_client"

    def test_classify_analyze_performance(self):
        intake = SupremeIntake()
        assert intake._classify_intent("analisar métricas do mês") == "analyze_performance"

    def test_classify_commercial_outreach(self):
        intake = SupremeIntake()
        assert intake._classify_intent("fazer prospecção de leads") == "commercial_outreach"

    def test_classify_case_insensitive(self):
        intake = SupremeIntake()
        assert intake._classify_intent("CRIAR CAMPANHA URGENTE") == "create_campaign"

    def test_unknown_intent_raises(self):
        intake = SupremeIntake()
        with pytest.raises(UnknownIntentError):
            intake._classify_intent("xyz abc def")

    def test_parse_sets_intent_and_sector(self):
        intake = SupremeIntake()
        mission = intake.parse("publicar conteúdo")
        assert mission.intent == "publish_content"
        assert mission.sector == "midia"

    def test_sector_mapping_create_campaign(self):
        intake = SupremeIntake()
        assert intake._classify_sector("create_campaign") == "comercial"

    def test_sector_mapping_analyze(self):
        intake = SupremeIntake()
        assert intake._classify_sector("analyze_performance") == "inteligencia"


class TestSupremeContextBuilder:
    def test_build_returns_dict(self):
        builder = SupremeContextBuilder()
        result = builder.build("create_campaign")
        assert isinstance(result, dict)
        assert "sources" in result
        assert "warnings" in result

    def test_build_has_three_sources(self):
        builder = SupremeContextBuilder()
        result = builder.build("publish_content")
        sources = result["sources"]
        assert "memory" in sources
        assert "analytics" in sources
        assert "briefings" in sources

    def test_memory_source_returns_ok(self):
        builder = SupremeContextBuilder()
        result = builder._fetch_memory("create_campaign")
        assert result["status"] == "ok"

    def test_analytics_source_returns_ok(self):
        builder = SupremeContextBuilder()
        result = builder._fetch_analytics("analyze_performance")
        assert result["status"] == "ok"

    def test_briefings_source_returns_ok(self):
        builder = SupremeContextBuilder()
        result = builder._fetch_briefings("create_campaign")
        assert result["status"] == "ok"


class TestSupremePlanner:
    def test_plan_returns_supreme_plan(self):
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="create_campaign")
        plan = planner.plan(mission)
        assert isinstance(plan, SupremePlan)
        assert plan.mission_id == mission.mission_id

    def test_plan_has_steps_for_create_campaign(self):
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="create_campaign")
        plan = planner.plan(mission)
        assert len(plan.steps) == 7

    def test_plan_has_steps_for_publish_content(self):
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="publish_content")
        plan = planner.plan(mission)
        assert len(plan.steps) == 1

    def test_plan_has_steps_for_deliver(self):
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="deliver_to_client")
        plan = planner.plan(mission)
        assert len(plan.steps) == 1
        assert plan.steps[0].module_ref == "P17"

    def test_plan_has_steps_for_analyze(self):
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="analyze_performance")
        plan = planner.plan(mission)
        assert len(plan.steps) == 1
        assert plan.steps[0].operation == "calculate_roi"

    def test_plan_has_steps_for_commercial(self):
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="commercial_outreach")
        plan = planner.plan(mission)
        assert len(plan.steps) == 2

    def test_build_steps_creates_correct_count(self):
        planner = SupremePlanner()
        pipeline = [("P5", "op1"), ("P19", "op2"), ("P8", "op3")]
        steps = planner._build_steps(pipeline)
        assert len(steps) == 3
        assert all(isinstance(s, SupremeStep) for s in steps)

    def test_build_steps_has_correct_refs(self):
        planner = SupremePlanner()
        pipeline = [("P5", "brief"), ("P19", "orchestrate")]
        steps = planner._build_steps(pipeline)
        assert steps[0].module_ref == "P5"
        assert steps[0].operation == "brief"
        assert steps[1].module_ref == "P19"
        assert steps[1].operation == "orchestrate"

    def test_build_edges_linear_chain(self):
        planner = SupremePlanner()
        s1 = SupremeStep.new(module_ref="P5", operation="a")
        s2 = SupremeStep.new(module_ref="P19", operation="b")
        s3 = SupremeStep.new(module_ref="P8", operation="c")
        edges = planner._build_edges([s1, s2, s3])
        assert edges == [(s1.step_id, s2.step_id), (s2.step_id, s3.step_id)]

    def test_build_edges_single_step(self):
        planner = SupremePlanner()
        s1 = SupremeStep.new(module_ref="P5", operation="a")
        edges = planner._build_edges([s1])
        assert edges == []

    def test_topological_sort_linear(self):
        planner = SupremePlanner()
        s1 = SupremeStep.new(module_ref="P5", operation="a")
        s2 = SupremeStep.new(module_ref="P19", operation="b")
        edges = [(s1.step_id, s2.step_id)]
        result = planner._topological_sort([s1, s2], edges)
        assert result[0].step_id == s1.step_id
        assert result[1].step_id == s2.step_id

    def test_topological_sort_three_nodes(self):
        planner = SupremePlanner()
        s1 = SupremeStep.new(module_ref="P5", operation="a")
        s2 = SupremeStep.new(module_ref="P19", operation="b")
        s3 = SupremeStep.new(module_ref="P8", operation="c")
        edges = [(s1.step_id, s2.step_id), (s2.step_id, s3.step_id)]
        result = planner._topological_sort([s1, s2, s3], edges)
        assert len(result) == 3
        assert result[0].step_id == s1.step_id
        assert result[2].step_id == s3.step_id

    def test_topological_sort_cycle_detected(self):
        planner = SupremePlanner()
        s1 = SupremeStep.new(module_ref="P5", operation="a")
        s2 = SupremeStep.new(module_ref="P19", operation="b")
        edges = [(s1.step_id, s2.step_id), (s2.step_id, s1.step_id)]
        with pytest.raises(PlanError, match="Cycle detected"):
            planner._topological_sort([s1, s2], edges)

    def test_plan_dry_run_inherited(self):
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="create_campaign", dry_run=True)
        plan = planner.plan(mission)
        assert plan.dry_run is True

    def test_plan_selected_modules(self):
        planner = SupremePlanner()
        mission = SupremeMission.new(request_text="test", intent="publish_content")
        plan = planner.plan(mission)
        assert "P8" in plan.selected_modules


class TestSupremeOrchestrator:
    def test_init_default_dry_run_true(self):
        orch = SupremeOrchestrator()
        assert orch.dry_run is True

    def test_run_returns_mission(self):
        orch = SupremeOrchestrator()
        mission = orch.run("criar campanha para hotel X")
        assert isinstance(mission, SupremeMission)
        assert mission.intent == "create_campaign"

    def test_run_progresses_through_states(self):
        orch = SupremeOrchestrator()
        mission = orch.run("publicar conteúdo")
        assert mission.status == SupremeStatus.DRY_RUN

    def test_run_populates_context(self):
        orch = SupremeOrchestrator()
        mission = orch.run("analisar métricas")
        assert "sources" in mission.context

    def test_run_populates_plan(self):
        orch = SupremeOrchestrator()
        mission = orch.run("entregar ao cliente")
        assert hasattr(mission.plan, "plan_id")

    def test_run_create_campaign_has_full_pipeline(self):
        orch = SupremeOrchestrator()
        mission = orch.run("criar campanha de marketing")
        plan = mission.plan
        assert len(plan.steps) == 7


class TestIntentMappings:
    def test_all_five_intents_in_patterns(self):
        expected = {"create_campaign", "publish_content", "deliver_to_client", "analyze_performance", "commercial_outreach"}
        assert set(INTENT_PATTERNS) == expected

    def test_all_five_intents_in_pipeline(self):
        expected = {"create_campaign", "publish_content", "deliver_to_client", "analyze_performance", "commercial_outreach"}
        assert set(INTENT_TO_PIPELINE) == expected


class TestAdapterRegistry:
    def test_all_adapters_registered(self):
        from src.omnis_supreme.adapters import ADAPTER_REGISTRY
        assert len(ADAPTER_REGISTRY) == 8

    def test_adapter_keys_present(self):
        from src.omnis_supreme.adapters import ADAPTER_REGISTRY
        expected_keys = [
            ("P5", "build_campaign_brief"),
            ("P19", "orchestrate_campaign"),
            ("P19", "allocate_budget"),
            ("P19", "calculate_roi"),
            ("P19", "build_publish_queue_plan"),
            ("P8", "validate_publish_readiness"),
            ("P17", "build_delivery_package"),
            ("P19", "generate_manifest"),
        ]
        for key in expected_keys:
            assert key in ADAPTER_REGISTRY, f"Missing adapter: {key}"

    def test_each_adapter_is_callable(self):
        from src.omnis_supreme.adapters import ADAPTER_REGISTRY
        for key, fn in ADAPTER_REGISTRY.items():
            assert callable(fn), f"Adapter {key} is not callable"

    def test_mk_brief_adapter_returns_dict(self):
        from src.omnis_supreme.adapters import ADAPTER_REGISTRY
        result = ADAPTER_REGISTRY[("P5", "build_campaign_brief")]({"name": "test-campaign"}, {})
        assert isinstance(result, dict)
        assert "name" in result or "id" in result

    def test_validate_publish_adapter_returns_dict(self):
        from src.omnis_supreme.adapters import ADAPTER_REGISTRY
        result = ADAPTER_REGISTRY[("P8", "validate_publish_readiness")]({"caption": "test"}, {})
        assert isinstance(result, dict)
        assert "verdict" in result or "status" in result or "item_id" in result
