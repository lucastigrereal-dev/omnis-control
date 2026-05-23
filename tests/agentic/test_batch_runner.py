"""Testes para BatchRunner + BatchReport."""
import json
import uuid
import pytest

from src.agentic.batch_runner import (
    BatchReport, BatchRunner, BatchVerdict, PROCESSABLE_STATUSES,
)
from src.agentic.caption_draft_agent import CaptionDraftAgent
from src.agentic.llm_adapter import MockLLMAdapter
from src.agentic.agent_models import AgentRunRepository
from src.caption_approval.drafts import DraftsManager
from src.content_queue.models import QueueItem, QueueStatus
from src.content_queue.queue import Queue


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_queue(tmp_path, items: list[tuple[str, str, str]] | None = None) -> Queue:
    """items: list of (account, objective, status)"""
    path = str(tmp_path / "queue.jsonl")
    q = Queue(path=path)
    for account, objective, status in (items or []):
        item = QueueItem(
            queue_id=uuid.uuid4().hex[:12],
            account_handle=account,
            date="2026-06-01",
            time="10:00",
            format="feed",
            objective=objective,
            status=status,
        )
        with open(path, "a") as f:
            f.write(json.dumps(item.to_dict()) + "\n")
    return q


def _make_runner(tmp_path, dry_run=True, items=None) -> BatchRunner:
    queue = _make_queue(tmp_path, items)
    drafts = DraftsManager(
        drafts_path=str(tmp_path / "drafts.jsonl"),
        log_path=str(tmp_path / "log.jsonl"),
    )
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    agent = CaptionDraftAgent(
        dry_run=dry_run, queue=queue, drafts_manager=drafts,
        repo=repo, llm=MockLLMAdapter(),
    )
    return BatchRunner(dry_run=dry_run, queue=queue, agent=agent)


# ── BatchReport ───────────────────────────────────────────────────────────────

def test_report_counts_approved():
    from src.agentic.batch_runner import BatchItemResult
    report = BatchReport(
        batch_id="b1", dry_run=True, account_filter=None,
        limit=5, total_candidates=3, total_processed=3,
    )
    report.results = [
        BatchItemResult("q1", "@x", "alcance", "r1", BatchVerdict.APPROVED_DRY),
        BatchItemResult("q2", "@x", "alcance", "r2", BatchVerdict.NEEDS_REVIEW),
        BatchItemResult("q3", "@x", "alcance", "r3", BatchVerdict.FAILED),
    ]
    assert report.approved == 1
    assert report.needs_review == 1
    assert report.failed == 1
    assert report.skipped == 0


def test_report_to_dict():
    report = BatchReport(
        batch_id="b1", dry_run=True, account_filter="@x",
        limit=5, total_candidates=0, total_processed=0,
    )
    report.finish()
    d = report.to_dict()
    assert d["batch_id"] == "b1"
    assert d["dry_run"] is True
    assert d["finished_at"] is not None
    assert "results" in d


# ── BatchRunner — empty queue ─────────────────────────────────────────────────

def test_batch_empty_queue(tmp_path):
    runner = _make_runner(tmp_path, items=[])
    report = runner.run(limit=5)
    assert report.total_candidates == 0
    assert report.total_processed == 0
    assert report.finished_at is not None


def test_batch_empty_returns_report(tmp_path):
    runner = _make_runner(tmp_path, items=[])
    report = runner.run()
    assert isinstance(report, BatchReport)


# ── BatchRunner — dry_run ─────────────────────────────────────────────────────

def test_batch_dry_run_processes_planned(tmp_path):
    items = [("@oinatalrn", "alcance", "planned")] * 3
    runner = _make_runner(tmp_path, dry_run=True, items=items)
    report = runner.run(limit=5)
    assert report.total_processed == 3
    assert report.approved == 3


def test_batch_dry_run_verdict_approved_dry(tmp_path):
    items = [("@oinatalrn", "alcance", "planned")]
    runner = _make_runner(tmp_path, dry_run=True, items=items)
    report = runner.run()
    assert report.results[0].verdict == BatchVerdict.APPROVED_DRY


def test_batch_limit_respected(tmp_path):
    items = [("@oinatalrn", "alcance", "planned")] * 10
    runner = _make_runner(tmp_path, dry_run=True, items=items)
    report = runner.run(limit=3)
    assert report.total_processed == 3
    assert report.total_candidates == 3


def test_batch_account_filter(tmp_path):
    items = [
        ("@oinatalrn", "alcance", "planned"),
        ("@oinatalrn", "alcance", "planned"),
        ("@lucastigrereal", "alcance", "planned"),
    ]
    runner = _make_runner(tmp_path, dry_run=True, items=items)
    report = runner.run(limit=10, account_filter="@oinatalrn")
    assert report.total_processed == 2
    for r in report.results:
        assert r.account_handle == "@oinatalrn"


def test_batch_account_filter_without_at(tmp_path):
    items = [("@oinatalrn", "alcance", "planned")]
    runner = _make_runner(tmp_path, dry_run=True, items=items)
    report = runner.run(limit=5, account_filter="oinatalrn")
    assert report.total_processed == 1


def test_batch_skips_non_processable_status(tmp_path):
    items = [
        ("@x", "alcance", "planned"),
        ("@x", "alcance", "approved"),
        ("@x", "alcance", "published"),
    ]
    runner = _make_runner(tmp_path, dry_run=True, items=items)
    report = runner.run(limit=10)
    assert report.total_processed == 1


def test_batch_processes_needs_caption(tmp_path):
    items = [("@x", "alcance", "needs_caption")]
    runner = _make_runner(tmp_path, dry_run=True, items=items)
    report = runner.run(limit=5)
    assert report.total_processed == 1


def test_batch_result_has_run_id(tmp_path):
    items = [("@oinatalrn", "alcance", "planned")]
    runner = _make_runner(tmp_path, dry_run=True, items=items)
    report = runner.run()
    assert report.results[0].run_id != "error"
    assert len(report.results[0].run_id) > 0


def test_batch_result_has_draft_id(tmp_path):
    items = [("@oinatalrn", "alcance", "planned")]
    runner = _make_runner(tmp_path, dry_run=True, items=items)
    report = runner.run()
    assert report.results[0].draft_id.startswith("dry-")


# ── BatchRunner — real ────────────────────────────────────────────────────────

def test_batch_real_approves_and_updates_queue(tmp_path):
    queue = _make_queue(tmp_path, [("@oinatalrn", "alcance", "planned")])
    drafts = DraftsManager(
        drafts_path=str(tmp_path / "drafts.jsonl"),
        log_path=str(tmp_path / "log.jsonl"),
    )
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    agent = CaptionDraftAgent(
        dry_run=False, queue=queue, drafts_manager=drafts,
        repo=repo, llm=MockLLMAdapter(),
    )
    runner = BatchRunner(dry_run=False, queue=queue, agent=agent)
    report = runner.run(limit=5)
    assert report.approved == 1
    assert report.results[0].verdict == BatchVerdict.APPROVED
    item = queue.list_all()[0]
    assert item.status == "caption_ready"


# ── BatchReport serialization ─────────────────────────────────────────────────

def test_batch_report_roundtrip_json(tmp_path):
    items = [("@x", "alcance", "planned")] * 2
    runner = _make_runner(tmp_path, dry_run=True, items=items)
    report = runner.run()
    d = report.to_dict()
    assert d["total_processed"] == 2
    assert len(d["results"]) == 2
    # serializable
    json.dumps(d)
