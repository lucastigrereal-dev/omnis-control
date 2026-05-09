"""P5.2 — Gap-to-Approval Workflow tests."""
import json
import pytest
from typer.testing import CliRunner
from src.capability_gap.models import CapabilityGap
from src.capability_gap.workflow import (
    request_approval_for_gap, mark_gap_planned, mark_gap_dismissed,
    GAP_STATUS_PLANNED, GAP_STATUS_DISMISSED,
)
from src.capability_gap import store as gap_store_mod
from src.capability_gap.store import GapStore
from src.approval_center import store as approval_store_mod
from src.approval_center.service import approve, reject
from src.capability_gap.errors import CapabilityGapError
from src.cli import app

runner = CliRunner()


def make_saved_gap(tmp_path, suffix="001") -> CapabilityGap:
    store = GapStore(tmp_path / "gaps.jsonl")
    gap = CapabilityGap.new(
        request=f"request {suffix}",
        sector="apps",
        missing_capability="crm_app_capability",
        desired_output="crm_app",
        risk_level="high",
    )
    store.save(gap)
    return gap


def test_gap_creates_approval_request(tmp_path):
    gap = make_saved_gap(tmp_path)
    req_id = request_approval_for_gap(
        gap.gap_id,
        gaps_log=tmp_path / "gaps.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    assert req_id.startswith("req_")


def test_approved_approval_allows_planned(tmp_path):
    gap = make_saved_gap(tmp_path)
    req_id = request_approval_for_gap(
        gap.gap_id,
        gaps_log=tmp_path / "gaps.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    approve(req_id, approvals_log=tmp_path / "approvals.jsonl")
    updated = mark_gap_planned(
        gap.gap_id, req_id,
        gaps_log=tmp_path / "gaps.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    assert updated.status == GAP_STATUS_PLANNED


def test_without_approval_blocks_planned(tmp_path):
    gap = make_saved_gap(tmp_path)
    # No approval created — mark_gap_planned should raise
    with pytest.raises(CapabilityGapError):
        mark_gap_planned(
            gap.gap_id, "req_ghost",
            gaps_log=tmp_path / "gaps.jsonl",
            approvals_log=tmp_path / "approvals.jsonl",
        )


def test_pending_approval_blocks_planned(tmp_path):
    gap = make_saved_gap(tmp_path)
    req_id = request_approval_for_gap(
        gap.gap_id,
        gaps_log=tmp_path / "gaps.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    # approval still pending — should raise
    with pytest.raises(CapabilityGapError, match="not 'approved'"):
        mark_gap_planned(
            gap.gap_id, req_id,
            gaps_log=tmp_path / "gaps.jsonl",
            approvals_log=tmp_path / "approvals.jsonl",
        )


def test_rejected_approval_allows_dismissed(tmp_path):
    gap = make_saved_gap(tmp_path)
    req_id = request_approval_for_gap(
        gap.gap_id,
        gaps_log=tmp_path / "gaps.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    reject(req_id, approvals_log=tmp_path / "approvals.jsonl")
    updated = mark_gap_dismissed(
        gap.gap_id, req_id,
        gaps_log=tmp_path / "gaps.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    assert updated.status == GAP_STATUS_DISMISSED


def test_gap_not_found_raises(tmp_path):
    with pytest.raises(CapabilityGapError, match="not found"):
        request_approval_for_gap(
            "gap_ghost",
            gaps_log=tmp_path / "gaps.jsonl",
            approvals_log=tmp_path / "approvals.jsonl",
        )


def test_cli_request_approval(tmp_path, monkeypatch):
    monkeypatch.setattr(gap_store_mod, "DEFAULT_GAPS_LOG", tmp_path / "gaps.jsonl")
    monkeypatch.setattr(approval_store_mod, "DEFAULT_APPROVALS_LOG", tmp_path / "approvals.jsonl")
    # First save a gap via CLI detect
    detect_result = runner.invoke(app, ["capability-gap", "detect", "roi faturamento receita financeiro", "--save"])
    assert detect_result.exit_code == 0
    # Get the gap_id
    gaps = GapStore(tmp_path / "gaps.jsonl").list_all()
    assert len(gaps) >= 1
    gap_id = gaps[0].gap_id
    # Request approval
    result = runner.invoke(app, ["capability-gap", "request-approval", gap_id, "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["gap_id"] == gap_id
    assert data["approval_id"].startswith("req_")


def test_cli_mark_planned(tmp_path, monkeypatch):
    monkeypatch.setattr(gap_store_mod, "DEFAULT_GAPS_LOG", tmp_path / "gaps.jsonl")
    monkeypatch.setattr(approval_store_mod, "DEFAULT_APPROVALS_LOG", tmp_path / "approvals.jsonl")
    # Save gap, create and approve approval
    gap = make_saved_gap(tmp_path)
    req_id = request_approval_for_gap(
        gap.gap_id,
        gaps_log=tmp_path / "gaps.jsonl",
        approvals_log=tmp_path / "approvals.jsonl",
    )
    approve(req_id, approvals_log=tmp_path / "approvals.jsonl")
    result = runner.invoke(app, [
        "capability-gap", "mark-planned", gap.gap_id,
        "--approval-id", req_id, "--json",
    ])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == GAP_STATUS_PLANNED
