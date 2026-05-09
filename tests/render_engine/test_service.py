"""Tests for render_engine service."""
import json
import pytest
from pathlib import Path

import src.render_engine.service as svc_mod
from src.render_engine.errors import PackageNotFoundError
from src.render_engine.models import RenderStatus
from src.render_engine.service import render_package, list_renders, get_render


class TestRenderPackage:
    def test_raises_when_package_not_found(self, patched_roots):
        with pytest.raises(PackageNotFoundError):
            render_package("nonexistent_id")

    def test_returns_render_result_ok(self, patched_roots, fake_package_dir):
        export_root, render_root = patched_roots
        result = render_package("carousel_0b79aa1c_test", export_root=export_root, render_root=render_root)
        assert result.status == RenderStatus.OK

    def test_html_file_created_on_disk(self, patched_roots, fake_package_dir):
        export_root, render_root = patched_roots
        result = render_package("carousel_0b79aa1c_test", export_root=export_root, render_root=render_root)
        assert Path(result.html_path).is_file()

    def test_manifest_file_created_on_disk(self, patched_roots, fake_package_dir):
        export_root, render_root = patched_roots
        result = render_package("carousel_0b79aa1c_test", export_root=export_root, render_root=render_root)
        assert Path(result.render_manifest_path).is_file()

    def test_manifest_is_valid_json(self, patched_roots, fake_package_dir):
        export_root, render_root = patched_roots
        result = render_package("carousel_0b79aa1c_test", export_root=export_root, render_root=render_root)
        data = json.loads(Path(result.render_manifest_path).read_text(encoding="utf-8"))
        assert "render_id" in data
        assert "package_id" in data
        assert data["status"] == "ok"

    def test_render_id_starts_with_render_(self, patched_roots, fake_package_dir):
        export_root, render_root = patched_roots
        result = render_package("carousel_0b79aa1c_test", export_root=export_root, render_root=render_root)
        assert result.render_id.startswith("render_")

    def test_html_contains_doctype(self, patched_roots, fake_package_dir):
        export_root, render_root = patched_roots
        result = render_package("carousel_0b79aa1c_test", export_root=export_root, render_root=render_root)
        html = Path(result.html_path).read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html

    def test_no_errors_in_result(self, patched_roots, fake_package_dir):
        export_root, render_root = patched_roots
        result = render_package("carousel_0b79aa1c_test", export_root=export_root, render_root=render_root)
        assert result.errors == []

    def test_never_calls_meta(self, patched_roots, fake_package_dir):
        from unittest.mock import patch
        export_root, render_root = patched_roots
        with patch("requests.post") as mock_post:
            render_package("carousel_0b79aa1c_test", export_root=export_root, render_root=render_root)
            mock_post.assert_not_called()

    def test_no_secret_in_html(self, patched_roots, fake_package_dir):
        export_root, render_root = patched_roots
        result = render_package("carousel_0b79aa1c_test", export_root=export_root, render_root=render_root)
        html = Path(result.html_path).read_text(encoding="utf-8")
        for secret in ["access_token", "META_APP_SECRET", "client_secret"]:
            assert secret not in html


class TestListRenders:
    def test_empty_when_no_renders(self, patched_roots):
        export_root, render_root = patched_roots
        result = list_renders(render_root=render_root)
        assert result == []

    def test_lists_after_render(self, patched_roots, fake_package_dir):
        export_root, render_root = patched_roots
        render_package("carousel_0b79aa1c_test", export_root=export_root, render_root=render_root)
        result = list_renders(render_root=render_root)
        assert len(result) == 1
        assert "render_id" in result[0]

    def test_returns_dicts(self, patched_roots, fake_package_dir):
        export_root, render_root = patched_roots
        render_package("carousel_0b79aa1c_test", export_root=export_root, render_root=render_root)
        result = list_renders(render_root=render_root)
        assert isinstance(result[0], dict)


class TestGetRender:
    def test_returns_none_when_not_found(self, patched_roots):
        export_root, render_root = patched_roots
        assert get_render("nonexistent", render_root=render_root) is None

    def test_returns_dict_when_found(self, patched_roots, fake_package_dir):
        export_root, render_root = patched_roots
        result = render_package("carousel_0b79aa1c_test", export_root=export_root, render_root=render_root)
        entry = get_render(result.render_id, render_root=render_root)
        assert entry is not None
        assert entry["render_id"] == result.render_id
