"""P5.4 — E2E Executive Decision Flow tests.

Validates the complete local brain pipeline:
  request → sector → skill → gap/approval → manifest → dry-run
"""
import json
import os
import socket
import pytest
from src.mission_orchestrator.planner import build_plan
from src.mission_orchestrator.executor import execute, RUN_STATUS_BLOCKED_APPROVAL
from src.mission_orchestrator.execution_manifest import build_manifest, no_secrets_in_manifest
from src.mission_orchestrator.models import RUN_STATUS_DRY_RUN, RUN_STATUS_BLOCKED
from src.approval_center import service as svc_mod
from src.approval_center import store as approval_store_mod
from src.capability_gap import store as gap_store_mod
from src.capability_gap.workflow import request_approval_for_gap, mark_gap_planned


# ─── Flow 1: marketing campaign — no approval needed ───────────────────────

def test_marketing_flow_no_approval(tmp_path):
    """carrossel campanha → marketing sector, covered, no approval needed."""
    run = build_plan("carrossel campanha instagram post")
    assert run.sector_id == "marketing"
    assert len(run.matched_capabilities) >= 1
    assert run.approval_required is False
    assert run.suggested_gap_ids == []


def test_marketing_flow_dry_run_completes(tmp_path):
    run = build_plan("carrossel campanha instagram post")
    result = execute(run, approvals_log=tmp_path / "approvals.jsonl")
    assert result.status == RUN_STATUS_DRY_RUN


def test_marketing_flow_manifest_exists(tmp_path):
    run = build_plan("carrossel campanha instagram post")
    result = execute(run, approvals_log=tmp_path / "approvals.jsonl")
    manifest = build_manifest(result)
    assert manifest["status"] == RUN_STATUS_DRY_RUN
    assert manifest["sector"] == "marketing"
    assert len(manifest["capabilities"]) >= 1


# ─── Flow 2: app factory — gap + approval required ──────────────────────────

def test_app_factory_flow_requires_approval(tmp_path):
    """cria app sistema → app sector, high-risk, requires approval."""
    run = build_plan("cria app sistema api software", allow_unknown=True)
    assert "app_factory_spec" in run.matched_capabilities
    assert run.approval_required is True


def test_app_factory_flow_blocked_without_approval(tmp_path):
    run = build_plan("cria app sistema api software", allow_unknown=True)
    result = execute(run, approvals_log=tmp_path / "approvals.jsonl")
    assert result.status == RUN_STATUS_BLOCKED_APPROVAL
    assert result.approval_id is not None


def test_app_factory_flow_approved_and_dry_runs(tmp_path):
    run = build_plan("cria app sistema api software", allow_unknown=True)
    result = execute(run, approvals_log=tmp_path / "approvals.jsonl")
    approval_id = result.approval_id
    svc_mod.approve(approval_id, note="cleared", approvals_log=tmp_path / "approvals.jsonl")
    result.approval_id = approval_id
    result2 = execute(result, approvals_log=tmp_path / "approvals.jsonl")
    assert result2.status == RUN_STATUS_DRY_RUN


def test_app_factory_rejected_blocks_permanently(tmp_path):
    run = build_plan("cria app sistema api software", allow_unknown=True)
    result = execute(run, approvals_log=tmp_path / "approvals.jsonl")
    approval_id = result.approval_id
    svc_mod.reject(approval_id, note="not now", approvals_log=tmp_path / "approvals.jsonl")
    result.approval_id = approval_id
    result2 = execute(result, approvals_log=tmp_path / "approvals.jsonl")
    assert result2.status == RUN_STATUS_BLOCKED


# ─── Flow 3: gap workflow ────────────────────────────────────────────────────

def test_finance_gap_workflow(tmp_path):
    """roi faturamento → finance sector, no capability, gap workflow."""
    run = build_plan("roi faturamento receita financeiro", allow_unknown=True)
    assert run.sector_id == "finance"
    assert run.matched_capabilities == []
    assert len(run.suggested_gap_ids) >= 1

    # Save a gap manually (orchestrator doesn't auto-save)
    from src.capability_gap.models import CapabilityGap
    from src.capability_gap.store import GapStore
    gap = CapabilityGap.new("roi faturamento", "finance", "finance_capability", "financial_report", "medium")
    GapStore(tmp_path / "gaps.jsonl").save(gap)

    # Gap approval workflow
    req_id = request_approval_for_gap(
        gap.gap_id,
        gaps_log=tmp_path / "gaps.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    assert req_id.startswith("req_")

    svc_mod.approve(req_id, approvals_log=tmp_path / "approvals.jsonl")
    planned_gap = mark_gap_planned(
        gap.gap_id, req_id,
        gaps_log=tmp_path / "gaps.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    assert planned_gap.status == "planned"


# ─── Security invariants ────────────────────────────────────────────────────

def test_no_oauth_no_meta_no_secrets():
    run = build_plan("carrossel campanha instagram")
    result = execute(run)
    manifest = build_manifest(result)
    assert no_secrets_in_manifest(manifest) is True


def test_no_network_calls_in_flow(monkeypatch):
    def _block(*args, **kwargs):
        raise AssertionError("Network blocked")
    monkeypatch.setattr(socket.socket, "connect", _block)
    run = build_plan("carrossel campanha instagram post")
    result = execute(run)
    assert result.status == RUN_STATUS_DRY_RUN


def test_no_secret_env_reads(monkeypatch):
    original = os.getenv
    def _guard(key, *args, **kwargs):
        assert not key.startswith("META_") and not key.startswith("INSTAGRAM_")
        return original(key, *args, **kwargs)
    monkeypatch.setattr(os, "getenv", _guard)
    run = build_plan("carrossel instagram post campanha")
    execute(run)
