"""Tests for manual_publishing service."""
import pytest
from src.manual_publishing.errors import PublishRecordNotFoundError
from src.manual_publishing.service import mark_published, list_published, get_published


class TestMarkPublished:
    def test_returns_publish_record(self, log_path):
        r = mark_published("pkg1", log_path=log_path)
        assert r.package_id == "pkg1"

    def test_status_is_posted(self, log_path):
        r = mark_published("pkg1", log_path=log_path)
        assert r.status == "posted"

    def test_platform_stored(self, log_path):
        r = mark_published("pkg1", platform="twitter", log_path=log_path)
        assert r.platform == "twitter"

    def test_url_stored(self, log_path):
        r = mark_published("pkg1", url="https://insta.com/p/abc", log_path=log_path)
        assert r.url == "https://insta.com/p/abc"

    def test_posted_at_set(self, log_path):
        r = mark_published("pkg1", log_path=log_path)
        assert r.posted_at

    def test_no_meta_calls(self, log_path):
        from unittest.mock import patch
        with patch("requests.post") as mock_post:
            mark_published("pkg1", log_path=log_path)
            mock_post.assert_not_called()


class TestListPublished:
    def test_empty_list_when_no_records(self, log_path):
        result = list_published(log_path=log_path)
        assert result == []

    def test_lists_records(self, log_path):
        mark_published("pkg1", log_path=log_path)
        mark_published("pkg2", log_path=log_path)
        result = list_published(log_path=log_path)
        assert len(result) == 2

    def test_returns_dicts(self, log_path):
        mark_published("pkg1", log_path=log_path)
        result = list_published(log_path=log_path)
        assert isinstance(result[0], dict)
        assert "package_id" in result[0]


class TestGetPublished:
    def test_raises_when_not_found(self, log_path):
        with pytest.raises(PublishRecordNotFoundError):
            get_published("nonexistent", log_path=log_path)

    def test_returns_dict_when_found(self, log_path):
        mark_published("pkg1", log_path=log_path)
        result = get_published("pkg1", log_path=log_path)
        assert result["package_id"] == "pkg1"
