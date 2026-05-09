"""Tests for render_engine models."""
from src.render_engine.models import RenderResult, RenderStatus


class TestRenderResult:
    def test_status_ok(self):
        r = RenderResult(render_id="r1", package_id="pkg1", status=RenderStatus.OK)
        assert r.status == RenderStatus.OK

    def test_to_dict_has_required_keys(self):
        r = RenderResult(render_id="r1", package_id="pkg1", status=RenderStatus.FAILED)
        d = r.to_dict()
        assert "render_id" in d
        assert "package_id" in d
        assert "status" in d
        assert "html_path" in d
        assert "files_generated" in d
        assert "errors" in d

    def test_status_value_is_string(self):
        r = RenderResult(render_id="r1", package_id="pkg1", status=RenderStatus.OK)
        d = r.to_dict()
        assert d["status"] == "ok"

    def test_defaults_are_empty_lists(self):
        r = RenderResult(render_id="r1", package_id="pkg1", status=RenderStatus.OK)
        assert r.files_generated == []
        assert r.warnings == []
        assert r.errors == []
