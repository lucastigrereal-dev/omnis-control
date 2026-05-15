"""W020 — E2E Dry-Run Test: complete mission lifecycle simulation.

Simulates a full mission package: contract → events → artifacts → learnings → checkpoint → report.
All file-backed, zero real integrations.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from src.missions.models import (
    MissionContract,
    BudgetCaps,
    AcceptanceCriterion,
    Sector,
    RiskLevel,
    ApprovalPolicy,
)
from src.missions.events import EventEnvelope
from src.missions.repository import JsonlRepository
from src.missions.state_machine import MissionStatus
from src.missions.artifacts import (
    Artifact,
    ArtifactKind,
    ArtifactRegistry,
    ArtifactStatus,
)
from src.missions.learning import LearningJournal, Confidence, LearningEntry
from src.missions.runtime import (
    checkpoint_mission,
    pause_mission,
    resume_mission,
    retry_mission,
    get_resume_context,
)


# ── Helpers ──────────────────────────────────────────────────────────

def _make_contract(title: str = "E2E Dry-Run Mission") -> MissionContract:
    return MissionContract(
        title=title,
        objective="Criar carrossel sobre viagem em família para @afamiliatigrereal",
        sector=Sector.MARKETING,
        user_request="Quero um carrossel de 5 slides sobre Férias de Julho em família",
        risk_level=RiskLevel.LOW,
        approval_policy=ApprovalPolicy.AUTO,
        budget=BudgetCaps(max_tokens=50000, max_cost_usd=2.0, max_duration_seconds=600, max_steps=50),
        acceptance_criteria=[
            AcceptanceCriterion(id="AC-001", description="Carrossel tem 5 slides"),
            AcceptanceCriterion(id="AC-002", description="Legenda tem CTA de salvar"),
            AcceptanceCriterion(id="AC-003", description="SEO score >= 70"),
        ],
        expected_deliverables=[
            "carousel/slides.json",
            "carousel/caption.md",
            "carousel/hashtags.txt",
            "reports/seo_audit.json",
            "reports/mission_report.md",
        ],
        tags=["carrossel", "familia", "ferias-julho"],
    )


def _emit_start(repo: JsonlRepository, mission_id: str) -> EventEnvelope:
    return repo.append_event(EventEnvelope(
        mission_id=mission_id, event_type="mission_started", sequence=0, actor="omnis",
    ))


def _emit_step(repo: JsonlRepository, mission_id: str, step_id: str, artifacts: list[str] | None = None) -> EventEnvelope:
    repo.append_event(EventEnvelope(
        mission_id=mission_id, event_type="step_started", sequence=0, actor="omnis",
        payload={"step_id": step_id},
    ))
    payload: dict = {"step_id": step_id}
    if artifacts:
        payload["artifacts"] = [{"path": a} for a in artifacts]
    return repo.append_event(EventEnvelope(
        mission_id=mission_id, event_type="step_completed", sequence=0, actor="omnis",
        payload=payload,
    ))


def _emit_artifact(repo: JsonlRepository, mission_id: str, path: str) -> EventEnvelope:
    return repo.append_event(EventEnvelope(
        mission_id=mission_id, event_type="artifact_produced", sequence=0, actor="omnis",
        payload={"artifacts": [{"path": path}]},
    ))


# ── Tests ────────────────────────────────────────────────────────────

class TestE2EDryRunPackage:
    """Simula missão completa: criação → execução → artefatos → aprendizado → conclusão."""

    def test_full_lifecycle(self, tmp_path):
        repo = JsonlRepository(base_dir=str(tmp_path / "data"))
        contract = _make_contract()
        mission_id = repo.save_contract(contract)

        # Phase 1: Start
        _emit_start(repo, mission_id)
        state = repo.project(mission_id)
        assert state.status == MissionStatus.RUNNING

        # Phase 2: Planning
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="plan_drafted", sequence=0, actor="omnis",
            payload={"steps": ["research", "draft", "design", "seo", "package"]},
        ))
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="plan_approved", sequence=0, actor="lucas",
            payload={"approved_by": "lucas"},
        ))

        # Phase 3: Research step
        _emit_step(repo, mission_id, "research", ["research/briefing.md"])
        _emit_artifact(repo, mission_id, "research/briefing.md")

        # Phase 4: Draft step (with token tracking)
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="step_started", sequence=0, actor="omnis",
            payload={"step_id": "draft"},
        ))
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="token_used", sequence=0, actor="omnis",
            delta_tokens=1500, delta_cost_usd=0.03,
        ))
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="step_completed", sequence=0, actor="omnis",
            payload={"step_id": "draft", "artifacts": [
                {"path": "carousel/slides.json"},
                {"path": "carousel/caption.md"},
            ]},
        ))
        _emit_artifact(repo, mission_id, "carousel/slides.json")
        _emit_artifact(repo, mission_id, "carousel/caption.md")

        # Phase 5: SEO audit step
        _emit_step(repo, mission_id, "seo", ["reports/seo_audit.json"])
        _emit_artifact(repo, mission_id, "reports/seo_audit.json")

        # Phase 6: Complete
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_completed", sequence=0, actor="omnis",
        ))

        # Final projection
        final_state = repo.project(mission_id)
        assert final_state.status == MissionStatus.COMPLETED
        assert len(final_state.completed_steps) == 3
        assert len(final_state.artifacts) == 4
        assert final_state.cumulative_tokens == 1500
        assert final_state.cumulative_cost_usd == 0.03

    def test_package_has_all_expected_files(self, tmp_path):
        """Verifica que o pacote final contém todos os 10 tipos de arquivo esperados."""
        repo = JsonlRepository(base_dir=str(tmp_path / "data"))
        contract = _make_contract()
        mission_id = repo.save_contract(contract)

        # Emit events covering all deliverable types
        _emit_start(repo, mission_id)
        for step, files in [
            ("research", ["research/briefing.md"]),
            ("draft", ["carousel/slides.json", "carousel/caption.md"]),
            ("hashtags", ["carousel/hashtags.txt"]),
            ("seo", ["reports/seo_audit.json"]),
            ("report", ["reports/mission_report.md"]),
        ]:
            _emit_step(repo, mission_id, step, files)
            for f in files:
                _emit_artifact(repo, mission_id, f)

        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_completed", sequence=0, actor="omnis",
        ))

        state = repo.project(mission_id)
        assert state.status == MissionStatus.COMPLETED

        # All 5 expected deliverables present
        for d in contract.expected_deliverables:
            assert any(d in a for a in state.artifacts), f"Missing: {d}"

    def test_approval_flow(self, tmp_path):
        """Verifica fluxo de aprovação: request → waiting → grant → running."""
        repo = JsonlRepository(base_dir=str(tmp_path / "data"))
        contract = _make_contract()
        mission_id = repo.save_contract(contract)

        _emit_start(repo, mission_id)

        # Request approval
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="approval_requested", sequence=0, actor="omnis",
            payload={"reason": "Verificar slides antes de finalizar"},
        ))
        state = repo.project(mission_id)
        assert state.status == MissionStatus.WAITING_APPROVAL
        assert state.approval_pending is True

        # Grant approval
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="approval_granted", sequence=0, actor="lucas",
            payload={"approved_by": "lucas", "notes": "Slide 3 ajustar cor"},
        ))
        state = repo.project(mission_id)
        assert state.status == MissionStatus.RUNNING
        assert state.approval_pending is False

    def test_pause_resume_cycle(self, tmp_path):
        """Verifica ciclo de pause → checkpoint → resume."""
        repo = JsonlRepository(base_dir=str(tmp_path / "data"))
        contract = _make_contract()
        mission_id = repo.save_contract(contract)

        _emit_start(repo, mission_id)
        _emit_step(repo, mission_id, "research", ["research/briefing.md"])

        # Pause
        result = pause_mission(mission_id, reason="Preciso validar briefing", repo=repo)
        assert result["status"] == "paused"

        state = repo.project(mission_id)
        assert state.status == MissionStatus.PAUSED

        # Resume
        result = resume_mission(mission_id, repo=repo)
        assert result["status"] == "running"
        assert result["resume_context"]["completed_steps"] == ["research"]

    def test_retry_from_failed(self, tmp_path):
        """Verifica retry de missão em estado FAILED."""
        repo = JsonlRepository(base_dir=str(tmp_path / "data"))
        contract = _make_contract()
        mission_id = repo.save_contract(contract)

        _emit_start(repo, mission_id)
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_failed", sequence=0, actor="omnis",
            payload={"error": "SEO score 55 below threshold"},
        ))

        state = repo.project(mission_id)
        assert state.status == MissionStatus.FAILED

        result = retry_mission(mission_id, repo=repo)
        assert result["status"] == "running"
        assert result["retry_attempt"] == 1

    def test_retry_limit_exceeded(self, tmp_path):
        """Verifica que retry é bloqueado quando max_retries atingido."""
        repo = JsonlRepository(base_dir=str(tmp_path / "data"))
        contract = _make_contract()
        mission_id = repo.save_contract(contract)

        _emit_start(repo, mission_id)

        # Fail and retry 3 times
        for _ in range(3):
            repo.append_event(EventEnvelope(
                mission_id=mission_id, event_type="mission_failed", sequence=0, actor="omnis",
            ))
            repo.append_event(EventEnvelope(
                mission_id=mission_id, event_type="retry_attempted", sequence=0, actor="runtime",
            ))
            repo.append_event(EventEnvelope(
                mission_id=mission_id, event_type="mission_resumed", sequence=0, actor="runtime",
            ))

        # 4th fail
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_failed", sequence=0, actor="omnis",
        ))

        result = retry_mission(mission_id, repo=repo)
        assert result["status"] == "blocked"
        assert result["retry_allowed"] is False


class TestE2EWithArtifactsAndLearning:
    """E2E com ArtifactRegistry + LearningJournal integrados."""

    def test_artifacts_registered_during_lifecycle(self, tmp_path):
        repo = JsonlRepository(base_dir=str(tmp_path / "data"))
        mission_dir = tmp_path / "mission_package"
        mission_dir.mkdir()

        contract = _make_contract()
        mission_id = repo.save_contract(contract)

        reg = ArtifactRegistry(str(mission_dir))

        # Simulate file creation
        (mission_dir / "carousel").mkdir(parents=True)
        (mission_dir / "reports").mkdir(parents=True)
        (mission_dir / "carousel" / "slides.json").write_text(
            json.dumps({"slides": 5}), encoding="utf-8"
        )
        (mission_dir / "carousel" / "caption.md").write_text("# Legenda\nCTA salvar", encoding="utf-8")
        (mission_dir / "reports" / "seo_audit.json").write_text(
            json.dumps({"score": 85}), encoding="utf-8"
        )

        # Register each
        reg.register_file("carousel/slides.json", kind=ArtifactKind.OTHER)
        reg.register_file("carousel/caption.md", kind=ArtifactKind.CAPTION)
        reg.register_file("reports/seo_audit.json", kind=ArtifactKind.REPORT)

        # Also emit events in repo
        _emit_start(repo, mission_id)
        _emit_step(repo, mission_id, "draft", ["carousel/slides.json", "carousel/caption.md"])
        _emit_step(repo, mission_id, "seo", ["reports/seo_audit.json"])
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_completed", sequence=0, actor="omnis",
        ))

        # Verify registry
        assert reg.count() == 3
        all_verified = reg.verify_all()
        assert len(all_verified["verified"]) == 3
        assert len(all_verified["corrupted"]) == 0

    def test_learnings_recorded_during_lifecycle(self, tmp_path):
        repo = JsonlRepository(base_dir=str(tmp_path / "data"))
        mission_dir = tmp_path / "mission_package"
        mission_dir.mkdir()

        contract = _make_contract()
        mission_id = repo.save_contract(contract)

        journal = LearningJournal(str(mission_dir))

        # Record learnings at each stage
        _emit_start(repo, mission_id)
        journal.record(
            insight="Briefing inicial foi vago — precisaria de 2 rounds de refinamento",
            source="research",
            confidence=Confidence.HIGH,
            tags=["briefing", "refinamento"],
            mission_id=mission_id,
            step_id="research",
        )

        _emit_step(repo, mission_id, "draft", ["carousel/slides.json"])
        journal.record(
            insight="Slide 2 ficou genérico — dados locais específicos aumentam retenção",
            source="draft",
            confidence=Confidence.MEDIUM,
            tags=["slides", "melhoria"],
            mission_id=mission_id,
            step_id="draft",
        )

        _emit_step(repo, mission_id, "seo", ["reports/seo_audit.json"])
        journal.record(
            insight="Hashtags de localização (#Natal #RN) performam melhor que genéricas",
            source="seo",
            confidence=Confidence.HIGH,
            tags=["hashtags", "seo", "padrao"],
            mission_id=mission_id,
            step_id="seo",
        )

        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_completed", sequence=0, actor="omnis",
        ))

        # Verify journal
        assert journal.count() == 3
        assert len(journal.filter_by_tag("seo")) == 1
        assert len(journal.filter_by_confidence(Confidence.HIGH)) == 2

        summary = journal.summary()
        assert summary["total"] == 3

    def test_full_package_integrity(self, tmp_path):
        """Teste completo: contract + events + artifacts + learnings + checkpoint + hash check."""
        repo = JsonlRepository(base_dir=str(tmp_path / "data"))
        mission_dir = tmp_path / "mission_package"
        mission_dir.mkdir()

        contract = _make_contract()
        mission_id = repo.save_contract(contract)

        (mission_dir / "carousel").mkdir(parents=True)
        (mission_dir / "reports").mkdir(parents=True)
        (mission_dir / "carousel" / "slides.json").write_text('{"slides":5}')
        (mission_dir / "carousel" / "caption.md").write_text("# Cap")
        (mission_dir / "reports" / "seo_audit.json").write_text('{"score":85}')
        (mission_dir / "reports" / "mission_report.md").write_text("# Relatório")

        reg = ArtifactRegistry(str(mission_dir))
        journal = LearningJournal(str(mission_dir))

        # Lifecycle
        _emit_start(repo, mission_id)
        _emit_step(repo, mission_id, "research", ["research/briefing.md"])
        _emit_artifact(repo, mission_id, "research/briefing.md")
        _emit_step(repo, mission_id, "draft", ["carousel/slides.json", "carousel/caption.md"])
        _emit_artifact(repo, mission_id, "carousel/slides.json")
        _emit_artifact(repo, mission_id, "carousel/caption.md")
        _emit_step(repo, mission_id, "seo", ["reports/seo_audit.json"])
        _emit_artifact(repo, mission_id, "reports/seo_audit.json")
        _emit_step(repo, mission_id, "report", ["reports/mission_report.md"])
        _emit_artifact(repo, mission_id, "reports/mission_report.md")

        # Register artifacts
        for path, kind in [
            ("carousel/slides.json", ArtifactKind.OTHER),
            ("carousel/caption.md", ArtifactKind.CAPTION),
            ("reports/seo_audit.json", ArtifactKind.REPORT),
            ("reports/mission_report.md", ArtifactKind.REPORT),
        ]:
            reg.register_file(path, kind=kind)

        # Record learnings
        journal.record(insight="SEO score 85 — acima do threshold de 70", confidence=Confidence.HIGH, tags=["seo"])
        journal.record(insight="Caption CTA forte — salvar > curtir", confidence=Confidence.HIGH, tags=["caption"])

        # Checkpoint
        ckpt = checkpoint_mission(mission_id, repo=repo, label="pre-complete")
        assert ckpt["checkpoint_id"]

        # Complete
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_completed", sequence=0, actor="omnis",
        ))

        # ── Integrity assertions ──
        state = repo.project(mission_id)
        assert state.status == MissionStatus.COMPLETED
        assert len(state.completed_steps) == 4
        assert len(state.artifacts) >= 4

        # Artifact hash integrity
        verify_result = reg.verify_all()
        assert len(verify_result["verified"]) == 4
        assert verify_result["corrupted"] == []
        assert verify_result["missing"] == []

        # Learning integrity
        assert journal.count() == 2
        assert len(journal.filter_by_confidence(Confidence.HIGH)) == 2

        # Checkpoint exists
        latest = repo.get_latest_checkpoint(mission_id)
        assert latest is not None
        assert latest["mission_id"] == mission_id

        # Contract hash intact
        loaded = repo.get_contract(mission_id)
        assert loaded.content_hash() == mission_id

        # Resume context coherent
        ctx = get_resume_context(mission_id, repo=repo)
        assert ctx["mission_id"] == mission_id
        assert ctx["status"] == "completed"
        assert len(ctx["completed_steps"]) == 4

        # Events ordered and complete
        events = repo.get_events(mission_id)
        sequences = [e.sequence for e in events]
        assert sequences == list(range(1, len(events) + 1))

        # All acceptance criteria referenced
        assert contract.acceptance_criteria[0].id == "AC-001"
        assert contract.acceptance_criteria[1].id == "AC-002"
        assert contract.acceptance_criteria[2].id == "AC-003"


class TestE2EBudgetEnforcement:
    """E2E com enforcement de budget."""

    def test_budget_exceeded_stops_mission(self, tmp_path):
        repo = JsonlRepository(base_dir=str(tmp_path / "data"))
        contract = MissionContract(
            title="Budget Test",
            objective="Testar estouro de budget",
            sector=Sector.RESEARCH,
            budget=BudgetCaps(max_tokens=1000, max_cost_usd=0.5, max_duration_seconds=60, max_steps=5),
        )
        mission_id = repo.save_contract(contract)

        _emit_start(repo, mission_id)

        # Simulate heavy token usage
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="token_used", sequence=0, actor="omnis",
            delta_tokens=800, delta_cost_usd=0.30,
        ))

        # Budget exceeded event
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="budget_exceeded", sequence=0, actor="omnis",
            payload={"reason": "Custo acumulado R$0.60 > cap R$0.50", "current_cost": 0.60, "cap": 0.50},
        ))

        state = repo.project(mission_id)
        assert state.budget_exceeded is True
        assert state.status == MissionStatus.WAITING_APPROVAL
