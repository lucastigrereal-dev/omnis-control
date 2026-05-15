"""Tests for argos_bridge models."""
from __future__ import annotations

from src.argos_bridge.models import ArgosDraft, ArgosStatus, WarnCode


class TestArgosDraft:
    def test_defaults(self):
        d = ArgosDraft(
            draft_id="d1",
            queue_id="q1",
            caption_draft_id="cd1",
            account_handle="@test",
        )
        assert d.draft_id == "d1"
        assert d.platform == "instagram"
        assert d.post_type == "feed"
        assert d.status == ArgosStatus.LOCAL_DRAFT
        assert d.hashtags == []
        assert d.warnings == []

    def test_to_dict_roundtrip(self):
        d = ArgosDraft(
            draft_id="d1", queue_id="q1", caption_draft_id="cd1",
            account_handle="@lucastigrereal", caption_text="Hello world",
            hashtags=["#omnis", "#test"], cta="Link in bio",
            warnings=[WarnCode.NO_ASSET_ATTACHED],
        )
        restored = ArgosDraft.from_dict(d.to_dict())
        assert restored.draft_id == "d1"
        assert restored.account_handle == "@lucastigrereal"
        assert restored.caption_text == "Hello world"
        assert restored.hashtags == ["#omnis", "#test"]
        assert WarnCode.NO_ASSET_ATTACHED in restored.warnings

    def test_warn_codes(self):
        """All warning codes are defined as class attributes."""
        assert WarnCode.NO_ASSET_ATTACHED == "NO_ASSET_ATTACHED"
        assert WarnCode.CAPTION_MODIFIED_AFTER_EXPORT == "CAPTION_MODIFIED_AFTER_EXPORT"
        assert WarnCode.QUEUE_ITEM_MISSING == "QUEUE_ITEM_MISSING"
        assert WarnCode.ACCOUNT_NOT_FOUND == "ACCOUNT_NOT_FOUND"
        assert WarnCode.PLACEHOLDER_DETECTED == "PLACEHOLDER_DETECTED"

    def test_status_constants(self):
        assert ArgosStatus.LOCAL_DRAFT == "local_draft"
        assert ArgosStatus.READY_FOR_ARGOS == "ready_for_argos"
        assert ArgosStatus.EXPORTED == "exported"
        assert ArgosStatus.BLOCKED == "blocked"
