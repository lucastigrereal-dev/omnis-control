"""Tests for _load_asset() integration with offline packager — P1.9."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import src.offline_factory.packager as packager_mod
from src.offline_factory.models import PackageStatus
from tests.offline_factory.conftest import FAKE_CAPTION


def _make_queue_item(asset_id=None):
    item = MagicMock()
    item.queue_id = "0b79aa1c"
    item.account_handle = "afamiliatigrereal"
    item.status = "caption_ready"
    item.asset_id = asset_id
    return item


def _make_asset(asset_id="mock_001"):
    asset = MagicMock()
    asset.asset_id = asset_id
    asset.format = "carousel"
    asset.source_path = "[MOCK] test.jpg"

    def to_dict():
        return {
            "asset_id": asset_id,
            "format": "carousel",
            "source_path": "[MOCK] test.jpg",
            "file_name": "test.jpg",
        }
    asset.to_dict = to_dict
    return asset


class TestLoadAssetRealFlow:
    def test_load_asset_returns_none_when_no_asset_id(self, monkeypatch, tmp_path):
        monkeypatch.setattr(packager_mod, "EXPORT_ROOT", tmp_path / "offline_factory")
        q_mock = MagicMock()
        q_mock.get.return_value = _make_queue_item(asset_id=None)
        with patch("src.content_queue.queue.Queue", return_value=q_mock):
            result = packager_mod._load_asset("0b79aa1c")
        assert result is None

    def test_load_asset_returns_dict_when_asset_found(self, monkeypatch, tmp_path):
        monkeypatch.setattr(packager_mod, "EXPORT_ROOT", tmp_path / "offline_factory")
        q_mock = MagicMock()
        q_mock.get.return_value = _make_queue_item(asset_id="mock_001")
        reg_mock = MagicMock()
        reg_mock.get.return_value = _make_asset("mock_001")
        with patch("src.content_queue.queue.Queue", return_value=q_mock):
            with patch("src.video_assets.registry.Registry", return_value=reg_mock):
                result = packager_mod._load_asset("0b79aa1c")
        assert result is not None
        assert result["asset_id"] == "mock_001"

    def test_carousel_package_ready_when_asset_from_registry(self, monkeypatch, tmp_path):
        monkeypatch.setattr(packager_mod, "EXPORT_ROOT", tmp_path / "offline_factory")
        monkeypatch.setattr(packager_mod, "_load_queue_item", lambda *a: None)
        q_mock = MagicMock()
        q_mock.get.return_value = _make_queue_item(asset_id="mock_001")
        reg_mock = MagicMock()
        reg_mock.get.return_value = _make_asset("mock_001")
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch("src.content_queue.queue.Queue", return_value=q_mock):
                with patch("src.video_assets.registry.Registry", return_value=reg_mock):
                    pkg = packager_mod.create_carousel_package("0b79aa1c")
        assert pkg.status == PackageStatus.READY

    def test_carousel_package_partial_when_no_asset_in_registry(self, monkeypatch, tmp_path):
        monkeypatch.setattr(packager_mod, "EXPORT_ROOT", tmp_path / "offline_factory")
        monkeypatch.setattr(packager_mod, "_load_queue_item", lambda *a: None)
        q_mock = MagicMock()
        q_mock.get.return_value = _make_queue_item(asset_id=None)
        with patch.object(packager_mod, "_load_caption", return_value=FAKE_CAPTION):
            with patch("src.content_queue.queue.Queue", return_value=q_mock):
                pkg = packager_mod.create_carousel_package("0b79aa1c")
        assert pkg.status == PackageStatus.PARTIAL

    def test_load_asset_never_calls_meta(self, monkeypatch, tmp_path):
        monkeypatch.setattr(packager_mod, "EXPORT_ROOT", tmp_path / "offline_factory")
        with patch("requests.post") as mock_post:
            packager_mod._load_asset("0b79aa1c")
            mock_post.assert_not_called()
