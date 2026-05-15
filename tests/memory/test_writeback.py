"""Tests for LearningWritebackService — Mission Journal → Memory bridge."""
from __future__ import annotations

import pytest

from src.memory.writeback import LearningWritebackService, WritebackResult
from src.missions.learning import LearningJournal, Confidence


class TestLearningWritebackService:
    def test_writeback_from_empty_journal(self, tmp_path):
        svc = LearningWritebackService(dry_run=True)
        result = svc.writeback_from_journal(
            mission_id="test-001",
            journal_dir=str(tmp_path),
        )
        assert result.total_learnings == 0
        assert result.written == 0

    def test_writeback_from_journal_with_learnings(self, tmp_path):
        journal = LearningJournal(str(tmp_path))
        journal.record(
            insight="SEO score 85 — hashtags de localizacao performam melhor",
            source="seo",
            confidence=Confidence.HIGH,
            tags=["seo", "hashtags"],
            mission_id="test-002",
            step_id="seo",
        )
        journal.record(
            insight="Caption CTA forte — 'salvar' supera 'curtir' em 3x",
            source="draft",
            confidence=Confidence.HIGH,
            tags=["caption", "cta"],
            mission_id="test-002",
            step_id="draft",
        )

        svc = LearningWritebackService(dry_run=True)
        result = svc.writeback_from_journal(
            mission_id="test-002",
            journal_dir=str(tmp_path),
            sector="midia",
        )
        assert result.total_learnings == 2
        assert result.dry_run is True

    def test_writeback_single(self):
        svc = LearningWritebackService(dry_run=True)
        result = svc.writeback_single(
            mission_id="test-003",
            insight="Turismo em Natal tem melhor engajamento com videos de praia",
            sector="midia",
            tags=["turismo", "natal"],
        )
        assert result.total_learnings == 1
        assert result.dry_run is True

    def test_writeback_result_to_dict(self):
        result = WritebackResult(
            writeback_id="wb_test",
            mission_id="test",
            total_learnings=3,
            written=2,
            blocked=1,
            approval_required=1,
            records=[{"title": "test"}],
            details=["blocked: policy"],
        )
        d = result.to_dict()
        assert d["written"] == 2
        assert d["blocked"] == 1
        assert d["records"] == [{"title": "test"}]

    def test_writeback_result_success_property(self):
        assert WritebackResult(writeback_id="w1", mission_id="m", written=2).success is True
        assert WritebackResult(writeback_id="w2", mission_id="m", total_learnings=0).success is True
        assert WritebackResult(writeback_id="w3", mission_id="m", blocked=1).success is False
