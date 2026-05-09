"""Tests for manual_publishing store."""
from src.manual_publishing.models import PublishRecord
from src.manual_publishing.store import append_record, load_all, find_by_package_id


def _make_record(pkg_id="pkg_test"):
    return PublishRecord(package_id=pkg_id, platform="instagram", posted_at="2026-05-09T10:00:00Z", posted_by="lucas")


class TestAppendAndLoad:
    def test_empty_log_returns_empty(self, log_path):
        result = load_all(log_path=log_path)
        assert result == []

    def test_append_and_load(self, log_path):
        r = _make_record()
        append_record(r, log_path=log_path)
        records = load_all(log_path=log_path)
        assert len(records) == 1
        assert records[0].package_id == "pkg_test"

    def test_append_multiple(self, log_path):
        append_record(_make_record("pkg1"), log_path=log_path)
        append_record(_make_record("pkg2"), log_path=log_path)
        records = load_all(log_path=log_path)
        assert len(records) == 2

    def test_creates_parent_dirs(self, tmp_path):
        deep_path = tmp_path / "a" / "b" / "log.jsonl"
        append_record(_make_record(), log_path=deep_path)
        assert deep_path.is_file()


class TestFindByPackageId:
    def test_returns_none_when_not_found(self, log_path):
        result = find_by_package_id("nonexistent", log_path=log_path)
        assert result is None

    def test_finds_exact_match(self, log_path):
        append_record(_make_record("carousel_0b79aa1c"), log_path=log_path)
        result = find_by_package_id("carousel_0b79aa1c", log_path=log_path)
        assert result is not None
        assert result.package_id == "carousel_0b79aa1c"

    def test_finds_prefix_match(self, log_path):
        append_record(_make_record("carousel_0b79aa1c_full"), log_path=log_path)
        result = find_by_package_id("carousel_0b79aa1c", log_path=log_path)
        assert result is not None
