from src.caption_approval.models import (
    ApprovalLogEntry,
    CaptionDraft,
    CaptionTemplate,
    DraftStatus,
)


def test_caption_draft_round_trip_preserves_optional_fields():
    draft = CaptionDraft(
        draft_id="draft-1",
        queue_id="queue-1",
        account_handle="lucastigrereal",
        status=DraftStatus.REJECTED,
        rejection_reason="rewrite",
        asset_id="asset-1",
    )

    restored = CaptionDraft.from_dict(draft.to_dict())

    assert restored == draft


def test_caption_template_round_trip_allows_format_none():
    template = CaptionTemplate(
        template_id="tpl-1",
        name="Generic",
        objective="alcance",
        format=None,
        hook_template="hook",
        body_template="body",
        cta_template="cta",
    )

    restored = CaptionTemplate.from_dict(template.to_dict())

    assert restored == template


def test_approval_log_round_trip_preserves_metadata():
    entry = ApprovalLogEntry(
        event_id="evt-1",
        draft_id="draft-1",
        queue_id="queue-1",
        action="approved",
        metadata={"source": "test"},
    )

    restored = ApprovalLogEntry.from_dict(entry.to_dict())

    assert restored == entry
