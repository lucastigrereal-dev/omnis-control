"""Tests for quality_layer service."""
import pytest
from src.quality_layer.errors import PackageNotFoundError
from src.quality_layer.models import QualityGrade
from src.quality_layer.service import score_package


class TestScorePackage:
    def test_raises_when_package_not_found(self, patched_roots):
        export_root, render_root = patched_roots
        with pytest.raises(PackageNotFoundError):
            score_package("nonexistent_id", export_root=export_root, render_root=render_root)

    def test_returns_quality_result(self, patched_roots):
        export_root, render_root = patched_roots
        result = score_package("carousel_full_test", export_root=export_root, render_root=render_root)
        assert result.package_id.startswith("carousel_full_test")

    def test_score_is_int_between_0_and_100(self, patched_roots):
        export_root, render_root = patched_roots
        result = score_package("carousel_full_test", export_root=export_root, render_root=render_root)
        assert isinstance(result.score, int)
        assert 0 <= result.score <= 100

    def test_grade_is_valid(self, patched_roots):
        export_root, render_root = patched_roots
        result = score_package("carousel_full_test", export_root=export_root, render_root=render_root)
        assert result.grade in list(QualityGrade)

    def test_full_package_with_render_scores_high(self, patched_roots):
        export_root, render_root = patched_roots
        result = score_package("carousel_full_test", export_root=export_root, render_root=render_root)
        assert result.score >= 90

    def test_checks_passed_list_not_empty(self, patched_roots):
        export_root, render_root = patched_roots
        result = score_package("carousel_full_test", export_root=export_root, render_root=render_root)
        assert len(result.checks_passed) > 0

    def test_no_meta_calls(self, patched_roots):
        from unittest.mock import patch
        export_root, render_root = patched_roots
        with patch("requests.post") as mock_post:
            score_package("carousel_full_test", export_root=export_root, render_root=render_root)
            mock_post.assert_not_called()
