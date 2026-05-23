from types import SimpleNamespace

from src.argos_bridge import draft_builder
from src.argos_bridge.draft_builder import DraftBuilder
from src.argos_bridge.models import WarnCode


def test_draft_builder_creates_argos_draft_with_asset_warning(tmp_path, monkeypatch):
    monkeypatch.setattr(draft_builder, "DRAFTS_PATH", str(tmp_path / "argos_drafts.jsonl"))
    queue_item = SimpleNamespace(
        status="caption_ready",
        asset_id=None,
        account_handle="lucastigrereal",
        format="reels",
        date="2026-05-23",
        time="08:50",
    )
    caption = SimpleNamespace(
        draft_id="cap-1",
        status="approved",
        caption_text="Legenda pronta",
        hashtags=["viagem"],
        cta="Salva",
    )

    draft, errors = DraftBuilder(lambda _id: queue_item, lambda _id: caption).create("queue-1")

    assert errors == []
    assert draft is not None
    assert draft.account_handle == "lucastigrereal"
    assert draft.warnings == [WarnCode.NO_ASSET_ATTACHED]


def test_draft_builder_blocks_missing_queue_item(tmp_path, monkeypatch):
    monkeypatch.setattr(draft_builder, "DRAFTS_PATH", str(tmp_path / "argos_drafts.jsonl"))

    draft, errors = DraftBuilder(lambda _id: None, lambda _id: None).create("queue-1")

    assert draft is None
    assert errors
