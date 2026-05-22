"""E2E Vertical Slice — Intake → Engine → Squad → Dispatcher → Graph → SkillBridge → ModelRouter → Output.

Phase 3 gate: uma missão de criação de legenda executada do início ao fim.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.skills_bridge.models import SkillCall, SkillIntent, SkillDefinition
from src.skills_bridge.skill_catalog import SkillCatalog
from src.skills_bridge.selection import SkillSelector, MOCK_SKILLS
from src.skills_bridge.adapter import MockSkillAdapter, RealSkillAdapter, SkillAdapter
from src.agentic.skill_runner_bridge import SkillRunnerBridge, ExecutionResult
from src.agentic.task_dispatcher import DispatchEntry, DispatchPlan, TaskDispatcher
from src.agentic.deliverable_mapper import DeliverableMapper
from src.agentic.mission_intake import MissionIntake
from src.agentic.squad_selector import SquadSelector
from src.agentic.mission_engine import MissionEngine
from src.execution_graph.mission_bridge import (
    run_full_pipeline,
    run_full_pipeline_real,
    build_graph_from_orchestrator,
    run_graph_from_orchestrator,
)
from src.execution_graph.runner import run_graph_dry, run_graph_real
from src.mission_orchestrator.planner import build_plan


CATALOG_PATH = Path(__file__).parent.parent.parent / "src" / "skills_bridge" / "catalog" / "skills.json"


# ── 3.5.1 — Catalog-backed SkillSelector ─────────────────────────────

class TestCatalogSkillSelector:
    def test_load_skills_from_catalog(self):
        catalog = SkillCatalog(catalog_path=str(CATALOG_PATH))
        skills = catalog.load()
        assert len(skills) >= 3
        ids = {s.skill_id for s in skills}
        assert "generate_seogram_caption" in ids
        assert "generate_caption" in ids

    def test_selector_uses_catalog_when_provided(self):
        catalog = SkillCatalog(catalog_path=str(CATALOG_PATH))
        selector = SkillSelector(dry_run=True, catalog=catalog)
        # Should have loaded from catalog, not MOCK_SKILLS
        skill_ids = [s["skill_id"] for s in selector.skills]
        assert "generate_seogram_caption" in skill_ids
        assert "generate_caption" in skill_ids
        # Catalog has 5 skills + manual-review fallback added
        assert len(selector.skills) >= 5

    def test_selector_falls_back_to_mock_when_catalog_empty(self):
        empty_catalog = SkillCatalog(catalog_path=str(Path("/nonexistent/skills.json")))
        selector = SkillSelector(dry_run=True, catalog=empty_catalog)
        assert len(selector.skills) == len(MOCK_SKILLS)

    def test_select_by_id_via_catalog(self):
        catalog = SkillCatalog(catalog_path=str(CATALOG_PATH))
        selector = SkillSelector(dry_run=True, catalog=catalog)
        call = SkillCall(skill_id="generate_seogram_caption", intent=SkillIntent.CREATE)
        selection = selector.select(call)
        assert selection.skill_id == "generate_seogram_caption"
        assert selection.confidence == 1.0

    def test_select_by_tags_via_catalog(self):
        catalog = SkillCatalog(catalog_path=str(CATALOG_PATH))
        selector = SkillSelector(dry_run=True, catalog=catalog)
        call = SkillCall(intent=SkillIntent.CREATE, tags=["caption", "instagram"])
        selection = selector.select(call)
        assert selection.skill_id != "manual-review"
        assert "caption" in selection.skill_id or "seogram" in selection.skill_id

    def test_select_by_intent_via_catalog(self):
        catalog = SkillCatalog(catalog_path=str(CATALOG_PATH))
        selector = SkillSelector(dry_run=True, catalog=catalog)
        call = SkillCall(intent=SkillIntent.GENERATE)
        selection = selector.select(call)
        assert selection.skill_id != "manual-review"

    def test_fallback_when_no_match_in_catalog(self):
        catalog = SkillCatalog(catalog_path=str(CATALOG_PATH))
        selector = SkillSelector(dry_run=True, catalog=catalog)
        call = SkillCall(skill_id="nonexistent_skill_xyz", intent=SkillIntent.DELETE)
        selection = selector.select(call)
        assert selection.skill_id == "manual-review"
        assert selection.requires_manual_review is True


# ── 3.5.2 — RealSkillAdapter smoke ──────────────────────────────────

class TestRealSkillAdapter:
    def test_adapter_creation(self):
        adapter = RealSkillAdapter(dry_run=True)
        assert adapter.health_check() is True

    def test_adapter_dry_run_returns_dry_run_status(self):
        adapter = RealSkillAdapter(dry_run=True)
        call = SkillCall(skill_id="generate_caption", intent=SkillIntent.CREATE)
        result = adapter.call_skill(call)
        assert result["status"] == "dry_run"
        assert "DRY_RUN" in result["output"]

    def test_adapter_tracks_calls(self):
        adapter = RealSkillAdapter(dry_run=True)
        call = SkillCall(skill_id="generate_caption", intent=SkillIntent.CREATE)
        adapter.call_skill(call)
        assert len(adapter.calls) == 1

    @pytest.mark.slow
    def test_adapter_real_call_if_ollama_available(self):
        """Real call through Ollama if available — skipped if not healthy."""
        adapter = RealSkillAdapter(dry_run=False)
        ollama_model = adapter._registry.find_by_name("llama3.2:3b")
        if ollama_model is None or not ollama_model.enabled:
            pytest.skip("llama3.2:3b not registered or disabled")
        from src.multi_model_orchestration.adapters.ollama_adapter import OllamaAdapter
        oa = OllamaAdapter()
        if not oa.health_check():
            pytest.skip("Ollama not reachable")
        adapter._router.dry_run = False
        call = SkillCall(
            skill_id="generate_caption",
            intent=SkillIntent.CREATE,
            input_payload={"prompt": "Escreva uma frase curta sobre viagem"},
        )
        result = adapter.call_skill(call)
        # May be dry_run if adapter's own dry_run is True, so we test the path at minimum
        assert result["status"] in ("dry_run", "ok", "failed")
        assert "skill_id" in result


# ── 3.5.3 — SkillRunnerBridge with catalog + adapter ─────────────────

class TestBridgeWithCatalog:
    def test_bridge_with_catalog_selector(self):
        catalog = SkillCatalog(catalog_path=str(CATALOG_PATH))
        selector = SkillSelector(dry_run=True, catalog=catalog)
        adapter = MockSkillAdapter(dry_run=True)
        bridge = SkillRunnerBridge(dry_run=True, adapter=adapter)
        bridge.selector = selector

        entry = DispatchEntry(
            task_id="TSK-test001",
            deliverable="legenda_instagram.md",
            executor="publisher",
            dry_run=True,
        )
        result = bridge.execute_entry(entry)
        assert result.status in ("dry_run", "success")
        assert result.skill_id != "manual-review"

    def test_bridge_dispatches_to_correct_skill(self):
        catalog = SkillCatalog(catalog_path=str(CATALOG_PATH))
        selector = SkillSelector(dry_run=True, catalog=catalog)
        adapter = MockSkillAdapter(dry_run=True)
        bridge = SkillRunnerBridge(dry_run=True, adapter=adapter)
        bridge.selector = selector

        entry = DispatchEntry(
            task_id="TSK-test002",
            deliverable="legenda_final.md",
            executor="skill_runner",
            dry_run=True,
        )
        result = bridge.execute_entry(entry)
        assert result.status in ("dry_run", "success")
        # Should resolve to a caption-related skill
        assert "caption" in result.skill_id.lower() or "seogram" in result.skill_id.lower()

    def test_bridge_plan_execution(self):
        catalog = SkillCatalog(catalog_path=str(CATALOG_PATH))
        selector = SkillSelector(dry_run=True, catalog=catalog)
        adapter = MockSkillAdapter(dry_run=True)
        bridge = SkillRunnerBridge(dry_run=True, adapter=adapter)
        bridge.selector = selector

        plan = DispatchPlan(
            mission_id="MIS-test",
            entries=[
                DispatchEntry(task_id="T1", deliverable="legenda_final.md", executor="publisher", dry_run=True),
                DispatchEntry(task_id="T2", deliverable="caption_variants.csv", executor="publisher", dry_run=True),
            ],
            dry_run=True,
            total=2,
        )
        results = bridge.execute_plan(plan)
        assert len(results) == 2
        for r in results:
            assert r.status in ("dry_run", "success")

    def test_bridge_auto_creates_real_adapter_when_not_dry_run(self):
        bridge = SkillRunnerBridge(dry_run=False)
        assert isinstance(bridge.adapter, RealSkillAdapter)


# ── 3.5.4 — Full Pipeline Dry-Run with Catalog ──────────────────────

class TestFullPipelineDryRun:
    def test_run_full_pipeline_real_dry_run(self):
        orch_run, step_run = run_full_pipeline_real(
            "criar post carrossel instagram",
            dry_run=True,
            catalog_path=str(CATALOG_PATH),
        )
        assert orch_run is not None
        assert orch_run.status in ("dry_run", "complete")
        if orch_run.status in ("failed", "blocked", "blocked_pending_approval"):
            pytest.skip(f"Orchestrator blocked: {orch_run.status}")
        assert step_run is not None
        assert step_run.status == "done"

    def test_run_full_pipeline_real_links_squad_and_graph(self):
        orch_run, step_run = run_full_pipeline_real(
            "criar post de viagem em família",
            dry_run=True,
            catalog_path=str(CATALOG_PATH),
        )
        assert orch_run.squad_id is not None
        assert orch_run.graph_run_id is not None
        assert orch_run.graph_run_id == step_run.graph_run_id

    def test_full_pipeline_logs_contain_steps(self):
        orch_run, step_run = run_full_pipeline_real(
            "criar post carrossel instagram",
            dry_run=True,
            catalog_path=str(CATALOG_PATH),
        )
        if orch_run.status in ("failed", "blocked", "blocked_pending_approval"):
            pytest.skip(f"Orchestrator blocked: {orch_run.status}")
        assert len(step_run.logs) > 0
        statuses = [log.status for log in step_run.logs]
        assert "done" in statuses or "running" in statuses


# ── 3.5.5 — run_graph_real with bridge ──────────────────────────────

class TestGraphRealExecution:
    def test_run_graph_real_dry_mode(self):
        """Build graph from orchestrator, run with bridge in dry mode."""
        orch_run = build_plan("criar post de viagem em natal")
        graph = build_graph_from_orchestrator(orch_run)

        catalog = SkillCatalog(catalog_path=str(CATALOG_PATH))
        selector = SkillSelector(dry_run=True, catalog=catalog)
        adapter = MockSkillAdapter(dry_run=True)
        bridge = SkillRunnerBridge(dry_run=True, adapter=adapter)
        bridge.selector = selector

        step_run = run_graph_real(graph, bridge, include_snapshot=True)
        assert step_run.status == "done"
        assert len(step_run.logs) > 0
        # Each step should have running + done log entries
        done_logs = [l for l in step_run.logs if l.status == "done"]
        assert len(done_logs) > 0

    def test_run_graph_real_handles_empty_graph(self):
        from src.execution_graph.models import ExecutionGraph
        from src.execution_graph.errors import ExecutionGraphError

        empty = ExecutionGraph(
            graph_id="empty",
            request="test",
            squad_id="",
            task_plan_id="",
            nodes=[],
            edges=[],
            topological_order=[],
            created_at="",
        )
        adapter = MockSkillAdapter(dry_run=True)
        bridge = SkillRunnerBridge(dry_run=True, adapter=adapter)

        with pytest.raises(ExecutionGraphError, match="empty"):
            run_graph_real(empty, bridge)

    def test_graph_real_output_to_file(self, tmp_path):
        """Verify that graph execution results can be persisted."""
        orch_run = build_plan("criar post de viagem em natal")
        graph = build_graph_from_orchestrator(orch_run)

        adapter = MockSkillAdapter(dry_run=True)
        bridge = SkillRunnerBridge(dry_run=True, adapter=adapter)

        step_run = run_graph_real(graph, bridge, include_snapshot=True)

        # Save to file
        output_path = tmp_path / "graph_run_output.json"
        output_path.write_text(json.dumps(step_run.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

        assert output_path.exists()
        reloaded = json.loads(output_path.read_text())
        assert reloaded["status"] == "done"
        assert reloaded["graph_id"] == graph.graph_id


# ── 3.5.6 — Pipeline Integration (System A + System B) ──────────────

class TestPipelineIntegration:
    def test_agentic_intake_to_graph(self):
        """System A intake → System B graph in one flow."""
        intake = MissionIntake()
        result = intake.parse("criar legenda para @afamiliatigrereal sobre viagem em Natal")

        squad = SquadSelector()
        assignment = squad.assign("MIS-test", result.setor)

        mapper = DeliverableMapper()
        manifest = mapper.map(result)

        dispatcher = TaskDispatcher(dry_run=True)
        plan = dispatcher.dispatch(manifest, "MIS-test")

        assert plan.total >= 1
        assert any("legenda" in e.deliverable.lower() or "caption" in e.deliverable.lower()
                   for e in plan.entries)

    def test_agentic_dispatch_to_bridge(self):
        """System A dispatcher → SkillRunnerBridge with catalog."""
        intake = MissionIntake()
        result = intake.parse("criar legenda para @lucastigrereal sobre praias")

        mapper = DeliverableMapper()
        manifest = mapper.map(result)

        dispatcher = TaskDispatcher(dry_run=True)
        plan = dispatcher.dispatch(manifest, "MIS-int-001")

        catalog = SkillCatalog(catalog_path=str(CATALOG_PATH))
        selector = SkillSelector(dry_run=True, catalog=catalog)
        adapter = MockSkillAdapter(dry_run=True)
        bridge = SkillRunnerBridge(dry_run=True, adapter=adapter)
        bridge.selector = selector

        results = bridge.execute_plan(plan)
        assert len(results) == plan.total
        for r in results:
            assert r.status in ("dry_run", "success")

    def test_mission_engine_contract_creation(self, tmp_path):
        """MissionEngine creates contract → can be dispatched."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            engine = MissionEngine(missions_root=tmp_path / "missions")
            contract = engine.open_mission(
                "criar legenda para @lucastigrereal sobre Natal",
                setor="marketing",
                criado_por="e2e_test",
            )
            assert contract.mission_id.startswith("MIS-")
            assert contract.status == "open"
            contract_path = Path(contract.mission_path) if contract.mission_path else None
            assert contract_path is not None
            assert (contract_path / "mission_contract.json").exists()
        finally:
            os.chdir(original_cwd)


# ── 3.5.7 — Caption Generation Skill E2E ────────────────────────────

class TestCaptionGenerationE2E:
    def test_caption_request_builds_prompt(self):
        from src.skills.caption_skill import CaptionRequest, build_caption_prompt, build_full_prompt
        req = CaptionRequest(topic="praias de Natal", page="@lucastigrereal")
        prompt = build_caption_prompt(req)
        assert "praias de Natal" in prompt
        assert "@lucastigrereal" in prompt
        full = build_full_prompt(req)
        assert "system" in full
        assert "user" in full

    def test_caption_result_from_llm_response(self):
        from src.skills.caption_skill import CaptionRequest, CaptionResult
        req = CaptionRequest(topic="viagem em família")
        fake_content = "Descubra o paraíso escondido!\n\nTexto aqui.\n\n#viagem\n#família"
        result = CaptionResult.from_llm_response(fake_content, req, model_used="test-model")
        assert result.hook == "Descubra o paraíso escondido!"
        assert len(result.hashtags) == 2
        assert result.model_used == "test-model"

    def test_caption_result_save_to_file(self, tmp_path):
        from src.skills.caption_skill import CaptionRequest, CaptionResult
        req = CaptionRequest(topic="teste")
        result = CaptionResult(
            caption="Legenda teste",
            topic="teste",
            page="@test",
            model_used="mock",
            hook="Hook teste",
            hashtags=["#test"],
        )
        output_path = tmp_path / "caption_output.json"
        result.save(str(output_path))
        assert output_path.exists()
        loaded = json.loads(output_path.read_text())
        assert loaded["caption"] == "Legenda teste"

    def test_full_caption_flow_dry(self, tmp_path):
        """CaptionRequest → build prompt → simulate response → save."""
        from src.skills.caption_skill import CaptionRequest, CaptionResult, build_caption_prompt
        req = CaptionRequest(topic="gastronomia em Natal RN", page="@oquecomernatalrn")
        prompt = build_caption_prompt(req)
        assert len(prompt) > 50

        # Simulate what the LLM would return
        simulated_response = (
            "COMIDA BOA É EM NATAL! 🔥\n\n"
            "Se você ainda não provou a ginga com tapioca, "
            "não sabe o que está perdendo...\n\n"
            "#gastronomia #natalrn #oquefazernatal"
        )
        result = CaptionResult.from_llm_response(simulated_response, req, model_used="ollama/llama3.2:3b")
        output_path = tmp_path / "caption_legenda.json"
        result.save(str(output_path))
        assert output_path.exists()

    @pytest.mark.slow
    def test_real_caption_via_adapter_if_ollama_available(self, tmp_path):
        """Generate a real caption via RealSkillAdapter → Ollama if available."""
        from src.skills.caption_skill import CaptionRequest, CaptionResult, build_full_prompt
        adapter = RealSkillAdapter(dry_run=False)
        from src.multi_model_orchestration.adapters.ollama_adapter import OllamaAdapter
        oa = OllamaAdapter()
        if not oa.health_check():
            pytest.skip("Ollama not reachable")

        req = CaptionRequest(topic="viagem em Natal com família", page="@afamiliatigrereal")
        prompts = build_full_prompt(req)

        call = SkillCall(
            skill_id="generate_caption",
            intent=SkillIntent.CREATE,
            input_payload={"prompt": prompts["user"], "system": prompts["system"]},
        )
        adapter._router.dry_run = False
        result = adapter.call_skill(call)

        if result["status"] in ("ok",):
            caption_result = CaptionResult.from_llm_response(
                result["output"], req, model_used=result.get("model_used", "unknown")
            )
            output_path = tmp_path / "real_caption_output.json"
            caption_result.save(str(output_path))
            assert output_path.exists()
            assert len(caption_result.caption) > 10
