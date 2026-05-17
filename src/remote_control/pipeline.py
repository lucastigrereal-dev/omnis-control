"""W160 — G17 Remote Control E2E Pipeline: webhook → rate_limit → dispatch → audit."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .audit_log import AuditEntry, CommandAuditLog
from .command_dispatcher import CommandDispatcher, DispatchRequest
from .models import CommandStatus, _new_id, _now_iso
from .rate_limiter import RateLimiter, RateLimitConfig
from .webhook_gateway import WebhookGateway, WebhookPayload


# ---------------------------------------------------------------------------
# Pipeline config
# ---------------------------------------------------------------------------

@dataclass
class PipelineConfig:
    dry_run: bool = True
    rate_limit: Optional[RateLimitConfig] = None
    webhook_secret: str = ""
    allowed_sources: Optional[list[str]] = None

    def to_dict(self) -> dict:
        return {
            "dry_run": self.dry_run,
            "rate_limit": self.rate_limit.to_dict() if self.rate_limit else None,
            "webhook_secret": "***" if self.webhook_secret else "",
            "allowed_sources": self.allowed_sources,
        }


# ---------------------------------------------------------------------------
# Pipeline result
# ---------------------------------------------------------------------------

@dataclass
class PipelineResult:
    result_id: str = field(default_factory=lambda: _new_id("pipe"))
    ok: bool = False
    stage_reached: str = "none"
    command_id: str = ""
    command: str = ""
    dispatch_status: str = ""
    audit_entry_id: str = ""
    rejection_reason: str = ""
    error: str = ""
    dry_run: bool = True
    completed_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "ok": self.ok,
            "stage_reached": self.stage_reached,
            "command_id": self.command_id,
            "command": self.command,
            "dispatch_status": self.dispatch_status,
            "audit_entry_id": self.audit_entry_id,
            "rejection_reason": self.rejection_reason,
            "error": self.error,
            "dry_run": self.dry_run,
            "completed_at": self.completed_at,
        }


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class RemoteControlPipeline:
    """Full G17 pipeline: WebhookGateway → RateLimiter → CommandDispatcher → AuditLog."""

    def __init__(self, config: Optional[PipelineConfig] = None) -> None:
        self.config = config or PipelineConfig()
        self.gateway = WebhookGateway(
            webhook_secret=self.config.webhook_secret,
            dry_run=self.config.dry_run,
            allowed_sources=self.config.allowed_sources,
        )
        self.rate_limiter = RateLimiter(
            self.config.rate_limit or RateLimitConfig()
        )
        self.dispatcher = CommandDispatcher()
        self.audit = CommandAuditLog()
        self._results: list[PipelineResult] = []

    # ------------------------------------------------------------------
    def process(self, payload: WebhookPayload, raw_body: bytes = b"") -> PipelineResult:
        pr = PipelineResult(dry_run=self.config.dry_run)

        # Stage 1: Ingest
        pr.stage_reached = "ingest"
        ingest = self.gateway.ingest(payload, raw_body)
        if not ingest.ok:
            pr.rejection_reason = ingest.rejected_reason or ingest.error
            self._audit_rejection(pr, ingest.rejected_reason, source=payload.source)
            self._results.append(pr)
            return pr

        cmd = ingest.command
        pr.command_id = cmd.command_id
        pr.command = cmd.command

        # Stage 2: Rate limit
        pr.stage_reached = "rate_limit"
        throttle = self.rate_limiter.check(cmd.source_user_id or cmd.source.value)
        if not throttle.allowed:
            pr.rejection_reason = throttle.reason
            self._audit_rejection(pr, throttle.reason, source=cmd.source.value, user_id=cmd.source_user_id, command=cmd.command)
            self._results.append(pr)
            return pr

        # Stage 3: High-risk gate (requires_approval blocks automatic dispatch)
        pr.stage_reached = "risk_gate"
        if cmd.requires_approval:
            pr.rejection_reason = "requires_human_approval"
            pr.dispatch_status = CommandStatus.BLOCKED.value
            self._record_audit(pr, cmd.source.value, cmd.source_user_id, cmd.command, cmd.risk.value, allowed=False)
            self._results.append(pr)
            return pr

        # Stage 4: Dispatch
        pr.stage_reached = "dispatch"
        req = DispatchRequest.new(
            command=cmd.command,
            source=cmd.source.value,
            payload=cmd.args,
            dry_run=self.config.dry_run,
        )
        result = self.dispatcher.dispatch(req)
        pr.dispatch_status = result.status
        pr.ok = result.status in ("dispatched", "dry_run")

        # Stage 5: Audit
        pr.stage_reached = "audit"
        entry = self._record_audit(
            pr,
            cmd.source.value,
            cmd.source_user_id,
            cmd.command,
            cmd.risk.value,
            allowed=pr.ok,
            output=str(result.output),
            error=result.error,
        )
        pr.audit_entry_id = entry.entry_id
        self._results.append(pr)
        return pr

    # ------------------------------------------------------------------
    def _audit_rejection(self, pr: PipelineResult, reason: str, source: str = "", user_id: str = "", command: str = "") -> None:
        entry = self.audit.record(AuditEntry(
            command_id=pr.command_id or _new_id("rej"),
            command=command or pr.command,
            source=source,
            user_id=user_id,
            status=CommandStatus.BLOCKED.value,
            allowed=False,
            rejection_reason=reason,
            dry_run=self.config.dry_run,
        ))
        pr.audit_entry_id = entry.entry_id

    def _record_audit(self, pr: PipelineResult, source: str, user_id: str, command: str, risk: str,
                      allowed: bool, output: str = "", error: str = "") -> AuditEntry:
        status = CommandStatus.EXECUTED.value if allowed else CommandStatus.BLOCKED.value
        return self.audit.record(AuditEntry(
            command_id=pr.command_id,
            command=command,
            source=source,
            user_id=user_id,
            status=status,
            risk=risk,
            allowed=allowed,
            output=output,
            error=error,
            dry_run=self.config.dry_run,
        ))

    # ------------------------------------------------------------------
    def results(self) -> list[PipelineResult]:
        return list(self._results)

    def stats(self) -> dict:
        total = len(self._results)
        ok = sum(1 for r in self._results if r.ok)
        return {
            "total": total,
            "ok": ok,
            "rejected": total - ok,
            "audit": self.audit.stats(),
            "rate_limiter_users": len(self.rate_limiter._buckets),
        }
