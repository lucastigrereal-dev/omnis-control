"""W162 — Tests for KratosSerializer & payload validation."""
import json
import pytest
from src.kratos_bridge.serializer import (
    KratosEnvelope,
    KratosSerializer,
    ValidationResult,
    validate_payload,
)
from src.kratos_bridge.models import KratosPayload, PayloadType, PayloadPriority


def _p(**kwargs) -> KratosPayload:
    return KratosPayload(**kwargs)


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

def test_validation_ok_default():
    vr = ValidationResult()
    assert vr.ok is True
    assert vr.errors == []


def test_validation_fail_adds_error():
    vr = ValidationResult()
    vr.fail("bad field")
    assert not vr.ok
    assert "bad field" in vr.errors


def test_validation_to_dict():
    vr = ValidationResult(ok=False, errors=["e1"])
    d = vr.to_dict()
    assert d["ok"] is False
    assert "e1" in d["errors"]


# ---------------------------------------------------------------------------
# validate_payload
# ---------------------------------------------------------------------------

def test_valid_status_update():
    p = KratosPayload.status_update("Done", {"wave": "W162"})
    vr = validate_payload(p)
    assert vr.ok


def test_valid_alert():
    p = KratosPayload.alert("Fire!", "Something broke")
    vr = validate_payload(p)
    assert vr.ok


def test_valid_metric():
    p = KratosPayload.metric("tests", 42.0, "count")
    vr = validate_payload(p)
    assert vr.ok


def test_valid_wave_progress():
    p = KratosPayload.wave_progress("W162", 8, 10)
    vr = validate_payload(p)
    assert vr.ok


def test_title_too_long():
    p = _p(title="x" * 201)
    vr = validate_payload(p)
    assert not vr.ok
    assert any("title" in e for e in vr.errors)


def test_metric_missing_value():
    p = _p(payload_type=PayloadType.METRIC, body={})
    vr = validate_payload(p)
    assert not vr.ok
    assert any("value" in e for e in vr.errors)


def test_metric_non_numeric_value():
    p = _p(payload_type=PayloadType.METRIC, body={"value": "not_a_number"})
    vr = validate_payload(p)
    assert not vr.ok


def test_alert_missing_message():
    p = _p(payload_type=PayloadType.ALERT, body={})
    vr = validate_payload(p)
    assert not vr.ok
    assert any("message" in e for e in vr.errors)


def test_wave_progress_total_zero():
    p = _p(payload_type=PayloadType.WAVE_PROGRESS, body={"wave": "W1", "complete": 0, "total": 0})
    vr = validate_payload(p)
    assert not vr.ok


def test_wave_progress_complete_exceeds_total():
    p = _p(payload_type=PayloadType.WAVE_PROGRESS, body={"wave": "W1", "complete": 11, "total": 10})
    vr = validate_payload(p)
    assert not vr.ok


def test_body_not_dict():
    p = KratosPayload()
    p.body = "not a dict"  # type: ignore
    vr = validate_payload(p)
    assert not vr.ok


def test_multiple_errors_collected():
    p = _p(payload_type=PayloadType.METRIC, title="x" * 201, body={})
    vr = validate_payload(p)
    assert not vr.ok
    assert len(vr.errors) >= 2


# ---------------------------------------------------------------------------
# KratosEnvelope
# ---------------------------------------------------------------------------

def test_envelope_round_trip_json():
    p = KratosPayload.status_update("Test", {"k": "v"})
    env = KratosEnvelope(payload=p)
    raw = env.to_json()
    env2 = KratosEnvelope.from_json(raw)
    assert env2.payload.title == "Test"
    assert env2.schema_version == "1.0"


def test_envelope_to_dict_has_all_keys():
    env = KratosEnvelope(payload=KratosPayload())
    d = env.to_dict()
    for key in ["envelope_id", "schema_version", "payload", "created_at"]:
        assert key in d


def test_envelope_from_json_no_payload():
    raw = json.dumps({"envelope_id": "e1", "schema_version": "1.0", "created_at": "2026"})
    env = KratosEnvelope.from_json(raw)
    assert env.payload is None


# ---------------------------------------------------------------------------
# KratosSerializer
# ---------------------------------------------------------------------------

def test_serialize_valid_returns_envelope():
    s = KratosSerializer()
    p = KratosPayload.status_update("OK", {"wave": "W162"})
    env = s.serialize(p)
    assert env is not None
    assert env.payload is p


def test_serialize_invalid_non_strict_still_returns():
    s = KratosSerializer(strict=False)
    p = _p(payload_type=PayloadType.METRIC, body={})  # missing value
    env = s.serialize(p)
    assert env is not None
    assert not env.validation.ok


def test_serialize_invalid_strict_returns_none():
    s = KratosSerializer(strict=True)
    p = _p(payload_type=PayloadType.METRIC, body={})
    env = s.serialize(p)
    assert env is None


def test_strict_rejection_recorded():
    s = KratosSerializer(strict=True)
    p = _p(payload_type=PayloadType.ALERT, body={})
    s.serialize(p)
    assert len(s.rejected()) == 1


def test_serialize_many():
    s = KratosSerializer()
    payloads = [KratosPayload.metric("a", 1.0), KratosPayload.metric("b", 2.0)]
    envs = s.serialize_many(payloads)
    assert len(envs) == 2


def test_serialize_many_strict_filters():
    s = KratosSerializer(strict=True)
    good = KratosPayload.status_update("OK", {})
    bad = _p(payload_type=PayloadType.METRIC, body={})
    envs = s.serialize_many([good, bad])
    assert len(envs) == 1


def test_stats():
    s = KratosSerializer(strict=True)
    s.serialize(_p(payload_type=PayloadType.METRIC, body={}))
    st = s.stats()
    assert st["rejected"] == 1
    assert st["strict"] is True
