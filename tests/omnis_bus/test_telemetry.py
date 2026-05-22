"""Tests for OMNIS Bus telemetry events (17.6)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from src.omnis_bus.telemetry import (
    TELEMETRY_CHANNEL_MAP,
    TELEMETRY_PAYLOADS,
    TelemetryEvent,
)
from src.omnis_bus.channels import Channel


class TestTelemetryEvent:
    def test_six_events_defined(self):
        assert len(TelemetryEvent) == 6

    def test_runtime_heartbeat(self):
        assert TelemetryEvent.RUNTIME_HEARTBEAT == "runtime.heartbeat"

    def test_mission_created(self):
        assert TelemetryEvent.MISSION_CREATED == "mission.created"

    def test_mission_completed(self):
        assert TelemetryEvent.MISSION_COMPLETED == "mission.completed"

    def test_memory_ingested(self):
        assert TelemetryEvent.MEMORY_INGESTED == "memory.ingested"

    def test_cost_recorded(self):
        assert TelemetryEvent.COST_RECORDED == "cost.recorded"

    def test_risk_detected(self):
        assert TelemetryEvent.RISK_DETECTED == "risk.detected"


class TestTelemetryPayloads:
    def test_all_events_have_payload_docs(self):
        for event in TelemetryEvent:
            assert event in TELEMETRY_PAYLOADS, f"Missing payload doc for {event}"

    def test_runtime_heartbeat_payload(self):
        payload = TELEMETRY_PAYLOADS[TelemetryEvent.RUNTIME_HEARTBEAT]
        assert "service" in payload
        assert "uptime_seconds" in payload

    def test_mission_created_payload(self):
        payload = TELEMETRY_PAYLOADS[TelemetryEvent.MISSION_CREATED]
        assert "mission_id" in payload
        assert "mission_name" in payload

    def test_cost_recorded_payload(self):
        payload = TELEMETRY_PAYLOADS[TelemetryEvent.COST_RECORDED]
        assert "provider" in payload
        assert "cost_usd" in payload

    def test_risk_detected_payload(self):
        payload = TELEMETRY_PAYLOADS[TelemetryEvent.RISK_DETECTED]
        assert "risk_level" in payload
        assert "action" in payload


class TestTelemetryChannelMap:
    def test_runtime_heartbeat_to_omnis_runtime(self):
        assert TELEMETRY_CHANNEL_MAP[TelemetryEvent.RUNTIME_HEARTBEAT] == Channel.OMNIS_RUNTIME

    def test_mission_events_to_mission_channel(self):
        assert TELEMETRY_CHANNEL_MAP[TelemetryEvent.MISSION_CREATED] == Channel.MISSION_EVENTS
        assert TELEMETRY_CHANNEL_MAP[TelemetryEvent.MISSION_COMPLETED] == Channel.MISSION_EVENTS

    def test_memory_ingested_to_akasha_memory(self):
        assert TELEMETRY_CHANNEL_MAP[TelemetryEvent.MEMORY_INGESTED] == Channel.AKASHA_MEMORY

    def test_cost_to_finance(self):
        assert TELEMETRY_CHANNEL_MAP[TelemetryEvent.COST_RECORDED] == Channel.FINANCE_COST

    def test_risk_to_omnis_runtime(self):
        assert TELEMETRY_CHANNEL_MAP[TelemetryEvent.RISK_DETECTED] == Channel.OMNIS_RUNTIME
