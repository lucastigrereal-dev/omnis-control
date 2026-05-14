"""Tests for P21 Memory Intelligence similarity module."""
from __future__ import annotations

import pytest

from src.memory_intel.similarity import find_similar_missions, compute_similarity_score
from src.memory_pack.models import MissionMemoryRecord
from src.memory_pack.models import SECTOR_MIDIA, SECTOR_COMERCIAL, SECTOR_PRODUTO


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_records():
    return [
        MissionMemoryRecord.new(
            mission_id="spr_001",
            sector=SECTOR_MIDIA,
            title="Campanha Hotel Natal 2026",
            summary="Campanha gerou 3 collabs",
            key_insights=["Hotels respondem melhor quarta"],
            decisions=["Precificar Growth a R$990"],
            outcomes=["success_rate=100%"],
            tags=["success", "campaign", "hotel"],
            metadata={"intent": "create_campaign"},
        ),
        MissionMemoryRecord.new(
            mission_id="spr_002",
            sector=SECTOR_MIDIA,
            title="Falha: publish tarde",
            summary="Post 23h teve 80% menos engagement",
            key_insights=["Publicar entre 9h-11h"],
            decisions=["Nao publicar apos 22h"],
            outcomes=["step_failed"],
            tags=["failure", "publish", "timing"],
            metadata={"intent": "publish_content"},
        ),
        MissionMemoryRecord.new(
            mission_id="spr_003",
            sector=SECTOR_COMERCIAL,
            title="SDR Hotels Interior SP",
            summary="150 leads, 12 respostas",
            key_insights=["DM direta funciona melhor"],
            tags=["success", "sdr", "outreach"],
            metadata={"intent": "commercial_outreach"},
        ),
        MissionMemoryRecord.new(
            mission_id="spr_004",
            sector=SECTOR_PRODUTO,
            title="Bug fix: briefing.py",
            summary="Corrigido FileNotFoundError",
            key_insights=["Sempre verificar diretorios"],
            tags=["bugfix", "P16"],
            metadata={"intent": "create_campaign"},
        ),
    ]


# ── find_similar_missions ───────────────────────────────────────────────────

class TestFindSimilarMissions:
    def test_exact_intent_and_sector_match(self, sample_records):
        results = find_similar_missions(
            intent="create_campaign",
            sector=SECTOR_MIDIA,
            tags=[],
            past_records=sample_records,
        )
        assert len(results) > 0
        top = results[0]
        assert top.similarity_score == pytest.approx(0.70)  # 0.40 + 0.30

    def test_only_sector_match(self, sample_records):
        results = find_similar_missions(
            intent="unknown_intent",
            sector=SECTOR_MIDIA,
            tags=[],
            past_records=sample_records,
        )
        top = results[0]
        assert top.similarity_score == pytest.approx(0.30)  # only sector

    def test_only_intent_match(self, sample_records):
        results = find_similar_missions(
            intent="publish_content",
            sector="financeiro",
            tags=[],
            past_records=sample_records,
        )
        top = results[0]
        assert top.similarity_score == pytest.approx(0.40)  # only intent

    def test_tags_overlap_boosts_score(self, sample_records):
        results_no_tags = find_similar_missions(
            intent="create_campaign",
            sector=SECTOR_MIDIA,
            tags=[],
            past_records=sample_records,
        )
        results_with_tags = find_similar_missions(
            intent="create_campaign",
            sector=SECTOR_MIDIA,
            tags=["campaign", "hotel"],
            past_records=sample_records,
        )
        assert results_with_tags[0].similarity_score > results_no_tags[0].similarity_score

    def test_scores_bounded_by_one(self, sample_records):
        results = find_similar_missions(
            intent="create_campaign",
            sector=SECTOR_MIDIA,
            tags=["success", "campaign", "hotel", "P19", "P8"],
            past_records=sample_records,
        )
        for r in results:
            assert 0.0 <= r.similarity_score <= 1.0

    def test_results_sorted_descending(self, sample_records):
        results = find_similar_missions(
            intent="create_campaign",
            sector=SECTOR_MIDIA,
            tags=[],
            past_records=sample_records,
        )
        for i in range(len(results) - 1):
            assert results[i].similarity_score >= results[i + 1].similarity_score

    def test_respects_limit(self, sample_records):
        results = find_similar_missions(
            intent="create_campaign",
            sector=SECTOR_MIDIA,
            tags=[],
            past_records=sample_records,
            limit=2,
        )
        assert len(results) <= 2

    def test_empty_records(self):
        results = find_similar_missions(
            intent="create_campaign",
            sector=SECTOR_MIDIA,
            tags=[],
            past_records=[],
        )
        assert results == []

    def test_no_matches_zero_score(self, sample_records):
        results = find_similar_missions(
            intent="nonexistent",
            sector="financeiro",
            tags=[],
            past_records=sample_records,
        )
        assert len(results) == 4  # all records returned, even with 0.0 scores
        assert results[-1].similarity_score == 0.0

    def test_returns_mission_similarity_results(self, sample_records):
        results = find_similar_missions(
            intent="create_campaign",
            sector=SECTOR_MIDIA,
            tags=[],
            past_records=sample_records,
        )
        for r in results:
            assert r.sim_id.startswith("sim_")

    def test_matched_on_tracks_match_types(self, sample_records):
        results = find_similar_missions(
            intent="create_campaign",
            sector=SECTOR_MIDIA,
            tags=[],
            past_records=sample_records,
        )
        top = results[0]
        assert "intent" in top.matched_on
        assert "sector" in top.matched_on


# ── compute_similarity_score ────────────────────────────────────────────────

class TestComputeSimilarityScore:
    def test_full_match(self, sample_records):
        score = compute_similarity_score(
            intent="create_campaign",
            sector=SECTOR_MIDIA,
            tags=["campaign"],
            record=sample_records[0],
        )
        assert score == pytest.approx(0.90)  # intent(0.40) + sector(0.30) + tags(0.20*1/1=0.20)

    def test_only_intent(self, sample_records):
        score = compute_similarity_score(
            intent="publish_content",
            sector="financeiro",
            tags=[],
            record=sample_records[1],
        )
        assert score == pytest.approx(0.40)

    def test_only_sector(self, sample_records):
        score = compute_similarity_score(
            intent="nonexistent",
            sector=SECTOR_MIDIA,
            tags=[],
            record=sample_records[0],
        )
        assert score == pytest.approx(0.30)

    def test_no_match_zero(self, sample_records):
        score = compute_similarity_score(
            intent="nonexistent",
            sector="financeiro",
            tags=[],
            record=sample_records[0],
        )
        assert score == 0.0

    def test_score_bounded(self, sample_records):
        score = compute_similarity_score(
            intent="create_campaign",
            sector=SECTOR_MIDIA,
            tags=["success", "campaign", "hotel", "extra1", "extra2"],
            record=sample_records[0],
        )
        assert 0.0 <= score <= 1.0
