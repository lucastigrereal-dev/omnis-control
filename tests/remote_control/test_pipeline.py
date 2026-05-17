"""W160 — Tests for RemoteControlPipeline (G17 E2E)."""
import pytest
from src.remote_control.pipeline import RemoteControlPipeline, PipelineConfig
from src.remote_control.rate_limiter import RateLimitConfig
from src.remote_control.webhook_gateway import WebhookPayload


def _tg(text: str, user_id: int = 111, chat_id: int = 222) -> WebhookPayload:
    return WebhookPayload(
        source="TELEGRAM",
        body={"message": {"text": text, "from": {"id": user_id}, "chat": {"id": chat_id}}},
    )


def _generic(command: str, user_id: str = "u1") -> WebhookPayload:
    return WebhookPayload(source="GENERIC", body={"command": command, "user_id": user_id})


def _make_pipeline(**kwargs) -> RemoteControlPipeline:
    cfg = PipelineConfig(dry_run=True, **kwargs)
    return RemoteControlPipeline(cfg)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_low_risk_command_succeeds():
    p = _make_pipeline()
    result = p.process(_tg("/status"))
    assert result.ok
    assert result.stage_reached == "audit"
    assert result.command == "status"


def test_result_has_audit_entry():
    p = _make_pipeline()
    result = p.process(_tg("/ping"))
    assert result.audit_entry_id != ""


def test_dry_run_flagged():
    p = _make_pipeline()
    result = p.process(_tg("/briefing"))
    assert result.dry_run is True


def test_generic_source_succeeds():
    p = _make_pipeline()
    result = p.process(_generic("health_check"))
    assert result.ok


def test_pipeline_result_to_dict():
    p = _make_pipeline()
    result = p.process(_tg("/status"))
    d = result.to_dict()
    assert d["ok"] is True
    assert "result_id" in d
    assert d["command"] == "status"


# ---------------------------------------------------------------------------
# Source rejection
# ---------------------------------------------------------------------------

def test_unknown_source_rejected_at_ingest():
    p = _make_pipeline()
    payload = WebhookPayload(source="SLACK", body={"command": "status"})
    result = p.process(payload)
    assert not result.ok
    assert result.stage_reached == "ingest"
    assert "source_not_allowed" in result.rejection_reason


def test_empty_command_rejected_at_ingest():
    p = _make_pipeline()
    payload = WebhookPayload(source="TELEGRAM", body={"message": {"text": ""}})
    result = p.process(payload)
    assert not result.ok
    assert result.stage_reached == "ingest"


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def test_rate_limit_triggers():
    cfg = PipelineConfig(
        dry_run=True,
        rate_limit=RateLimitConfig(max_requests=2, window_seconds=60.0, burst_max=10),
    )
    p = RemoteControlPipeline(cfg)
    p.process(_generic("status", user_id="u1"))
    p.process(_generic("status", user_id="u1"))
    result = p.process(_generic("status", user_id="u1"))
    assert not result.ok
    assert result.stage_reached == "rate_limit"
    assert result.rejection_reason == "rate_limit_exceeded"


def test_rate_limit_per_user_isolation():
    cfg = PipelineConfig(
        dry_run=True,
        rate_limit=RateLimitConfig(max_requests=1, window_seconds=60.0, burst_max=10),
    )
    p = RemoteControlPipeline(cfg)
    p.process(_generic("status", user_id="alice"))
    p.process(_generic("status", user_id="alice"))  # alice blocked
    result = p.process(_generic("status", user_id="bob"))
    assert result.ok


# ---------------------------------------------------------------------------
# High-risk gate
# ---------------------------------------------------------------------------

def test_high_risk_blocked_at_risk_gate():
    p = _make_pipeline()
    result = p.process(_tg("/rm_rf /data"))
    assert not result.ok
    assert result.stage_reached == "risk_gate"
    assert result.rejection_reason == "requires_human_approval"
    assert result.dispatch_status == "BLOCKED"


def test_medium_risk_not_blocked():
    p = _make_pipeline()
    result = p.process(_tg("/publish daily"))
    assert result.ok  # medium risk goes through


# ---------------------------------------------------------------------------
# Audit integration
# ---------------------------------------------------------------------------

def test_audit_records_success():
    p = _make_pipeline()
    p.process(_tg("/status"))
    audit_stats = p.audit.stats()
    assert audit_stats["total"] >= 1
    assert audit_stats["allowed"] >= 1


def test_audit_records_rejection():
    p = _make_pipeline()
    p.process(WebhookPayload(source="SLACK", body={"command": "status"}))
    stats = p.audit.stats()
    assert stats["rejected"] >= 1


def test_audit_records_rate_limit_rejection():
    cfg = PipelineConfig(
        dry_run=True,
        rate_limit=RateLimitConfig(max_requests=1, window_seconds=60.0, burst_max=10),
    )
    p = RemoteControlPipeline(cfg)
    p.process(_generic("ping", user_id="u"))
    p.process(_generic("ping", user_id="u"))  # blocked
    stats = p.audit.stats()
    assert stats["rejected"] == 1


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def test_pipeline_stats_empty():
    p = _make_pipeline()
    s = p.stats()
    assert s["total"] == 0
    assert s["ok"] == 0


def test_pipeline_stats_after_processing():
    p = _make_pipeline()
    p.process(_tg("/status"))
    p.process(_tg("/ping"))
    p.process(WebhookPayload(source="SLACK", body={"command": "x"}))
    s = p.stats()
    assert s["total"] == 3
    assert s["ok"] == 2
    assert s["rejected"] == 1


def test_results_list():
    p = _make_pipeline()
    p.process(_tg("/status"))
    p.process(_tg("/ping"))
    assert len(p.results()) == 2


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def test_config_to_dict_masks_secret():
    cfg = PipelineConfig(dry_run=True, webhook_secret="mysecret")
    d = cfg.to_dict()
    assert d["webhook_secret"] == "***"


def test_config_no_secret():
    cfg = PipelineConfig(dry_run=True)
    assert cfg.to_dict()["webhook_secret"] == ""
