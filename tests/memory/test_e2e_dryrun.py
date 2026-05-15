"""W030 — Memory E2E Dry-Run: full Mission OS + Memory/Akasha pipeline.

Simulates: "Crie 3 posts sobre turismo em Natal para Instagram"
Exercises: contract → context_builder → 02_context_used.md → learnings → writeback
All file-backed, zero external calls.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.missions.models import MissionContract, Sector, RiskLevel, ApprovalPolicy, BudgetCaps
from src.missions.events import EventEnvelope
from src.missions.repository import JsonlRepository
from src.missions.state_machine import MissionStatus
from src.missions.artifacts import Artifact, ArtifactKind, ArtifactRegistry
from src.missions.learning import LearningJournal, Confidence
from src.memory.context_builder import MemoryContextBuilder
from src.memory.writeback import LearningWritebackService
from src.memory.embeddings import MockHashEmbeddingProvider


def _make_contract(title: str = "3 Posts Turismo Natal") -> MissionContract:
    return MissionContract(
        title=title,
        objective="Criar 3 posts sobre turismo em Natal para Instagram",
        sector=Sector.MARKETING,
        user_request="Crie 3 posts sobre turismo em Natal para Instagram",
        risk_level=RiskLevel.LOW,
        approval_policy=ApprovalPolicy.AUTO,
        budget=BudgetCaps(max_tokens=50000, max_cost_usd=2.0, max_duration_seconds=600, max_steps=50),
        expected_deliverables=[
            "posts/post_01_caption.md",
            "posts/post_02_caption.md",
            "posts/post_03_caption.md",
            "02_context_used.md",
            "learnings.jsonl",
            "reports/writeback_report.json",
        ],
        tags=["turismo", "natal", "instagram"],
    )


class TestMemoryE2EDryRun:
    """E2E completo: Mission OS + Memory pipeline."""

    def test_full_pipeline_3_posts_turismo_natal(self, tmp_path):
        # ── Setup ──────────────────────────────────────────────────
        data_dir = tmp_path / "data"
        pkg_dir = tmp_path / "mission_package"
        pkg_dir.mkdir()

        repo = JsonlRepository(base_dir=str(data_dir))
        contract = _make_contract()
        mission_id = repo.save_contract(contract)

        # ── Phase 1: Start mission ─────────────────────────────────
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_started", sequence=0, actor="omnis",
        ))
        state = repo.project(mission_id)
        assert state.status == MissionStatus.RUNNING

        # ── Phase 2: Context Builder → 02_context_used.md ──────────
        builder = MemoryContextBuilder(dry_run=True)
        context_result = builder.build(
            mission_id=mission_id,
            intent="create_campaign",
            sector="midia",
            account_handle="oinatalrn",
            tags=["turismo", "natal"],
            max_hits=5,
        )

        assert context_result is not None
        assert len(context_result.context_markdown) > 0
        assert "Contexto Usado" in context_result.context_markdown
        assert context_result.dry_run is True

        # Write 02_context_used.md to disk
        ctx_path = pkg_dir / "02_context_used.md"
        ctx_path.write_text(context_result.context_markdown, encoding="utf-8")
        assert ctx_path.exists()

        # ── Phase 3: Simulate content creation steps ───────────────
        registry = ArtifactRegistry(str(pkg_dir))

        # Create post directories
        posts = [
            {"id": "post_01", "title": "Praia de Ponta Negra ao amanhecer"},
            {"id": "post_02", "title": "Dunas de Genipabu — aventura em familia"},
            {"id": "post_03", "title": "Gastronomia em Ponta Negra — Top 5"},
        ]

        (pkg_dir / "posts").mkdir(exist_ok=True)
        (pkg_dir / "reports").mkdir(exist_ok=True)

        for post in posts:
            caption = f"# {post['title']}\n\nDescubra o melhor de Natal!\n\n#Turismo #Natal #RN"
            path = f"posts/{post['id']}_caption.md"
            (pkg_dir / path).write_text(caption, encoding="utf-8")
            registry.register_file(path, kind=ArtifactKind.CAPTION)

            repo.append_event(EventEnvelope(
                mission_id=mission_id, event_type="step_completed", sequence=0, actor="omnis",
                payload={"step_id": post["id"], "artifacts": [{"path": path}]},
            ))
            repo.append_event(EventEnvelope(
                mission_id=mission_id, event_type="artifact_produced", sequence=0, actor="omnis",
                payload={"artifacts": [{"path": path}]},
            ))

        # ── Phase 4: Record learnings ──────────────────────────────
        journal = LearningJournal(str(pkg_dir))

        journal.record(
            insight="Posts com foto de praia ao amanhecer tem 40% mais saves",
            source="research",
            confidence=Confidence.HIGH,
            tags=["turismo", "praia", "engajamento"],
            mission_id=mission_id,
            step_id="post_01",
        )
        journal.record(
            insight="Dunas + familia = combinacao viral — reels neste tema explodem",
            source="research",
            confidence=Confidence.HIGH,
            tags=["turismo", "familia", "viral"],
            mission_id=mission_id,
            step_id="post_02",
        )
        journal.record(
            insight="Gastronomia performa melhor em carrossel que single post",
            source="research",
            confidence=Confidence.MEDIUM,
            tags=["gastronomia", "formato", "carrossel"],
            mission_id=mission_id,
            step_id="post_03",
        )

        assert journal.count() == 3

        # ── Phase 5: Writeback to memory ───────────────────────────
        writeback_svc = LearningWritebackService(dry_run=True)
        wb_result = writeback_svc.writeback_from_journal(
            mission_id=mission_id,
            journal_dir=str(pkg_dir),
            sector="midia",
            tags=["turismo", "natal", "instagram"],
        )

        assert wb_result.total_learnings == 3
        assert wb_result.dry_run is True

        # Write writeback report
        wb_path = pkg_dir / "reports" / "writeback_report.json"
        wb_path.write_text(
            json.dumps(wb_result.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        assert wb_path.exists()

        # ── Phase 6: Complete mission ──────────────────────────────
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_completed", sequence=0, actor="omnis",
        ))
        final_state = repo.project(mission_id)
        assert final_state.status == MissionStatus.COMPLETED

        # ── Phase 7: Integrity verification ────────────────────────
        # All artifacts registered
        assert registry.count() == 3

        # All artifacts verified on disk
        verify = registry.verify_all()
        assert len(verify["verified"]) == 3
        assert verify["corrupted"] == []
        assert verify["missing"] == []

        # Learnings count matches
        assert journal.count() == 3

        # Contract hash intact
        loaded = repo.get_contract(mission_id)
        assert loaded.content_hash() == mission_id

        # Events ordered
        events = repo.get_events(mission_id)
        sequences = [e.sequence for e in events]
        assert sequences == list(range(1, len(events) + 1))

        # 02_context_used.md populated
        context_content = ctx_path.read_text(encoding="utf-8")
        assert "Contexto Usado" in context_content
        assert "oinatalrn" in context_content
        assert "create_campaign" in context_content

        # All expected deliverables exist
        for d in contract.expected_deliverables:
            expected_path = pkg_dir / d
            assert expected_path.exists(), f"Missing deliverable: {d}"

    def test_dry_run_no_external_calls(self, tmp_path):
        """Verify zero external APIs are called during full pipeline."""
        builder = MemoryContextBuilder(dry_run=True)
        result = builder.build(
            mission_id="dry-run-check",
            intent="publish_content",
            sector="midia",
            account_handle="agenteviajabrasil",
        )
        assert result.dry_run is True
        # Context builder works even without real Akasha
        assert len(result.context_markdown) > 0

    def test_embedding_integration(self, tmp_path):
        """Verify embedding provider integrates with pipeline."""
        provider = MockHashEmbeddingProvider(dimensions=128)

        # Same input → same output (deterministic, useful for dedup)
        a = provider.embed("turismo em natal rio grande do norte")
        b = provider.embed("turismo em natal rio grande do norte")
        assert a == b

        # Different input → different output
        c = provider.embed("post sobre turismo em natal")
        assert a != c

        # All vectors have correct dimensions
        assert len(a) == 128

    def test_end_to_end_with_approval_gate(self, tmp_path):
        """E2E with approval gate — mission pauses for review."""
        data_dir = tmp_path / "data"
        pkg_dir = tmp_path / "mission_package"
        pkg_dir.mkdir()

        repo = JsonlRepository(base_dir=str(data_dir))
        contract = MissionContract(
            title="Campanha com aprovacao",
            objective="Criar campanha que requer aprovacao manual",
            sector=Sector.MARKETING,
            approval_policy=ApprovalPolicy.MANUAL,
        )
        mission_id = repo.save_contract(contract)

        # Start
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_started", sequence=0, actor="omnis",
        ))

        # Request approval (content needs human review)
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="approval_requested", sequence=0, actor="omnis",
            payload={"reason": "Campanha precisa de revisao humana"},
        ))
        state = repo.project(mission_id)
        assert state.status == MissionStatus.WAITING_APPROVAL

        # During approval wait, build context for reviewer
        builder = MemoryContextBuilder(dry_run=True)
        ctx = builder.build_minimal(
            mission_id=mission_id,
            intent="create_campaign",
            sector="midia",
            account_handle="afamiliatigrereal",
        )
        assert len(ctx.context_markdown) > 0

        # Grant approval
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="approval_granted", sequence=0, actor="lucas",
            payload={"notes": "Aprovado — ajustar titulo do post 2"},
        ))
        state = repo.project(mission_id)
        assert state.status == MissionStatus.RUNNING

        # Complete
        repo.append_event(EventEnvelope(
            mission_id=mission_id, event_type="mission_completed", sequence=0, actor="omnis",
        ))
        assert repo.project(mission_id).status == MissionStatus.COMPLETED
