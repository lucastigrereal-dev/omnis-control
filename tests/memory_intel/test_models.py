"""Tests for P21 Memory Intelligence models."""
from __future__ import annotations

import json
import pytest

from src.memory_intel.models import (
    MemoryIntelConfig,
    MissionSimilarityResult,
    RetrievalResult,
    PatternResult,
    MemoryIntelMode,
    INTENT_CREATE_CAMPAIGN,
    INTENT_PUBLISH_CONTENT,
    INTENT_DELIVER_TO_CLIENT,
    INTENT_ANALYZE_PERFORMANCE,
    INTENT_COMMERCIAL_OUTREACH,
    VALID_INTENTS,
    INTENT_TO_SOURCES,
    SIMILARITY_WEIGHT_INTENT,
    SIMILARITY_WEIGHT_SECTOR,
    SIMILARITY_WEIGHT_TAGS,
    SIMILARITY_WEIGHT_MODULES,
    MAX_ASSEMBLED_TEXT_CHARS,
    MAX_SNIPPET_CHARS,
    MAX_HITS_PER_SOURCE,
    MAX_RECORDS_PER_MISSION,
    MAX_SIMILAR_MISSIONS_RESULTS,
    DEFAULT_MAX_HITS,
    MIN_SIMILARITY_THRESHOLD,
    _new_id,
    _now_iso,
)
from src.memory_intel.errors import (
    MemoryIntelError,
    RetrievalError,
    WritebackError,
    ContextTooLargeError,
    NoSourcesAvailableError,
    SimilarityError,
    SafetyViolationError,
)
from src.memory_pack.models import (
    ContextPack,
    MissionMemoryRecord,
    MemoryQuery,
    MemoryHit,
    SOURCE_AKASHA,
    SOURCE_OBSIDIAN,
    SOURCE_SESSION,
    SECTOR_MIDIA,
    SECTOR_COMERCIAL,
    RELEVANCE_HIGH,
    RELEVANCE_MEDIUM,
    RELEVANCE_LOW,
    RELEVANCE_NONE,
    RELEVANCE_EXACT,
)


# ── ID and timestamp helpers ─────────────────────────────────────────────────

class TestIdAndTimestamp:
    def test_new_id_has_prefix(self):
        result = _new_id("mic")
        assert result.startswith("mic_")
        assert len(result) == len("mic_") + 8

    def test_new_ids_are_unique(self):
        ids = {_new_id("sim") for _ in range(100)}
        assert len(ids) == 100

    def test_now_iso_format(self):
        result = _now_iso()
        assert "T" in result
        assert result.endswith("Z")

    def test_now_iso_is_current(self):
        result = _now_iso()
        assert result.startswith("202")


# ── MemoryIntelMode enum ─────────────────────────────────────────────────────

class TestMemoryIntelMode:
    def test_retrieval_mode_exists(self):
        assert MemoryIntelMode.RETRIEVAL.value == "retrieval"

    def test_writeback_mode_exists(self):
        assert MemoryIntelMode.WRITEBACK.value == "writeback"

    def test_two_modes_total(self):
        assert len(MemoryIntelMode) == 2


# ── MemoryIntelConfig ────────────────────────────────────────────────────────

class TestMemoryIntelConfig:
    def test_new_creates_config(self):
        cfg = MemoryIntelConfig.new()
        assert cfg.config_id.startswith("mic_")
        assert cfg.dry_run is True

    def test_new_respects_dry_run_param(self):
        cfg = MemoryIntelConfig.new(dry_run=False)
        assert cfg.dry_run is False

    def test_load_returns_same_as_new(self):
        cfg1 = MemoryIntelConfig.new()
        cfg2 = MemoryIntelConfig.load()
        assert cfg1.max_hits == cfg2.max_hits
        assert cfg1.max_assembled_chars == cfg2.max_assembled_chars

    def test_default_max_hits(self):
        cfg = MemoryIntelConfig.new()
        assert cfg.max_hits == DEFAULT_MAX_HITS

    def test_default_limits(self):
        cfg = MemoryIntelConfig.new()
        assert cfg.max_assembled_chars == MAX_ASSEMBLED_TEXT_CHARS
        assert cfg.max_snippet_chars == MAX_SNIPPET_CHARS
        assert cfg.max_hits_per_source == MAX_HITS_PER_SOURCE
        assert cfg.max_records_per_mission == MAX_RECORDS_PER_MISSION
        assert cfg.max_similar_results == MAX_SIMILAR_MISSIONS_RESULTS

    def test_default_similarity_threshold(self):
        cfg = MemoryIntelConfig.new()
        assert cfg.similarity_threshold == MIN_SIMILARITY_THRESHOLD

    def test_default_similarity_weights(self):
        cfg = MemoryIntelConfig.new()
        assert cfg.similarity_weight_intent == SIMILARITY_WEIGHT_INTENT
        assert cfg.similarity_weight_sector == SIMILARITY_WEIGHT_SECTOR
        assert cfg.similarity_weight_tags == SIMILARITY_WEIGHT_TAGS
        assert cfg.similarity_weight_modules == SIMILARITY_WEIGHT_MODULES

    def test_get_sources_for_known_intent(self):
        cfg = MemoryIntelConfig.new()
        sources = cfg.get_sources_for_intent(INTENT_CREATE_CAMPAIGN)
        assert SOURCE_AKASHA in sources
        assert SOURCE_OBSIDIAN in sources

    def test_get_sources_for_unknown_intent_returns_fallback(self):
        cfg = MemoryIntelConfig.new()
        sources = cfg.get_sources_for_intent("nonexistent_intent")
        assert SOURCE_AKASHA in sources
        assert SOURCE_SESSION in sources

    def test_all_five_intents_have_source_mappings(self):
        cfg = MemoryIntelConfig.new()
        for intent in VALID_INTENTS:
            sources = cfg.get_sources_for_intent(intent)
            assert isinstance(sources, list)
            assert len(sources) > 0

    def test_to_dict_roundtrip(self):
        cfg = MemoryIntelConfig.new()
        data = cfg.to_dict()
        restored = MemoryIntelConfig.from_dict(data)
        assert restored.config_id == cfg.config_id
        assert restored.dry_run == cfg.dry_run
        assert restored.max_hits == cfg.max_hits

    def test_to_dict_contains_all_fields(self):
        cfg = MemoryIntelConfig.new()
        data = cfg.to_dict()
        assert "config_id" in data
        assert "intent_to_sources" in data
        assert "max_hits" in data
        assert "similarity_threshold" in data


# ── MissionSimilarityResult ──────────────────────────────────────────────────

class TestMissionSimilarityResult:
    def _make_record(self, mission_id="spr_test", sector=SECTOR_MIDIA, **kwargs):
        return MissionMemoryRecord.new(
            mission_id=mission_id,
            sector=sector,
            title="Test mission record",
            summary="A test memory record",
            key_insights=["Insight A", "Insight B"],
            **kwargs,
        )

    def test_new_creates_result(self):
        record = self._make_record()
        result = MissionSimilarityResult.new(record, 0.75)
        assert result.sim_id.startswith("sim_")
        assert result.similarity_score == 0.75

    def test_score_bounds_zero(self):
        record = self._make_record()
        result = MissionSimilarityResult.new(record, 0.0)
        assert result.similarity_score == 0.0

    def test_score_bounds_one(self):
        record = self._make_record()
        result = MissionSimilarityResult.new(record, 1.0)
        assert result.similarity_score == 1.0

    def test_score_negative_raises(self):
        record = self._make_record()
        with pytest.raises(ValueError, match="0.0 e 1.0"):
            MissionSimilarityResult.new(record, -0.1)

    def test_score_above_one_raises(self):
        record = self._make_record()
        with pytest.raises(ValueError, match="0.0 e 1.0"):
            MissionSimilarityResult.new(record, 1.1)

    def test_default_matched_on_empty(self):
        record = self._make_record()
        result = MissionSimilarityResult.new(record, 0.5)
        assert result.matched_on == []

    def test_explicit_matched_on(self):
        record = self._make_record()
        result = MissionSimilarityResult.new(record, 0.7, matched_on=["intent", "sector"])
        assert "intent" in result.matched_on
        assert "sector" in result.matched_on

    def test_relevant_learnings_from_record(self):
        record = self._make_record()
        result = MissionSimilarityResult.new(record, 0.6)
        assert result.relevant_learnings == record.key_insights

    def test_to_dict_roundtrip(self):
        record = self._make_record()
        result = MissionSimilarityResult.new(record, 0.8, matched_on=["sector"])
        data = result.to_dict()
        restored = MissionSimilarityResult.from_dict(data)
        assert restored.similarity_score == 0.8
        assert restored.matched_on == ["sector"]


# ── RetrievalResult ──────────────────────────────────────────────────────────

class TestRetrievalResult:
    def _make_pack(self, query_id="qry_test"):
        pack = ContextPack.new(query_id=query_id)
        hit = MemoryHit.new(
            query_id=query_id,
            source_type=SOURCE_AKASHA,
            source_id="src_test",
            relevance=RELEVANCE_HIGH,
            title="Test hit",
            snippet="A test snippet",
        )
        pack.assemble([hit])
        return pack

    def _make_record(self):
        return MissionMemoryRecord.new(
            mission_id="spr_test",
            sector=SECTOR_MIDIA,
            title="Test record",
            summary="Test summary",
            key_insights=["Key insight"],
        )

    def test_new_creates_result(self):
        pack = self._make_pack()
        result = RetrievalResult.new(query_id="qry_test", pack=pack)
        assert result.result_id.startswith("ret_")
        assert result.dry_run is True

    def test_is_empty_delegates_to_pack(self):
        pack = self._make_pack()
        result = RetrievalResult.new(query_id="qry_test", pack=pack)
        assert result.is_empty is False

    def test_is_empty_with_empty_pack(self):
        pack = ContextPack.new(query_id="qry_empty")
        result = RetrievalResult.new(query_id="qry_empty", pack=pack)
        assert result.is_empty is True

    def test_similarity_count_zero(self):
        pack = self._make_pack()
        result = RetrievalResult.new(query_id="qry_test", pack=pack)
        assert result.similarity_count == 0

    def test_similarity_count_with_similars(self):
        pack = self._make_pack()
        record = self._make_record()
        sim = MissionSimilarityResult.new(record, 0.7)
        result = RetrievalResult.new(query_id="qry_test", pack=pack, similar_missions=[sim])
        assert result.similarity_count == 1

    def test_top_similarity_score_empty(self):
        pack = self._make_pack()
        result = RetrievalResult.new(query_id="qry_test", pack=pack)
        assert result.top_similarity_score == 0.0

    def test_top_similarity_score_with_similars(self):
        pack = self._make_pack()
        record = self._make_record()
        sim1 = MissionSimilarityResult.new(record, 0.5)
        sim2 = MissionSimilarityResult.new(
            MissionMemoryRecord.new(
                mission_id="spr_other", sector=SECTOR_COMERCIAL,
                title="Other record", summary="Other summary",
            ),
            0.9,
        )
        result = RetrievalResult.new(
            query_id="qry_test", pack=pack, similar_missions=[sim1, sim2]
        )
        assert result.top_similarity_score == 0.9

    def test_warnings_default_empty(self):
        pack = self._make_pack()
        result = RetrievalResult.new(query_id="qry_test", pack=pack)
        assert result.warnings == []

    def test_warnings_passed_through(self):
        pack = self._make_pack()
        result = RetrievalResult.new(
            query_id="qry_test", pack=pack, warnings=["Source X unavailable"]
        )
        assert "Source X unavailable" in result.warnings

    def test_patterns_default_empty(self):
        pack = self._make_pack()
        result = RetrievalResult.new(query_id="qry_test", pack=pack)
        assert result.patterns == {}

    def test_to_dict_roundtrip(self):
        pack = self._make_pack()
        record = self._make_record()
        sim = MissionSimilarityResult.new(record, 0.6)
        result = RetrievalResult.new(
            query_id="qry_test",
            pack=pack,
            similar_missions=[sim],
            patterns={"hooks": ["test hook"]},
            warnings=["warning 1"],
        )
        data = result.to_dict()
        restored = RetrievalResult.from_dict(data)
        assert restored.result_id == result.result_id
        assert restored.similarity_count == 1
        assert restored.patterns == {"hooks": ["test hook"]}
        assert restored.warnings == ["warning 1"]


# ── PatternResult ────────────────────────────────────────────────────────────

class TestPatternResult:
    def test_new_creates_pattern(self):
        pat = PatternResult.new(sector=SECTOR_MIDIA, intent=INTENT_CREATE_CAMPAIGN)
        assert pat.pattern_id.startswith("pat_")
        assert pat.sector == SECTOR_MIDIA
        assert pat.intent == INTENT_CREATE_CAMPAIGN

    def test_is_empty_when_zero_samples(self):
        pat = PatternResult.new(sector=SECTOR_MIDIA, intent=INTENT_CREATE_CAMPAIGN)
        assert pat.is_empty is True

    def test_is_empty_false_with_samples(self):
        pat = PatternResult.new(
            sector=SECTOR_MIDIA,
            intent=INTENT_CREATE_CAMPAIGN,
            sample_count=5,
        )
        assert pat.is_empty is False

    def test_default_lists_empty(self):
        pat = PatternResult.new(sector=SECTOR_MIDIA, intent=INTENT_CREATE_CAMPAIGN)
        assert pat.successful_hooks == []
        assert pat.common_modules == []
        assert pat.failure_patterns == []
        assert pat.insights == []

    def test_with_data(self):
        pat = PatternResult.new(
            sector=SECTOR_MIDIA,
            intent=INTENT_CREATE_CAMPAIGN,
            successful_hooks=["Hook A", "Hook B"],
            common_modules=["P19", "P8"],
            failure_patterns=["Timeout on publish"],
            insights=["Best: publish before 10am"],
            sample_count=10,
        )
        assert len(pat.successful_hooks) == 2
        assert len(pat.common_modules) == 2
        assert pat.sample_count == 10

    def test_to_dict_roundtrip(self):
        pat = PatternResult.new(
            sector=SECTOR_MIDIA,
            intent=INTENT_CREATE_CAMPAIGN,
            successful_hooks=["Hook X"],
            sample_count=3,
        )
        data = pat.to_dict()
        restored = PatternResult.from_dict(data)
        assert restored.pattern_id == pat.pattern_id
        assert restored.sector == pat.sector
        assert restored.successful_hooks == ["Hook X"]
        assert restored.sample_count == 3


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    def test_valid_intents_has_five(self):
        assert len(VALID_INTENTS) == 5

    def test_intent_to_sources_has_five_keys(self):
        assert len(INTENT_TO_SOURCES) == 5

    def test_weights_sum_to_one(self):
        total = (
            SIMILARITY_WEIGHT_INTENT
            + SIMILARITY_WEIGHT_SECTOR
            + SIMILARITY_WEIGHT_TAGS
            + SIMILARITY_WEIGHT_MODULES
        )
        assert total == pytest.approx(1.0)

    def test_all_intents_in_intent_to_sources(self):
        for intent in VALID_INTENTS:
            assert intent in INTENT_TO_SOURCES


# ── Errors ───────────────────────────────────────────────────────────────────

class TestErrors:
    def test_memory_intel_error_is_exception(self):
        with pytest.raises(MemoryIntelError):
            raise MemoryIntelError("base error")

    def test_retrieval_error_chain(self):
        with pytest.raises(RetrievalError):
            raise RetrievalError("cannot retrieve")

    def test_writeback_error_chain(self):
        with pytest.raises(WritebackError):
            raise WritebackError("cannot write back")

    def test_safety_violation_chain(self):
        with pytest.raises(SafetyViolationError):
            raise SafetyViolationError("safety rule violated")

    def test_similarity_error_chain(self):
        with pytest.raises(SimilarityError):
            raise SimilarityError("similarity calc failed")

    def test_no_sources_error_chain(self):
        with pytest.raises(NoSourcesAvailableError):
            raise NoSourcesAvailableError("no sources")

    def test_context_too_large_error_chain(self):
        with pytest.raises(ContextTooLargeError):
            raise ContextTooLargeError("context too large")

    def test_all_errors_extend_base(self):
        assert issubclass(RetrievalError, MemoryIntelError)
        assert issubclass(WritebackError, MemoryIntelError)
        assert issubclass(ContextTooLargeError, MemoryIntelError)
        assert issubclass(NoSourcesAvailableError, MemoryIntelError)
        assert issubclass(SimilarityError, MemoryIntelError)
        assert issubclass(SafetyViolationError, MemoryIntelError)
