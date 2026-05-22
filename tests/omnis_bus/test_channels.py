"""Tests for OMNIS Bus channels taxonomy (17.3)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from src.omnis_bus.channels import (
    CHANNELS,
    LEGACY_MAP,
    Channel,
    channel_for,
)


class TestChannelEnum:
    def test_six_channels_defined(self):
        assert len(Channel) == 6

    def test_omnis_runtime(self):
        assert Channel.OMNIS_RUNTIME.value == "omnis:runtime"

    def test_akasha_memory(self):
        assert Channel.AKASHA_MEMORY.value == "akasha:memory"

    def test_kratos_snapshot(self):
        assert Channel.KRATOS_SNAPSHOT.value == "kratos:snapshot"

    def test_mission_events(self):
        assert Channel.MISSION_EVENTS.value == "mission:events"

    def test_finance_cost(self):
        assert Channel.FINANCE_COST.value == "finance:cost"

    def test_crm_pipeline(self):
        assert Channel.CRM_PIPELINE.value == "crm:pipeline"

    def test_all_channels_follow_pattern(self):
        """All channels must follow <domain>:<subdomain> pattern."""
        for ch in CHANNELS:
            assert ":" in ch.value, f"Channel {ch.value} missing colon separator"
            parts = ch.value.split(":")
            assert len(parts) == 2, f"Channel {ch.value} should have exactly 2 parts"


class TestLegacyMapping:
    def test_system_heartbeat_maps_to_runtime(self):
        assert channel_for("system:heartbeat") == Channel.OMNIS_RUNTIME

    def test_omnis_events_maps_to_runtime(self):
        assert channel_for("omnis:events") == Channel.OMNIS_RUNTIME

    def test_akasha_events_maps_to_memory(self):
        assert channel_for("akasha:events") == Channel.AKASHA_MEMORY

    def test_risk_events_maps_to_runtime(self):
        assert channel_for("risk:events") == Channel.OMNIS_RUNTIME

    def test_runtime_heartbeat_maps_to_runtime(self):
        assert channel_for("runtime:heartbeat") == Channel.OMNIS_RUNTIME

    def test_mission_events_stays_mission(self):
        assert channel_for("mission:events") == Channel.MISSION_EVENTS

    def test_memory_events_maps_to_memory(self):
        assert channel_for("memory:events") == Channel.AKASHA_MEMORY

    def test_unknown_channel_defaults_to_runtime(self):
        """Safety: unknown legacy channels route to runtime."""
        assert channel_for("some:unknown") == Channel.OMNIS_RUNTIME
