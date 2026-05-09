"""Tests for manual_publishing models."""
from src.manual_publishing.models import PublishRecord


class TestPublishRecord:
    def test_to_dict_has_required_keys(self):
        r = PublishRecord(package_id="pkg1", platform="instagram", posted_at="2026-05-09T10:00:00Z", posted_by="lucas")
        d = r.to_dict()
        assert "package_id" in d
        assert "platform" in d
        assert "posted_at" in d
        assert "posted_by" in d
        assert "status" in d

    def test_default_status_is_posted(self):
        r = PublishRecord(package_id="pkg1", platform="instagram", posted_at="x", posted_by="lucas")
        assert r.status == "posted"

    def test_from_dict_roundtrip(self):
        r = PublishRecord(package_id="pkg1", platform="instagram", posted_at="2026-05-09T10:00:00Z", posted_by="lucas", url="http://insta.com/p/abc")
        d = r.to_dict()
        r2 = PublishRecord.from_dict(d)
        assert r2.package_id == r.package_id
        assert r2.url == r.url

    def test_url_optional(self):
        r = PublishRecord(package_id="pkg1", platform="instagram", posted_at="x", posted_by="lucas")
        assert r.url is None
