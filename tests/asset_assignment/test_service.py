"""Tests for Asset Assignment Center service — P1.9."""
import pytest
from unittest.mock import patch, MagicMock

import src.asset_assignment.service as svc_mod
from src.asset_assignment import check_assignment_status, add_mock_asset, list_ready_candidates
from src.asset_assignment.models import AssetAssignmentResult
from tests.asset_assignment.conftest import (
    FAKE_QUEUE_ITEM, FAKE_QUEUE_ITEM_WITH_ASSET, FAKE_ASSET, FAKE_DRAFT
)


def _mock_queue(item):
    q = MagicMock()
    q.get.return_value = item
    return q


def _mock_drafts(has_approved=True):
    dm = MagicMock()
    dm.list_all.return_value = [FAKE_DRAFT] if has_approved else []
    return dm


def _mock_registry(asset=None):
    reg = MagicMock()
    reg.get.return_value = asset
    return reg


class TestCheckAssignmentStatus:
    def test_returns_asset_assignment_result(self):
        with patch("src.content_queue.queue.Queue", return_value=_mock_queue(FAKE_QUEUE_ITEM)):
            with patch("src.caption_approval.drafts.DraftsManager", return_value=_mock_drafts()):
                result = check_assignment_status("0b79aa1c")
        assert isinstance(result, AssetAssignmentResult)

    def test_blocked_when_queue_not_found(self):
        with patch("src.content_queue.queue.Queue", return_value=_mock_queue(None)):
            result = check_assignment_status("nonexistent_id")
        assert not result.ready_for_package
        assert result.blockers

    def test_blocked_when_no_asset(self):
        with patch("src.content_queue.queue.Queue", return_value=_mock_queue(FAKE_QUEUE_ITEM)):
            with patch("src.caption_approval.drafts.DraftsManager", return_value=_mock_drafts()):
                result = check_assignment_status("0b79aa1c")
        assert not result.ready_for_package
        assert any("asset" in b.lower() for b in result.blockers)

    def test_not_ready_when_asset_but_no_caption(self):
        with patch("src.content_queue.queue.Queue", return_value=_mock_queue(FAKE_QUEUE_ITEM_WITH_ASSET)):
            with patch("src.video_assets.registry.Registry", return_value=_mock_registry(FAKE_ASSET)):
                with patch("src.caption_approval.drafts.DraftsManager", return_value=_mock_drafts(False)):
                    result = check_assignment_status("0b79aa1c")
        assert not result.ready_for_package

    def test_ready_when_asset_and_caption(self):
        with patch("src.content_queue.queue.Queue", return_value=_mock_queue(FAKE_QUEUE_ITEM_WITH_ASSET)):
            with patch("src.video_assets.registry.Registry", return_value=_mock_registry(FAKE_ASSET)):
                with patch("src.caption_approval.drafts.DraftsManager", return_value=_mock_drafts()):
                    result = check_assignment_status("0b79aa1c")
        assert result.ready_for_package

    def test_account_handle_from_queue(self):
        with patch("src.content_queue.queue.Queue", return_value=_mock_queue(FAKE_QUEUE_ITEM)):
            with patch("src.caption_approval.drafts.DraftsManager", return_value=_mock_drafts()):
                result = check_assignment_status("0b79aa1c")
        assert result.account_handle == "afamiliatigrereal"

    def test_caption_id_populated_when_approved(self):
        with patch("src.content_queue.queue.Queue", return_value=_mock_queue(FAKE_QUEUE_ITEM)):
            with patch("src.caption_approval.drafts.DraftsManager", return_value=_mock_drafts()):
                result = check_assignment_status("0b79aa1c")
        assert result.caption_id == "1d482d82"

    def test_asset_id_populated_when_assigned(self):
        with patch("src.content_queue.queue.Queue", return_value=_mock_queue(FAKE_QUEUE_ITEM_WITH_ASSET)):
            with patch("src.video_assets.registry.Registry", return_value=_mock_registry(FAKE_ASSET)):
                with patch("src.caption_approval.drafts.DraftsManager", return_value=_mock_drafts()):
                    result = check_assignment_status("0b79aa1c")
        assert result.asset_id == "mock_test_001"

    def test_next_actions_present_when_no_asset(self):
        with patch("src.content_queue.queue.Queue", return_value=_mock_queue(FAKE_QUEUE_ITEM)):
            with patch("src.caption_approval.drafts.DraftsManager", return_value=_mock_drafts()):
                result = check_assignment_status("0b79aa1c")
        assert len(result.next_actions) > 0

    def test_next_action_includes_package_command_when_ready(self):
        with patch("src.content_queue.queue.Queue", return_value=_mock_queue(FAKE_QUEUE_ITEM_WITH_ASSET)):
            with patch("src.video_assets.registry.Registry", return_value=_mock_registry(FAKE_ASSET)):
                with patch("src.caption_approval.drafts.DraftsManager", return_value=_mock_drafts()):
                    result = check_assignment_status("0b79aa1c")
        assert any("offline" in a for a in result.next_actions)

    def test_to_dict(self):
        with patch("src.content_queue.queue.Queue", return_value=_mock_queue(FAKE_QUEUE_ITEM)):
            with patch("src.caption_approval.drafts.DraftsManager", return_value=_mock_drafts()):
                result = check_assignment_status("0b79aa1c")
        d = result.to_dict()
        assert "queue_id" in d
        assert "ready_for_package" in d
        assert "blockers" in d


class TestAddMockAsset:
    def test_returns_dict_with_asset_id(self, tmp_path):
        registry_path = str(tmp_path / "assets.jsonl")
        result = add_mock_asset("test.jpg", registry_path=registry_path)
        assert "asset_id" in result
        assert result["asset_id"].startswith("mock_")

    def test_mock_flag_is_true(self, tmp_path):
        registry_path = str(tmp_path / "assets.jsonl")
        result = add_mock_asset("test.mp4", format="reel", registry_path=registry_path)
        assert result["mock"] is True

    def test_format_stored(self, tmp_path):
        registry_path = str(tmp_path / "assets.jsonl")
        result = add_mock_asset("video.mp4", format="reel", registry_path=registry_path)
        assert result["format"] == "reel"

    def test_asset_persisted_in_registry(self, tmp_path):
        from src.video_assets.registry import Registry
        registry_path = str(tmp_path / "assets.jsonl")
        result = add_mock_asset("test.jpg", registry_path=registry_path)
        reg = Registry(path=registry_path)
        asset = reg.get(result["asset_id"])
        assert asset is not None
        assert asset.asset_id == result["asset_id"]

    def test_no_meta_call(self, tmp_path):
        registry_path = str(tmp_path / "assets.jsonl")
        with patch("requests.post") as mock_post:
            add_mock_asset("test.jpg", registry_path=registry_path)
            mock_post.assert_not_called()


class TestListReadyCandidates:
    def test_returns_list(self):
        result = list_ready_candidates()
        assert isinstance(result, list)

    def test_ready_candidates_have_required_fields(self):
        result = list_ready_candidates()
        for c in result:
            assert "queue_id" in c
            assert "has_asset" in c
            assert "has_caption" in c
            assert "ready_for_package" in c
