"""W161 — Tests for KRATOS Bridge models."""
import pytest
from src.kratos_bridge.models import (
    KratosPayload,
    PayloadPriority,
    PayloadStatus,
    PayloadType,
)


def test_payload_defaults():
    p = KratosPayload()
    assert p.dry_run is True
    assert p.status == PayloadStatus.QUEUED
    assert p.payload_type == PayloadType.STATUS_UPDATE


def test_payload_round_trip():
    p = KratosPayload(title="Test", body={"k": "v"}, tags=["tag1"])
    p2 = KratosPayload.from_dict(p.to_dict())
    assert p2.title == "Test"
    assert p2.body == {"k": "v"}
    assert p2.tags == ["tag1"]


def test_status_update_factory():
    p = KratosPayload.status_update("Wave done", {"wave": "W161"})
    assert p.payload_type == PayloadType.STATUS_UPDATE
    assert p.target_view == "dashboard"
    assert p.title == "Wave done"


def test_alert_factory():
    p = KratosPayload.alert("Alert!", "Something happened", PayloadPriority.CRITICAL)
    assert p.payload_type == PayloadType.ALERT
    assert p.priority == PayloadPriority.CRITICAL
    assert p.body["message"] == "Something happened"


def test_metric_factory():
    p = KratosPayload.metric("test_count", 42.0, "tests")
    assert p.payload_type == PayloadType.METRIC
    assert p.body["value"] == 42.0
    assert p.body["unit"] == "tests"


def test_wave_progress_factory():
    p = KratosPayload.wave_progress("W161", 7, 10)
    assert p.payload_type == PayloadType.WAVE_PROGRESS
    assert p.body["pct"] == 70.0
    assert p.target_view == "progress"


def test_payload_id_unique():
    p1 = KratosPayload()
    p2 = KratosPayload()
    assert p1.payload_id != p2.payload_id


def test_to_dict_all_fields():
    p = KratosPayload(title="X")
    d = p.to_dict()
    for key in ["payload_id", "payload_type", "priority", "source_module", "target_view",
                "title", "body", "tags", "dry_run", "status", "created_at", "sent_at", "metadata"]:
        assert key in d
