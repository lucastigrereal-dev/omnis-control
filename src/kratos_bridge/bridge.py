"""W164 — KRATOS Bridge E2E: serialize → route → dispatch cockpit payloads."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .dispatcher import KratosDispatcher, DispatchResult
from .models import KratosPayload, PayloadPriority, _new_id, _now_iso
from .serializer import KratosEnvelope, KratosSerializer, ValidationResult
from .view_router import KratosViewRouter, RoutingResult


# ---------------------------------------------------------------------------
# Bridge config
# ---------------------------------------------------------------------------

@dataclass
class BridgeConfig:
    dry_run: bool = True
    strict_validation: bool = False
    fallback_view: str = "/dashboard"

    def to_dict(self) -> dict:
        return {
            "dry_run": self.dry_run,
            "strict_validation": self.strict_validation,
            "fallback_view": self.fallback_view,
        }


# ---------------------------------------------------------------------------
# Bridge result
# ---------------------------------------------------------------------------

@dataclass
class BridgeResult:
    result_id: str = field(default_factory=lambda: _new_id("br"))
    payload_id: str = ""
    ok: bool = False
    stage: str = "none"
    validation: Optional[ValidationResult] = None
    routing: Optional[RoutingResult] = None
    dispatch: Optional[DispatchResult] = None
    rejection_reason: str = ""
    completed_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "payload_id": self.payload_id,
            "ok": self.ok,
            "stage": self.stage,
            "validation": self.validation.to_dict() if self.validation else None,
            "routing": self.routing.to_dict() if self.routing else None,
            "dispatch": self.dispatch.to_dict() if self.dispatch else None,
            "rejection_reason": self.rejection_reason,
            "completed_at": self.completed_at,
        }


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------

class KratosBridge:
    """Full OMNIS → KRATOS pipeline: serialize → route → dispatch."""

    def __init__(self, config: Optional[BridgeConfig] = None) -> None:
        self.config = config or BridgeConfig()
        self.serializer = KratosSerializer(strict=self.config.strict_validation)
        self.router = KratosViewRouter(fallback_path=self.config.fallback_view)
        self.dispatcher = KratosDispatcher(dry_run=self.config.dry_run)
        self._results: list[BridgeResult] = []

    # ------------------------------------------------------------------
    def send(self, payload: KratosPayload) -> BridgeResult:
        br = BridgeResult(payload_id=payload.payload_id)

        # Stage 1: Serialize & validate
        br.stage = "serialize"
        envelope = self.serializer.serialize(payload)
        if envelope is None:
            br.rejection_reason = "validation_failed"
            br.validation = self.serializer.rejected()[-1][1] if self.serializer.rejected() else None
            self._results.append(br)
            return br
        br.validation = envelope.validation

        # Stage 2: Route
        br.stage = "route"
        routing = self.router.route(payload)
        br.routing = routing

        # Stage 3: Dispatch
        br.stage = "dispatch"
        dispatch = self.dispatcher.dispatch_one(payload)
        br.dispatch = dispatch
        br.ok = dispatch.ok
        br.stage = "complete"
        self._results.append(br)
        return br

    def send_many(self, payloads: list[KratosPayload]) -> list[BridgeResult]:
        return [self.send(p) for p in payloads]

    def send_alert(self, title: str, message: str, priority: PayloadPriority = PayloadPriority.HIGH) -> BridgeResult:
        return self.send(KratosPayload.alert(title, message, priority))

    def send_metric(self, name: str, value: float, unit: str = "") -> BridgeResult:
        return self.send(KratosPayload.metric(name, value, unit))

    def send_wave_progress(self, wave: str, complete: int, total: int) -> BridgeResult:
        return self.send(KratosPayload.wave_progress(wave, complete, total))

    def send_status(self, title: str, body: dict) -> BridgeResult:
        return self.send(KratosPayload.status_update(title, body))

    # ------------------------------------------------------------------
    def results(self) -> list[BridgeResult]:
        return list(self._results)

    def stats(self) -> dict:
        total = len(self._results)
        ok = sum(1 for r in self._results if r.ok)
        return {
            "total": total,
            "ok": ok,
            "rejected": total - ok,
            "dispatcher": self.dispatcher.stats(),
            "serializer": self.serializer.stats(),
        }
