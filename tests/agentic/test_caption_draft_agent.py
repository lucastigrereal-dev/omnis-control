"""Testes para CaptionDraftAgent."""
import uuid
import pytest

from src.agentic.agent_models import AgentRun, AgentRunRepository, AgentRunStatus, StepStatus
from src.agentic.caption_draft_agent import CaptionDraftAgent
from src.agentic.llm_adapter import MockLLMAdapter
from src.caption_approval.drafts import DraftsManager
from src.caption_approval.models import DraftStatus
from src.content_queue.queue import Queue
from src.content_queue.models import QueueItem, QueueStatus
from src.memory.interface import MemoryInterface


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_queue_with_item(tmp_path, account="@oinatalrn", objective="alcance"):
    path = str(tmp_path / "queue.jsonl")
    q = Queue(path=path)
    item = QueueItem(
        queue_id=uuid.uuid4().hex[:12],
        account_handle=account,
        date="2026-06-01",
        time="10:00",
        format="feed",
        objective=objective,
        status=QueueStatus.PLANNED,
    )
    with open(path, "a") as f:
        import json
        f.write(json.dumps(item.to_dict()) + "\n")
    return q, item.queue_id


def _make_agent(tmp_path, dry_run=True):
    queue, queue_id = _make_queue_with_item(tmp_path)
    drafts = DraftsManager(
        drafts_path=str(tmp_path / "drafts.jsonl"),
        log_path=str(tmp_path / "log.jsonl"),
    )
    memory = MemoryInterface(dry_run=True)
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    agent = CaptionDraftAgent(dry_run=dry_run, queue=queue, drafts_manager=drafts, memory=memory, repo=repo)
    return agent, queue_id, repo


# ── dry_run=True ─────────────────────────────────────────────────────────────

def test_agent_dry_run_returns_run(tmp_path):
    agent, queue_id, _ = _make_agent(tmp_path)
    run = agent.run(queue_id)
    assert isinstance(run, AgentRun)
    assert run.status == AgentRunStatus.DRY_RUN


def test_agent_dry_run_has_6_steps(tmp_path):
    agent, queue_id, _ = _make_agent(tmp_path)
    run = agent.run(queue_id)
    assert len(run.steps) == 6
    step_names = [s.name for s in run.steps]
    assert "approval_gate" in step_names
    assert "memory_writeback" in step_names


def test_agent_dry_run_all_steps_ok(tmp_path):
    agent, queue_id, _ = _make_agent(tmp_path)
    run = agent.run(queue_id)
    for step in run.steps:
        assert step.status == StepStatus.OK, f"Step {step.name} falhou: {step.error}"


def test_agent_dry_run_result_has_draft_id(tmp_path):
    agent, queue_id, _ = _make_agent(tmp_path)
    run = agent.run(queue_id)
    assert "draft_id" in run.result
    assert run.result["draft_id"].startswith("dry-")


def test_agent_dry_run_result_has_hashtags(tmp_path):
    agent, queue_id, _ = _make_agent(tmp_path)
    run = agent.run(queue_id)
    assert len(run.result["hashtags"]) > 0


def test_agent_run_persisted(tmp_path):
    agent, queue_id, repo = _make_agent(tmp_path)
    run = agent.run(queue_id)
    saved = repo.get(run.run_id)
    assert saved is not None
    assert saved.run_id == run.run_id


def test_agent_sets_account_handle(tmp_path):
    agent, queue_id, _ = _make_agent(tmp_path)
    run = agent.run(queue_id)
    assert run.account_handle == "@oinatalrn"


def test_agent_sets_objective(tmp_path):
    agent, queue_id, _ = _make_agent(tmp_path)
    run = agent.run(queue_id)
    assert run.objective == "alcance"


# ── queue item not found ──────────────────────────────────────────────────────

def test_agent_missing_queue_item(tmp_path):
    queue = Queue(path=str(tmp_path / "empty.jsonl"))
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    agent = CaptionDraftAgent(dry_run=True, queue=queue, repo=repo)
    run = agent.run("nonexistent-id")
    assert run.status == AgentRunStatus.FAILED
    assert run.error is not None


# ── different objectives ──────────────────────────────────────────────────────

@pytest.mark.parametrize("objective", ["alcance", "conversao", "autoridade", "relacionamento"])
def test_agent_objectives(tmp_path, objective):
    path = str(tmp_path / f"queue_{objective}.jsonl")
    q = Queue(path=path)
    import json
    item = QueueItem(
        queue_id=uuid.uuid4().hex[:12],
        account_handle="@lucastigrereal",
        date="2026-06-01",
        time="10:00",
        format="reels",
        objective=objective,
        status=QueueStatus.PLANNED,
    )
    with open(path, "a") as f:
        f.write(json.dumps(item.to_dict()) + "\n")
    repo = AgentRunRepository(path=str(tmp_path / f"runs_{objective}.jsonl"))
    agent = CaptionDraftAgent(dry_run=True, queue=q, repo=repo)
    run = agent.run(item.queue_id)
    assert run.status == AgentRunStatus.DRY_RUN


# ── real write (dry_run=False) ────────────────────────────────────────────────

def test_agent_real_creates_draft(tmp_path):
    queue, queue_id = _make_queue_with_item(tmp_path)
    drafts = DraftsManager(
        drafts_path=str(tmp_path / "drafts.jsonl"),
        log_path=str(tmp_path / "log.jsonl"),
    )
    memory = MemoryInterface(dry_run=True)
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    agent = CaptionDraftAgent(
        dry_run=False, queue=queue, drafts_manager=drafts,
        memory=memory, repo=repo, llm=MockLLMAdapter(),
    )
    run = agent.run(queue_id)
    assert run.status == AgentRunStatus.COMPLETED
    draft_id = run.result["draft_id"]
    assert not draft_id.startswith("dry-")
    draft = drafts.get(draft_id)
    assert draft is not None
    assert draft.account_handle == "@oinatalrn"


# ── LLM adapter integration ───────────────────────────────────────────────────

def test_agent_uses_injected_llm(tmp_path):
    queue, queue_id = _make_queue_with_item(tmp_path)
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    agent = CaptionDraftAgent(
        dry_run=True, queue=queue, repo=repo, llm=MockLLMAdapter(),
    )
    run = agent.run(queue_id)
    assert run.status == AgentRunStatus.DRY_RUN
    assert run.result["model_used"] == "mock/deterministic"


def test_agent_result_has_model_used(tmp_path):
    agent, queue_id, _ = _make_agent(tmp_path)
    run = agent.run(queue_id)
    assert "model_used" in run.result
    assert "tokens_used" in run.result


def test_agent_result_caption_len_positive(tmp_path):
    agent, queue_id, _ = _make_agent(tmp_path)
    run = agent.run(queue_id)
    assert run.result["caption_len"] > 0


# ── Memory writeback ──────────────────────────────────────────────────────────

def test_agent_dry_run_no_writeback(tmp_path):
    agent, queue_id, _ = _make_agent(tmp_path)
    run = agent.run(queue_id)
    assert run.result["memory_written"] is False


def test_agent_real_approved_writes_memory(tmp_path):
    from src.memory.caption_memory import CaptionMemoryWriter, CaptionMemoryReader
    mem_path = str(tmp_path / "caption_memory.jsonl")
    queue, queue_id = _make_queue_with_item(tmp_path)
    drafts = DraftsManager(
        drafts_path=str(tmp_path / "drafts.jsonl"),
        log_path=str(tmp_path / "log.jsonl"),
    )
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    writer = CaptionMemoryWriter(path=mem_path)
    agent = CaptionDraftAgent(
        dry_run=False, queue=queue, drafts_manager=drafts,
        repo=repo, llm=MockLLMAdapter(), memory_writer=writer,
    )
    run = agent.run(queue_id)
    assert run.result["memory_written"] is True
    reader = CaptionMemoryReader(path=mem_path)
    assert reader.count("@oinatalrn") == 1


def test_agent_real_approved_memory_readable_next_run(tmp_path):
    from src.memory.caption_memory import CaptionMemoryWriter, CaptionMemoryReader
    mem_path = str(tmp_path / "caption_memory.jsonl")
    queue, queue_id = _make_queue_with_item(tmp_path)
    drafts = DraftsManager(
        drafts_path=str(tmp_path / "drafts.jsonl"),
        log_path=str(tmp_path / "log.jsonl"),
    )
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    writer = CaptionMemoryWriter(path=mem_path)
    agent = CaptionDraftAgent(
        dry_run=False, queue=queue, drafts_manager=drafts,
        repo=repo, llm=MockLLMAdapter(), memory_writer=writer,
    )
    agent.run(queue_id)
    reader = CaptionMemoryReader(path=mem_path)
    similar = reader.find_similar("@oinatalrn", "alcance")
    assert len(similar) == 1
    assert len(similar[0]) > 0


def test_agent_needs_review_no_writeback(tmp_path):
    from src.memory.caption_memory import CaptionMemoryWriter, CaptionMemoryReader
    from src.agentic.llm_adapter import CaptionLLMOutput

    class BlockedMockLLM:
        def generate_caption(self, prompt):
            return CaptionLLMOutput(
                hook="[HOOK A REVISAR]", body="corpo", cta="cta",
                hashtags=["#x"], raw="[HOOK A REVISAR]\ncorpo\ncta",
                model_used="mock/blocked", tokens_used=0,
            )

    mem_path = str(tmp_path / "caption_memory.jsonl")
    queue, queue_id = _make_queue_with_item(tmp_path)
    drafts = DraftsManager(
        drafts_path=str(tmp_path / "drafts.jsonl"),
        log_path=str(tmp_path / "log.jsonl"),
    )
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    writer = CaptionMemoryWriter(path=mem_path)
    agent = CaptionDraftAgent(
        dry_run=False, queue=queue, drafts_manager=drafts,
        repo=repo, llm=BlockedMockLLM(), memory_writer=writer,
    )
    run = agent.run(queue_id)
    assert run.result["gate_verdict"] == "needs_review"
    assert run.result["memory_written"] is False
    reader = CaptionMemoryReader(path=mem_path)
    assert reader.count() == 0


# ── Approval Gate — dry_run ───────────────────────────────────────────────────

def test_agent_dry_run_gate_verdict(tmp_path):
    agent, queue_id, _ = _make_agent(tmp_path)
    run = agent.run(queue_id)
    assert run.result["gate_verdict"] == "approved_dry"
    assert run.result["gate_blocks"] == []


def test_agent_dry_run_queue_status_caption_ready(tmp_path):
    agent, queue_id, _ = _make_agent(tmp_path)
    run = agent.run(queue_id)
    assert run.result["queue_status"] == "caption_ready"


# ── Approval Gate — real (dry_run=False) ──────────────────────────────────────

def test_agent_real_gate_approves_clean_caption(tmp_path):
    queue, queue_id = _make_queue_with_item(tmp_path)
    drafts = DraftsManager(
        drafts_path=str(tmp_path / "drafts.jsonl"),
        log_path=str(tmp_path / "log.jsonl"),
    )
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    agent = CaptionDraftAgent(
        dry_run=False, queue=queue, drafts_manager=drafts,
        repo=repo, llm=MockLLMAdapter(),
    )
    run = agent.run(queue_id)
    assert run.result["gate_verdict"] == "approved"
    assert run.result["queue_status"] == "caption_ready"


def test_agent_real_gate_queue_item_updated(tmp_path):
    queue, queue_id = _make_queue_with_item(tmp_path)
    drafts = DraftsManager(
        drafts_path=str(tmp_path / "drafts.jsonl"),
        log_path=str(tmp_path / "log.jsonl"),
    )
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    agent = CaptionDraftAgent(
        dry_run=False, queue=queue, drafts_manager=drafts,
        repo=repo, llm=MockLLMAdapter(),
    )
    agent.run(queue_id)
    item = queue.get(queue_id)
    assert item is not None
    assert item.status == "caption_ready"


def test_agent_real_gate_draft_approved(tmp_path):
    queue, queue_id = _make_queue_with_item(tmp_path)
    drafts = DraftsManager(
        drafts_path=str(tmp_path / "drafts.jsonl"),
        log_path=str(tmp_path / "log.jsonl"),
    )
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    agent = CaptionDraftAgent(
        dry_run=False, queue=queue, drafts_manager=drafts,
        repo=repo, llm=MockLLMAdapter(),
    )
    run = agent.run(queue_id)
    draft = drafts.get(run.result["draft_id"])
    assert draft is not None
    assert draft.status == DraftStatus.APPROVED


# ── LLM failure handling ──────────────────────────────────────────────────────

class _FailingLLM:
    """Simula LiteLLMAdapter com servidor indisponível."""
    def generate_caption(self, prompt):
        import urllib.error
        raise urllib.error.URLError("Connection refused")


class _TimeoutLLM:
    """Simula LiteLLMAdapter com timeout."""
    def generate_caption(self, prompt):
        import socket
        raise socket.timeout("timed out")


def test_agent_llm_connection_error_fails_gracefully(tmp_path):
    queue, queue_id = _make_queue_with_item(tmp_path)
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    agent = CaptionDraftAgent(
        dry_run=False, queue=queue, repo=repo, llm=_FailingLLM(),
    )
    run = agent.run(queue_id)
    assert run.status == AgentRunStatus.FAILED
    assert run.error is not None
    assert "falhou" in run.error or "Connection" in run.error


def test_agent_llm_timeout_fails_gracefully(tmp_path):
    queue, queue_id = _make_queue_with_item(tmp_path)
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    agent = CaptionDraftAgent(
        dry_run=False, queue=queue, repo=repo, llm=_TimeoutLLM(),
    )
    run = agent.run(queue_id)
    assert run.status == AgentRunStatus.FAILED


def test_agent_llm_failure_run_persisted(tmp_path):
    queue, queue_id = _make_queue_with_item(tmp_path)
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    agent = CaptionDraftAgent(
        dry_run=False, queue=queue, repo=repo, llm=_FailingLLM(),
    )
    run = agent.run(queue_id)
    saved = repo.get(run.run_id)
    assert saved is not None
    assert saved.status == AgentRunStatus.FAILED


def test_agent_llm_failure_has_error_step(tmp_path):
    queue, queue_id = _make_queue_with_item(tmp_path)
    repo = AgentRunRepository(path=str(tmp_path / "runs.jsonl"))
    agent = CaptionDraftAgent(
        dry_run=False, queue=queue, repo=repo, llm=_FailingLLM(),
    )
    run = agent.run(queue_id)
    error_steps = [s for s in run.steps if s.status == StepStatus.ERROR]
    assert len(error_steps) >= 1
