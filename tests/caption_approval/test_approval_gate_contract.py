import pytest

from src.caption_approval.approvals import ApprovalGate
from src.caption_approval.drafts import DraftsManager
from src.caption_approval.models import DraftStatus


def test_approval_gate_validate_blocks_empty_caption(tmp_path):
    manager = DraftsManager(str(tmp_path / "drafts.jsonl"), str(tmp_path / "approval.jsonl"))
    gate = ApprovalGate(manager)

    result = gate.validate("", hashtags=["a", "b", "c"], cta="vai")

    assert result.blocked is True
    assert result.to_dict()["passed"] is False


def test_approval_gate_approve_updates_draft_and_queue_callback(tmp_path):
    manager = DraftsManager(str(tmp_path / "drafts.jsonl"), str(tmp_path / "approval.jsonl"))
    draft = manager.create(
        "queue-1",
        "lucastigrereal",
        caption_text="Legenda pronta para publicar",
        hashtags=["viagem", "natal", "familia"],
        cta="Salva",
    )
    manager.submit(draft.draft_id)
    calls = []

    approved, warning = ApprovalGate(manager).approve(
        draft.draft_id,
        queue_updater=lambda queue_id, status: calls.append((queue_id, status)) or True,
    )

    assert approved is not None
    assert approved.status == DraftStatus.APPROVED
    assert warning is None
    assert calls == [("queue-1", "caption_ready")]


def test_approval_gate_reject_requires_reason(tmp_path):
    manager = DraftsManager(str(tmp_path / "drafts.jsonl"), str(tmp_path / "approval.jsonl"))
    draft = manager.create("queue-1", "lucastigrereal")

    with pytest.raises(ValueError, match="Motivo"):
        ApprovalGate(manager).reject(draft.draft_id, "")
