"""W162 — KRATOS payload serializer: JSON schema validation + envelope wrapping."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

from .models import KratosPayload, PayloadType, _new_id, _now_iso

# ---------------------------------------------------------------------------
# Required fields per type
# ---------------------------------------------------------------------------

_REQUIRED_BODY_FIELDS: dict[str, list[str]] = {
    PayloadType.METRIC.value: ["value"],
    PayloadType.WAVE_PROGRESS.value: ["wave", "complete", "total"],
    PayloadType.ALERT.value: ["message"],
    PayloadType.COMMAND_ECHO.value: ["command"],
}

_MAX_TITLE_LEN = 200
_MAX_BODY_DEPTH = 4


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.ok = False
        self.errors.append(msg)

    def to_dict(self) -> dict:
        return {"ok": self.ok, "errors": self.errors}


def _depth(obj: object, current: int = 0) -> int:
    if current > _MAX_BODY_DEPTH:
        return current
    if isinstance(obj, dict):
        if not obj:
            return current
        return max(_depth(v, current + 1) for v in obj.values())
    if isinstance(obj, list):
        if not obj:
            return current
        return max(_depth(v, current + 1) for v in obj)
    return current


def validate_payload(payload: KratosPayload) -> ValidationResult:
    result = ValidationResult()

    if not payload.payload_id:
        result.fail("payload_id is required")

    if len(payload.title) > _MAX_TITLE_LEN:
        result.fail(f"title exceeds {_MAX_TITLE_LEN} chars")

    if not isinstance(payload.body, dict):
        result.fail("body must be a dict")
    else:
        required = _REQUIRED_BODY_FIELDS.get(payload.payload_type.value, [])
        for field_name in required:
            if field_name not in payload.body:
                result.fail(f"body.{field_name} required for {payload.payload_type.value}")

        if _depth(payload.body) > _MAX_BODY_DEPTH:
            result.fail(f"body nesting exceeds max depth {_MAX_BODY_DEPTH}")

    if payload.payload_type == PayloadType.METRIC:
        val = payload.body.get("value")
        if val is not None and not isinstance(val, (int, float)):
            result.fail("body.value must be numeric for METRIC")

    if payload.payload_type == PayloadType.WAVE_PROGRESS:
        complete = payload.body.get("complete", 0)
        total = payload.body.get("total", 0)
        if total <= 0:
            result.fail("body.total must be > 0 for WAVE_PROGRESS")
        if complete < 0 or complete > total:
            result.fail("body.complete must be in [0, total]")

    return result


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------

@dataclass
class KratosEnvelope:
    envelope_id: str = field(default_factory=lambda: _new_id("kenv"))
    schema_version: str = "1.0"
    payload: Optional[KratosPayload] = None
    validation: Optional[ValidationResult] = None
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "envelope_id": self.envelope_id,
            "schema_version": self.schema_version,
            "payload": self.payload.to_dict() if self.payload else None,
            "validation": self.validation.to_dict() if self.validation else None,
            "created_at": self.created_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "KratosEnvelope":
        data = json.loads(raw)
        payload = KratosPayload.from_dict(data["payload"]) if data.get("payload") else None
        v_data = data.get("validation")
        validation = None
        if v_data:
            validation = ValidationResult(ok=v_data.get("ok", True), errors=v_data.get("errors", []))
        return cls(
            envelope_id=data.get("envelope_id", _new_id("kenv")),
            schema_version=data.get("schema_version", "1.0"),
            payload=payload,
            validation=validation,
            created_at=data.get("created_at", _now_iso()),
        )


# ---------------------------------------------------------------------------
# Serializer
# ---------------------------------------------------------------------------

class KratosSerializer:
    """Validates and serializes KratosPayloads into envelopes for cockpit delivery."""

    def __init__(self, strict: bool = False) -> None:
        self.strict = strict  # if True, reject invalid payloads
        self._rejected: list[tuple[KratosPayload, ValidationResult]] = []

    def serialize(self, payload: KratosPayload) -> Optional[KratosEnvelope]:
        vr = validate_payload(payload)
        if not vr.ok and self.strict:
            self._rejected.append((payload, vr))
            return None
        envelope = KratosEnvelope(payload=payload, validation=vr)
        return envelope

    def serialize_many(self, payloads: list[KratosPayload]) -> list[KratosEnvelope]:
        result = []
        for p in payloads:
            env = self.serialize(p)
            if env is not None:
                result.append(env)
        return result

    def rejected(self) -> list[tuple[KratosPayload, ValidationResult]]:
        return list(self._rejected)

    def stats(self) -> dict:
        return {"rejected": len(self._rejected), "strict": self.strict}
