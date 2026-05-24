"""Guardrails de propagação de run_context em mission_bridge."""
from __future__ import annotations

def test_run_full_pipeline_real_passes_run_context_to_bridge(monkeypatch):
    from src.execution_graph import mission_bridge as mb
    from src.mission_orchestrator.models import OrchestratorRun
    from src.utils.run_context import RunContext

    captured: dict[str, object] = {}

    # Stub orquestrador: retorna run pronto para avançar ao grafo
    orch_run = OrchestratorRun.new(
        request_text="criar carrossel para @oinatalrn",
        dry_run=True,
        intent="content_create",
        run_id="run_ctx_real_01",
    )

    def _fake_orch_run(**_kwargs):
        return orch_run

    # Grafo fake mínimo
    class _Graph:
        squad_id = "squad_fake_01"

    def _fake_build_graph(_orch_run):
        return _Graph()

    # Bridge fake: captura kwargs da construção
    class _FakeBridge:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.selector = None

    # StepRun fake para bypass do runner real
    class _StepRun:
        graph_run_id = "grun_fake_01"

        @staticmethod
        def to_dict():
            return {"graph_run_id": "grun_fake_01"}

    def _fake_run_graph_real(_graph, _bridge, include_snapshot=True, run_id=None):
        return _StepRun()

    monkeypatch.setattr("src.mission_orchestrator.service.run", _fake_orch_run)
    monkeypatch.setattr(mb, "build_graph_from_orchestrator", _fake_build_graph)
    monkeypatch.setattr("src.agentic.skill_runner_bridge.SkillRunnerBridge", _FakeBridge)
    monkeypatch.setattr("src.execution_graph.runner.run_graph_real", _fake_run_graph_real)
    monkeypatch.setattr("src.execution_graph.store.write_manifest", lambda *_a, **_k: None)

    ctx = RunContext(run_id="ctx_run_real_777")
    mb.run_full_pipeline_real(
        request_text="criar carrossel para hotéis",
        dry_run=True,
        run_context=ctx,
    )

    # Expectativa desejada: bridge recebe mesmo run_context da run
    assert captured.get("run_context") is ctx
