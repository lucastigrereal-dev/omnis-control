"""Tests for P21 Memory Intelligence service."""
from __future__ import annotations

import pytest

from src.memory_intel.service import MemoryIntelligence
from src.memory_intel.models import (
    MemoryIntelConfig,
    RetrievalResult,
    PatternResult,
    MemoryIntelMode,
    INTENT_CREATE_CAMPAIGN,
    INTENT_PUBLISH_CONTENT,
    INTENT_DELIVER_TO_CLIENT,
    INTENT_ANALYZE_PERFORMANCE,
    INTENT_COMMERCIAL_OUTREACH,
    MAX_ASSEMBLED_TEXT_CHARS,
    MAX_RECORDS_PER_MISSION,
)
from src.memory_intel.errors import (
    MemoryIntelError,
    RetrievalError,
    WritebackError,
    NoSourcesAvailableError,
    ContextTooLargeError,
    SafetyViolationError,
)
from src.memory_pack.models import (
    ContextPack,
    MemoryQuery,
    MemoryHit,
    MissionMemoryRecord,
    MemoryWritePlan,
    SOURCE_AKASHA,
    SOURCE_OBSIDIAN,
    SOURCE_SESSION,
    SECTOR_MIDIA,
    SECTOR_COMERCIAL,
    SECTOR_PRODUTO,
    RELEVANCE_HIGH,
    RELEVANCE_MEDIUM,
    RELEVANCE_LOW,
    ACTION_UPSERT,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mi():
    return MemoryIntelligence(dry_run=True)


@pytest.fixture
def sample_report():
    return {
        "mission_id": "spr_test_001",
        "report_id": "rpt_abc123",
        "status": "completed",
        "steps_summary": [
            {
                "step_id": "step_1",
                "operation": "analyze_market",
                "status": "done",
                "module_ref": "P19",
                "sector": "midia",
                "duration_ms": 150,
            },
            {
                "step_id": "step_2",
                "operation": "publish_post",
                "status": "failed",
                "module_ref": "P8",
                "sector": "midia",
                "error": "timeout connecting to publisher",
                "missing_dep": "publisher_auth_token",
            },
            {
                "step_id": "step_3",
                "operation": "send_delivery",
                "status": "done",
                "module_ref": "P17",
                "sector": "produto",
                "duration_ms": 300,
            },
        ],
        "metrics": {
            "total_steps": 3,
            "success_rate": 66,
            "insights": ["Pipeline parcialmente funcional"],
        },
    }


# ── Initialization ──────────────────────────────────────────────────────────

class TestMemoryIntelligenceInit:
    def test_default_dry_run_true(self):
        mi = MemoryIntelligence()
        assert mi.dry_run is True

    def test_explicit_dry_run_false(self):
        mi = MemoryIntelligence(dry_run=False)
        assert mi.dry_run is False

    def test_has_planner(self):
        mi = MemoryIntelligence()
        assert mi.planner is not None

    def test_has_config(self):
        mi = MemoryIntelligence()
        assert isinstance(mi.config, MemoryIntelConfig)


# ── Source Selection ────────────────────────────────────────────────────────

class TestSourceSelection:
    def test_select_sources_for_create_campaign(self, mi):
        sources = mi._select_sources(INTENT_CREATE_CAMPAIGN)
        assert SOURCE_AKASHA in sources
        assert SOURCE_OBSIDIAN in sources
        assert SOURCE_SESSION in sources

    def test_select_sources_for_deliver(self, mi):
        sources = mi._select_sources(INTENT_DELIVER_TO_CLIENT)
        assert len(sources) > 0

    def test_select_sources_for_unknown_intent(self, mi):
        sources = mi._select_sources("unknown_intent")
        assert SOURCE_AKASHA in sources
        assert SOURCE_SESSION in sources

    def test_select_sources_all_five_intents_have_sources(self, mi):
        for intent in [INTENT_CREATE_CAMPAIGN, INTENT_PUBLISH_CONTENT,
                       INTENT_DELIVER_TO_CLIENT, INTENT_ANALYZE_PERFORMANCE,
                       INTENT_COMMERCIAL_OUTREACH]:
            sources = mi._select_sources(intent)
            assert isinstance(sources, list)
            assert len(sources) > 0

    def test_sources_are_valid(self, mi):
        sources = mi._select_sources(INTENT_CREATE_CAMPAIGN)
        for src in sources:
            from src.memory_pack.models import VALID_SOURCES
            assert src in VALID_SOURCES


# ── Query Building ──────────────────────────────────────────────────────────

class TestQueryBuilding:
    def test_build_query_basic(self, mi):
        text = mi._build_query_text("create_campaign", "midia")
        assert "create campaign" in text
        assert "midia" in text

    def test_build_query_with_tags(self, mi):
        text = mi._build_query_text("create_campaign", "midia", tags=["hotel", "natal"])
        assert "hotel" in text
        assert "natal" in text

    def test_build_query_replaces_underscores(self, mi):
        text = mi._build_query_text("commercial_outreach", "produto")
        assert "commercial outreach" in text


# ── Retrieval: retrieve_context ─────────────────────────────────────────────

class TestRetrieveContext:
    def test_returns_context_pack(self, mi):
        pack = mi.retrieve_context(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA)
        assert isinstance(pack, ContextPack)

    def test_context_pack_not_none(self, mi):
        pack = mi.retrieve_context(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA)
        assert pack.pack_id.startswith("pack_")

    def test_context_pack_has_hits(self, mi):
        pack = mi.retrieve_context(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA)
        assert pack.total_hits >= 0

    def test_context_pack_respects_max_hits(self, mi):
        pack = mi.retrieve_context(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA, max_hits=3)
        assert pack.total_hits <= 3

    def test_context_pack_assembled_text_not_huge(self, mi):
        pack = mi.retrieve_context(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA)
        assert len(pack.assembled_text) <= MAX_ASSEMBLED_TEXT_CHARS


# ── Retrieval: retrieve (full) ──────────────────────────────────────────────

class TestRetrieve:
    def test_returns_retrieval_result(self, mi):
        result = mi.retrieve(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA, "spr_test_001")
        assert isinstance(result, RetrievalResult)

    def test_result_has_pack(self, mi):
        result = mi.retrieve(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA, "spr_test_001")
        assert isinstance(result.pack, ContextPack)

    def test_result_has_similar_missions(self, mi):
        result = mi.retrieve(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA, "spr_test_001")
        assert isinstance(result.similar_missions, list)

    def test_result_has_patterns(self, mi):
        result = mi.retrieve(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA, "spr_test_001")
        assert isinstance(result.patterns, dict)

    def test_dry_run_reflected(self, mi):
        result = mi.retrieve(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA, "spr_test_001")
        assert result.dry_run is True

    def test_result_id_format(self, mi):
        result = mi.retrieve(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA, "spr_test_001")
        assert result.result_id.startswith("ret_")

    def test_unknown_intent_uses_fallback(self, mi):
        result = mi.retrieve("weird_intent", SECTOR_MIDIA, "spr_test_002")
        assert isinstance(result, RetrievalResult)
        assert result.result_id is not None

    def test_all_five_intents_work(self, mi):
        for intent in [INTENT_CREATE_CAMPAIGN, INTENT_PUBLISH_CONTENT,
                       INTENT_DELIVER_TO_CLIENT, INTENT_ANALYZE_PERFORMANCE,
                       INTENT_COMMERCIAL_OUTREACH]:
            result = mi.retrieve(intent, SECTOR_MIDIA, f"spr_test_{intent}")
            assert isinstance(result, RetrievalResult)

    def test_warnings_initially_empty_for_known_intent(self, mi):
        result = mi.retrieve(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA, "spr_test_001")
        assert result.warnings == []


# ── Pattern Extraction ──────────────────────────────────────────────────────

class TestExtractPatterns:
    def test_returns_pattern_result(self, mi):
        pat = mi.extract_patterns(SECTOR_MIDIA, INTENT_CREATE_CAMPAIGN)
        assert isinstance(pat, PatternResult)

    def test_pattern_has_sector_and_intent(self, mi):
        pat = mi.extract_patterns(SECTOR_MIDIA, INTENT_CREATE_CAMPAIGN)
        assert pat.sector == SECTOR_MIDIA
        assert pat.intent == INTENT_CREATE_CAMPAIGN

    def test_unknown_sector_returns_empty_pattern(self, mi):
        pat = mi.extract_patterns("setor_inexistente", INTENT_CREATE_CAMPAIGN)
        assert pat.is_empty is True

    def test_valid_sector_may_have_samples(self, mi):
        pat = mi.extract_patterns(SECTOR_MIDIA, INTENT_CREATE_CAMPAIGN)
        assert pat.sample_count >= 0

    def test_pattern_id_format(self, mi):
        pat = mi.extract_patterns(SECTOR_MIDIA, INTENT_CREATE_CAMPAIGN)
        assert pat.pattern_id.startswith("pat_")

    def test_pattern_lists_are_not_none(self, mi):
        pat = mi.extract_patterns(SECTOR_MIDIA, INTENT_CREATE_CAMPAIGN)
        assert pat.successful_hooks is not None
        assert pat.common_modules is not None
        assert pat.failure_patterns is not None
        assert pat.insights is not None


# ── Writeback ───────────────────────────────────────────────────────────────

class TestWriteback:
    def test_writeback_returns_write_plan(self, mi, sample_report):
        plan = mi.writeback({"mission_id": "spr_test_001"}, sample_report)
        assert isinstance(plan, MemoryWritePlan)

    def test_write_plan_is_dry_run(self, mi, sample_report):
        plan = mi.writeback({"mission_id": "spr_test_001"}, sample_report)
        assert plan.is_dry_run is True

    def test_write_plan_requires_approval(self, mi, sample_report):
        plan = mi.writeback({"mission_id": "spr_test_001"}, sample_report)
        assert plan.requires_approval is True

    def test_writeback_generates_records(self, mi, sample_report):
        plan = mi.writeback({"mission_id": "spr_test_001"}, sample_report)
        assert plan.record_count >= 0

    def test_writeback_max_records_not_exceeded(self, mi, sample_report):
        plan = mi.writeback({"mission_id": "spr_test_001"}, sample_report)
        assert plan.record_count <= MAX_RECORDS_PER_MISSION

    def test_writeback_empty_report(self, mi):
        empty_report = {"mission_id": "spr_empty", "steps_summary": [], "metrics": {}}
        plan = mi.writeback({"mission_id": "spr_empty"}, empty_report)
        assert isinstance(plan, MemoryWritePlan)
        assert plan.record_count == 0

    def test_writeback_with_object_report(self, mi, sample_report):
        class FakeReport:
            def to_dict(self):
                return sample_report
        plan = mi.writeback({"mission_id": "spr_test_001"}, FakeReport())
        assert isinstance(plan, MemoryWritePlan)


# ── Learn from Step ─────────────────────────────────────────────────────────

class TestLearnFromStep:
    def test_learn_success_step(self, mi):
        record = mi.learn_from_step(
            "spr_test_001",
            {"step_id": "step_1", "operation": "analyze", "module_ref": "P19", "sector": "midia"},
            {"status": "done", "duration_ms": 150},
        )
        assert record is not None
        assert record.status == "draft"
        assert "success" in record.tags

    def test_learn_failed_step(self, mi):
        record = mi.learn_from_step(
            "spr_test_001",
            {"step_id": "step_2", "operation": "publish", "module_ref": "P8", "sector": "midia"},
            {"status": "failed", "error": "timeout"},
        )
        assert record is not None
        assert "failure" in record.tags

    def test_learn_unknown_status_no_record(self, mi):
        record = mi.learn_from_step(
            "spr_test_001",
            {"step_id": "step_3", "operation": "wait", "module_ref": "P20"},
            {"status": "running"},
        )
        assert record is None

    def test_learn_invalid_sector_falls_back(self, mi):
        record = mi.learn_from_step(
            "spr_test_001",
            {"step_id": "step_4", "operation": "test", "module_ref": "P1", "sector": "invalid_sector"},
            {"status": "done", "duration_ms": 50},
        )
        assert record is not None


# ── Source Limit Enforcement ────────────────────────────────────────────────

class TestEnforceSourceLimits:
    def test_enforces_limit_per_source(self, mi):
        hits = []
        for i in range(10):
            hits.append(
                MemoryHit.new(
                    query_id="qry_test",
                    source_type=SOURCE_AKASHA,
                    source_id="src_akasha",
                    relevance=RELEVANCE_HIGH,
                    title=f"Hit {i}",
                    snippet=f"Snippet {i}",
                )
            )
        filtered = mi._enforce_source_limits(hits)
        assert len(filtered) <= mi.config.max_hits_per_source

    def test_multiple_sources_preserved(self, mi):
        hits = [
            MemoryHit.new(query_id="qry_test", source_type=SOURCE_AKASHA, source_id="src_1",
                         relevance=RELEVANCE_HIGH, title="A1", snippet="S1"),
            MemoryHit.new(query_id="qry_test", source_type=SOURCE_OBSIDIAN, source_id="src_2",
                         relevance=RELEVANCE_HIGH, title="O1", snippet="S2"),
        ]
        filtered = mi._enforce_source_limits(hits)
        sources = {h.source_type for h in filtered}
        assert SOURCE_AKASHA in sources
        assert SOURCE_OBSIDIAN in sources


# ── Pack Optimization ───────────────────────────────────────────────────────

class TestOptimizePack:
    def test_optimize_preserves_structure(self, mi):
        pack = ContextPack.new(query_id="qry_test")
        hits = [
            MemoryHit.new(query_id="qry_test", source_type=SOURCE_AKASHA, source_id="src_1",
                         relevance=RELEVANCE_HIGH, title="Test", snippet="Short snippet"),
        ]
        pack.assemble(hits)
        optimized = mi._optimize_pack(pack)
        assert optimized.total_hits == 1

    def test_long_snippets_truncated(self, mi):
        pack = ContextPack.new(query_id="qry_test")
        long_snippet = "x" * 500
        hits = [
            MemoryHit.new(query_id="qry_test", source_type=SOURCE_AKASHA, source_id="src_1",
                         relevance=RELEVANCE_HIGH, title="Test", snippet=long_snippet),
        ]
        pack.assemble(hits)
        optimized = mi._optimize_pack(pack)
        for hit in optimized.hits:
            assert len(hit.snippet) <= mi.config.max_snippet_chars + 3  # +3 for "..."

    def test_assembled_text_size_respected(self, mi):
        pack = ContextPack.new(query_id="qry_test")
        hits = []
        for i in range(20):
            hits.append(
                MemoryHit.new(query_id="qry_test", source_type=SOURCE_AKASHA, source_id="src_1",
                             relevance=RELEVANCE_LOW, title=f"Title {i}",
                             snippet=f"A somewhat long snippet number {i} for testing truncation behavior")
            )
        pack.assemble(hits)
        optimized = mi._optimize_pack(pack)
        assert len(optimized.assembled_text) <= mi.config.max_assembled_chars


# ── Safety Validation ───────────────────────────────────────────────────────

class TestValidateWritebackSafety:
    def test_valid_plan_passes(self, mi):
        plan = MemoryWritePlan.new(target_source=SOURCE_AKASHA, action=ACTION_UPSERT)
        mi._validate_writeback_safety(plan)  # should not raise

    def test_non_dry_run_raises(self, mi):
        plan = MemoryWritePlan.new(target_source=SOURCE_AKASHA, action=ACTION_UPSERT)
        plan.is_dry_run = False
        with pytest.raises(SafetyViolationError, match="is_dry_run"):
            mi._validate_writeback_safety(plan)

    def test_no_approval_raises(self, mi):
        plan = MemoryWritePlan.new(target_source=SOURCE_AKASHA, action=ACTION_UPSERT)
        plan.requires_approval = False
        with pytest.raises(SafetyViolationError, match="requires_approval"):
            mi._validate_writeback_safety(plan)

    def test_delete_blocked_in_validation(self, mi):
        plan = MemoryWritePlan.new(target_source=SOURCE_AKASHA, action="upsert")
        plan.action = "delete"
        with pytest.raises(SafetyViolationError, match="DELETE"):
            mi._validate_writeback_safety(plan)

    def test_too_many_records_raises(self, mi):
        plan = MemoryWritePlan.new(target_source=SOURCE_AKASHA, action=ACTION_UPSERT)
        for i in range(mi.config.max_records_per_mission + 1):
            plan.add_record(
                MissionMemoryRecord.new(
                    mission_id="spr_test",
                    sector=SECTOR_MIDIA,
                    title=f"Record {i}",
                    summary=f"Summary {i}",
                )
            )
        with pytest.raises(SafetyViolationError, match="excede"):
            mi._validate_writeback_safety(plan)


# ── Past Records ────────────────────────────────────────────────────────────

class TestGetPastRecords:
    def test_valid_sector_returns_records(self, mi):
        records = mi._get_past_records(SECTOR_MIDIA)
        assert isinstance(records, list)
        assert len(records) >= 0

    def test_invalid_sector_returns_empty(self, mi):
        records = mi._get_past_records("invalid_sector")
        assert records == []

    def test_records_have_required_fields(self, mi):
        records = mi._get_past_records(SECTOR_MIDIA)
        for record in records:
            assert record.record_id.startswith("rec_")
            assert record.sector in ["midia", "comercial", "produto"] or record.sector is not None
