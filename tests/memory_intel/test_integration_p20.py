"""Integration tests: P21 Memory Intel → P4 Memory Pack → P20 context round-trip."""
from __future__ import annotations

import pytest

from src.memory_intel import (
    MemoryIntelligence,
    MemoryIntelConfig,
    RetrievalResult,
    PatternResult,
    INTENT_CREATE_CAMPAIGN,
    INTENT_PUBLISH_CONTENT,
    INTENT_DELIVER_TO_CLIENT,
    MAX_ASSEMBLED_TEXT_CHARS,
    MAX_RECORDS_PER_MISSION,
)
from src.memory_intel.errors import (
    RetrievalError,
    WritebackError,
    SafetyViolationError,
    NoSourcesAvailableError,
)
from src.memory_pack.models import (
    ContextPack,
    MemoryQuery,
    MemoryHit,
    MissionMemoryRecord,
    MemoryWritePlan,
    SOURCE_AKASHA,
    SOURCE_SESSION,
    SECTOR_MIDIA,
    SECTOR_COMERCIAL,
    SECTOR_PRODUTO,
    RELEVANCE_HIGH,
    RELEVANCE_MEDIUM,
    STATUS_DRAFT,
    ACTION_UPSERT,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mi():
    return MemoryIntelligence(dry_run=True)


# ── P21 → P4 round-trip ─────────────────────────────────────────────────────

class TestP21ToP4RoundTrip:
    def test_retrieve_returns_context_pack_from_p4(self, mi):
        """P21.retrieve() → P4.simulate_query() → ContextPack"""
        result = mi.retrieve(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA, "spr_test_rtt")
        pack = result.pack
        assert isinstance(pack, ContextPack)
        assert pack.pack_id.startswith("pack_")
        assert pack.query_id.startswith("qry_")

    def test_context_pack_has_hits_from_simulation(self, mi):
        result = mi.retrieve(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA, "spr_test_hits")
        assert result.pack.total_hits >= 0
        if result.pack.total_hits > 0:
            for hit in result.pack.hits:
                assert isinstance(hit, MemoryHit)
                assert hit.hit_id.startswith("hit_")

    def test_retrieve_context_vs_full_retrieve(self, mi):
        """retrieve_context() returns pack-compatible data to retrieve().pack"""
        pack = mi.retrieve_context(INTENT_DELIVER_TO_CLIENT, SECTOR_COMERCIAL)
        full = mi.retrieve(INTENT_DELIVER_TO_CLIENT, SECTOR_COMERCIAL, "spr_test_cmp")
        assert isinstance(pack, ContextPack)
        assert isinstance(full.pack, ContextPack)


# ── Full context pipeline (simulated P20 flow) ──────────────────────────────

class TestContextPipeline:
    def test_pre_mission_flow(self, mi):
        """Simula o fluxo: P20 chama P21.retrieve() antes da missao"""
        # P20 SupremeContextBuilder._fetch_memory() → P21.retrieve()
        intent = INTENT_PUBLISH_CONTENT
        sector = SECTOR_MIDIA
        mission_id = "spr_pre_001"

        result = mi.retrieve(intent, sector, mission_id)

        # P20 recebe ContextPack + similares + padroes
        assert isinstance(result, RetrievalResult)
        assert len(result.pack.assembled_text) <= MAX_ASSEMBLED_TEXT_CHARS
        assert result.mode == "retrieval"

    def test_post_mission_flow(self, mi):
        """Simula o fluxo: P20 chama P21.writeback() apos missao"""
        mission_dict = {"mission_id": "spr_post_001"}
        report_dict = {
            "mission_id": "spr_post_001",
            "report_id": "rpt_flow",
            "status": "completed",
            "steps_summary": [
                {
                    "step_id": "step_a",
                    "operation": "draft_caption",
                    "status": "done",
                    "module_ref": "P8",
                    "sector": "midia",
                    "duration_ms": 200,
                },
                {
                    "step_id": "step_b",
                    "operation": "schedule_post",
                    "status": "failed",
                    "module_ref": "P8",
                    "sector": "midia",
                    "error": "no auth token",
                    "missing_dep": "meta_token",
                },
            ],
            "metrics": {
                "total_steps": 2,
                "success_rate": 50,
                "insights": ["Auth token must be pre-validated"],
            },
        }

        plan = mi.writeback(mission_dict, report_dict)

        # P20 recebe MemoryWritePlan com registros de aprendizado
        assert isinstance(plan, MemoryWritePlan)
        assert plan.is_dry_run is True
        assert plan.requires_approval is True
        assert plan.action == ACTION_UPSERT
        assert plan.target_source == SOURCE_AKASHA

    def test_full_cycle_pre_post(self, mi):
        """Ciclo completo: pre-missao retrieve → pos-missao writeback"""
        mission_id = "spr_cycle_001"

        # Pre-mission
        pre = mi.retrieve(INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA, mission_id)
        assert pre.dry_run is True
        assert isinstance(pre.patterns, dict)

        # Post-mission
        report = {
            "mission_id": mission_id,
            "steps_summary": [
                {"step_id": "s1", "operation": "plan", "status": "done",
                 "module_ref": "P20", "sector": "produto", "duration_ms": 100}
            ],
            "metrics": {"total_steps": 1, "success_rate": 100},
        }
        post = mi.writeback({"mission_id": mission_id}, report)
        assert post.record_count > 0
        assert post.record_count <= MAX_RECORDS_PER_MISSION


# ── Degradacao graciosa ─────────────────────────────────────────────────────

class TestGracefulDegradation:
    def test_empty_report_does_not_break_writeback(self, mi):
        plan = mi.writeback(
            {"mission_id": "spr_empty"},
            {"mission_id": "spr_empty", "steps_summary": [], "metrics": {}},
        )
        assert isinstance(plan, MemoryWritePlan)
        assert plan.record_count == 0

    def test_all_five_intents_work_for_retrieve(self, mi):
        intents = [
            INTENT_CREATE_CAMPAIGN,
            INTENT_PUBLISH_CONTENT,
            INTENT_DELIVER_TO_CLIENT,
            ("analyze_performance", "produto"),  # intent not in VALID_INTENTS set
            ("commercial_outreach", "comercial"),  # intent not in VALID_INTENTS set
        ]
        from src.memory_intel.models import INTENT_ANALYZE_PERFORMANCE, INTENT_COMMERCIAL_OUTREACH
        intents = [
            (INTENT_CREATE_CAMPAIGN, SECTOR_MIDIA),
            (INTENT_PUBLISH_CONTENT, SECTOR_MIDIA),
            (INTENT_DELIVER_TO_CLIENT, SECTOR_COMERCIAL),
            (INTENT_ANALYZE_PERFORMANCE, SECTOR_PRODUTO),
            (INTENT_COMMERCIAL_OUTREACH, SECTOR_COMERCIAL),
        ]
        for intent, sector in intents:
            result = mi.retrieve(intent, sector, f"spr_test_{intent}")
            assert isinstance(result, RetrievalResult)
