"""Tests for OMNIS Bus canonical envelope (17.2)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

from src.omnis_bus.envelope import (
    CanonicalEnvelope,
    EventStatus,
    Severity,
    SourceBadge,
    SourceInfo,
    make_envelope,
    validate_envelope,
    _infer_badge,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _valid_event_dict(**overrides) -> dict:
    event = {
        "event_id": "evt-00000001",
        "type": "system.heartbeat",
        "timestamp": "2026-05-19T14:30:00.123456+00:00",
        "source": {
            "service": "kratos-mission-control",
            "version": "0.12.0",
            "instance": "kratos-backend",
        },
        "correlation_id": "corr-00000001",
        "mission_id": "MIS-20260519-001",
        "severity": "info",
        "status": "ok",
        "payload": {"status": "healthy"},
        "source_badge": "kratos",
    }
    event.update(overrides)
    return event


# ---------------------------------------------------------------------------
# Envelope model tests
# ---------------------------------------------------------------------------
class TestCanonicalEnvelope:
    def test_create_minimal(self):
        env = CanonicalEnvelope(
            type="system.heartbeat",
            source=SourceInfo(service="kratos-mission-control", version="0.12.0", badge=SourceBadge.KRATOS),
        )
        assert env.type == "system.heartbeat"
        assert env.event_id.startswith("evt-")
        assert env.severity == Severity.INFO
        assert env.status == EventStatus.OK
        assert env.source_badge == SourceBadge.KRATOS

    def test_create_full(self):
        env = CanonicalEnvelope(**{
            "event_id": "evt-custom",
            "type": "mission.created",
            "timestamp": "2026-05-19T14:30:00+00:00",
            "source": {"service": "omnis-control", "version": "1.0.0", "badge": "omnis"},
            "correlation_id": "corr-abc",
            "mission_id": "MIS-001",
            "severity": "warn",
            "status": "pending",
            "payload": {"key": "value"},
            "source_badge": "omnis",
        })
        assert env.event_id == "evt-custom"
        assert env.type == "mission.created"
        assert env.severity == Severity.WARN
        assert env.status == EventStatus.PENDING

    def test_auto_generates_event_id(self):
        env = CanonicalEnvelope(
            type="test.event",
            source=SourceInfo(service="test", version="0.1"),
        )
        assert env.event_id
        assert env.event_id.startswith("evt-")

    def test_auto_generates_correlation_id(self):
        env = CanonicalEnvelope(
            type="test.event",
            source=SourceInfo(service="test", version="0.1"),
        )
        assert env.correlation_id
        assert env.correlation_id.startswith("corr-")

    def test_default_severity_info(self):
        env = CanonicalEnvelope(
            type="test.event",
            source=SourceInfo(service="test", version="0.1"),
        )
        assert env.severity == Severity.INFO

    def test_default_status_ok(self):
        env = CanonicalEnvelope(
            type="test.event",
            source=SourceInfo(service="test", version="0.1"),
        )
        assert env.status == EventStatus.OK

    def test_to_redis_payload(self):
        env = CanonicalEnvelope(
            type="test.event",
            source=SourceInfo(service="test", version="0.1"),
        )
        payload = env.to_redis_payload()
        assert isinstance(payload, dict)
        assert payload["type"] == "test.event"
        assert payload["severity"] == "info"
        assert payload["status"] == "ok"

    def test_source_badge_syncs_from_source(self):
        env = CanonicalEnvelope(
            type="test.event",
            source=SourceInfo(service="kratos-mission-control", version="0.12.0", badge=SourceBadge.KRATOS),
        )
        assert env.source_badge == SourceBadge.KRATOS

    def test_from_redis_payload_legacy_event_type(self):
        """Legacy V2 envelopes with event_type should map to type."""
        legacy = {
            "event_id": "evt-legacy",
            "event_type": "system.heartbeat",
            "timestamp": "2026-05-19T14:30:00+00:00",
            "source": {"service": "kratos-mission-control", "version": "0.12.0"},
            "severity": "info",
            "status": "ok",
            "payload": {},
        }
        env = CanonicalEnvelope.from_redis_payload(legacy)
        assert env.type == "system.heartbeat"

    def test_from_redis_payload_infers_badge(self):
        """Should auto-detect kratos badge from service name."""
        legacy = {
            "event_id": "evt-legacy",
            "event_type": "system.heartbeat",
            "timestamp": "2026-05-19T14:30:00+00:00",
            "source": {"service": "kratos-mission-control", "version": "0.12.0"},
            "severity": "info",
            "status": "ok",
            "payload": {},
        }
        env = CanonicalEnvelope.from_redis_payload(legacy)
        assert env.source_badge == SourceBadge.KRATOS

    def test_roundtrip_redis(self):
        original = _valid_event_dict()
        env = CanonicalEnvelope.from_redis_payload(original)
        payload = env.to_redis_payload()
        env2 = CanonicalEnvelope.from_redis_payload(payload)
        assert env2.type == original["type"]
        assert env2.event_id == original["event_id"]


# ---------------------------------------------------------------------------
# validate_envelope tests (backward compat with V2)
# ---------------------------------------------------------------------------
class TestValidateEnvelope:
    def test_valid_event_passes(self):
        errors = validate_envelope(_valid_event_dict())
        assert errors == []

    def test_missing_required_fields(self):
        errors = validate_envelope({"event_id": "evt-1"})
        assert len(errors) > 0
        assert any("Missing fields" in e for e in errors)

    def test_invalid_severity(self):
        event = _valid_event_dict(severity="catastrophic")
        errors = validate_envelope(event)
        assert any("Invalid severity" in e for e in errors)

    def test_invalid_status(self):
        event = _valid_event_dict(status="unknown")
        errors = validate_envelope(event)
        assert any("Invalid status" in e for e in errors)

    def test_source_not_dict(self):
        event = _valid_event_dict(source="just-a-string")
        errors = validate_envelope(event)
        assert any("source must be a dict" in e for e in errors)

    def test_source_missing_service(self):
        event = _valid_event_dict(source={"version": "1.0"})
        errors = validate_envelope(event)
        assert any("Missing source.service" in e for e in errors)

    def test_source_missing_version(self):
        event = _valid_event_dict(source={"service": "test"})
        errors = validate_envelope(event)
        assert any("Missing source.version" in e for e in errors)

    def test_non_dict_returns_error(self):
        errors = validate_envelope("not a dict")
        assert errors == ["Event is not a dict"]

    def test_accepts_legacy_event_type(self):
        """Should accept event_type as valid type field."""
        event = _valid_event_dict()
        del event["type"]
        event["event_type"] = "system.heartbeat"
        errors = validate_envelope(event)
        assert errors == []

    def test_all_valid_severities(self):
        for sev in ["debug", "info", "warn", "error", "critical"]:
            event = _valid_event_dict(severity=sev)
            errors = validate_envelope(event)
            assert errors == [], f"Severity {sev} should be valid"

    def test_all_valid_statuses(self):
        for st in ["ok", "degraded", "failed", "pending"]:
            event = _valid_event_dict(status=st)
            errors = validate_envelope(event)
            assert errors == [], f"Status {st} should be valid"


# ---------------------------------------------------------------------------
# make_envelope factory tests
# ---------------------------------------------------------------------------
class TestMakeEnvelope:
    def test_creates_valid_envelope(self):
        env = make_envelope(
            event_type="test.event",
            payload={"key": "value"},
            source_service="kratos-mission-control",
            source_version="0.12.0",
        )
        assert env.type == "test.event"
        assert env.source.service == "kratos-mission-control"
        assert env.source_badge == SourceBadge.KRATOS

    def test_infers_badge_from_service(self):
        env = make_envelope(
            event_type="test.event",
            payload={},
            source_service="akasha",
            source_version="1.0",
        )
        assert env.source_badge == SourceBadge.AKASHA

    def test_explicit_badge_overrides_inference(self):
        env = make_envelope(
            event_type="test.event",
            payload={},
            source_service="custom-service",
            source_version="0.1",
            source_badge=SourceBadge.OMNIS,
        )
        assert env.source_badge == SourceBadge.OMNIS

    def test_generates_ids(self):
        env = make_envelope(
            event_type="test.event",
            payload={},
            source_service="test",
            source_version="0.1",
        )
        assert env.event_id.startswith("evt-")
        assert env.correlation_id.startswith("corr-")


# ---------------------------------------------------------------------------
# _infer_badge tests
# ---------------------------------------------------------------------------
class TestInferBadge:
    def test_kratos(self):
        assert _infer_badge("kratos-mission-control") == "kratos"

    def test_omnis(self):
        assert _infer_badge("omnis-control") == "omnis"

    def test_akasha(self):
        assert _infer_badge("akasha") == "akasha"

    def test_publisher(self):
        assert _infer_badge("publisher-os") == "publisher-os"

    def test_crm(self):
        assert _infer_badge("crm-tigre") == "crm"

    def test_finance(self):
        assert _infer_badge("gringotts") == "finance"

    def test_unknown(self):
        assert _infer_badge("some-random-service") == "unknown"


# ---------------------------------------------------------------------------
# Unknown event handling (17.7 — unknown source)
# ---------------------------------------------------------------------------
class TestUnknownEvent:
    def test_unknown_source_accepted(self):
        """Unknown source events should still be processable."""
        event = _valid_event_dict(
            source={"service": "mystery-service", "version": "0.1"},
            source_badge="unknown",
        )
        env = CanonicalEnvelope.from_redis_payload(event)
        assert env.source_badge == SourceBadge.UNKNOWN
        assert env.type == "system.heartbeat"

    def test_unknown_event_type_still_validates(self):
        """Unknown event types should pass validation if structurally valid."""
        event = _valid_event_dict(type="completely.unknown.event")
        errors = validate_envelope(event)
        assert errors == []

    def test_malformed_payload_is_error(self):
        """Missing payload field should fail."""
        event = _valid_event_dict()
        del event["payload"]
        errors = validate_envelope(event)
        assert any("Missing fields" in e for e in errors)
