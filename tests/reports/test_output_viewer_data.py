"""Tests for OutputViewerDataGenerator."""
import json
import pytest
from pathlib import Path
from src.reports.output_viewer_data import OutputViewerDataGenerator


def _make_mission(tmp: Path, mid: str, setor: str = "marketing", objetivo: str = "Test mission", with_exports: bool = False) -> Path:
    d = tmp / mid
    d.mkdir()
    contract = {"mission_id": mid, "setor": setor, "objetivo": objetivo, "status": "open"}
    (d / "mission_contract.json").write_text(json.dumps(contract), encoding="utf-8")
    if with_exports:
        exports = d / "06_exports"
        exports.mkdir()
        manifest = {"mission_id": mid, "files": [{"path": "05_outputs/out.md", "size_bytes": 100, "ext": ".md"}], "total_files": 1, "total_bytes": 100}
        (exports / "outputs_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (exports / "final_package.zip").write_bytes(b"PK")
    return d


def test_generate_returns_dict_with_missions_key(tmp_path):
    _make_mission(tmp_path, "MIS-001")
    gen = OutputViewerDataGenerator()
    result = gen.generate(tmp_path)
    assert "missions" in result
    assert isinstance(result["missions"], list)


def test_each_mission_has_required_fields(tmp_path):
    _make_mission(tmp_path, "MIS-001", setor="app_factory", objetivo="Build app")
    gen = OutputViewerDataGenerator()
    result = gen.generate(tmp_path)
    assert len(result["missions"]) == 1
    m = result["missions"][0]
    for field in ("id", "name", "type", "status", "files", "zip_path", "next_action", "mission_path"):
        assert field in m, f"Missing field: {field}"


def test_generate_js_writes_valid_js_file(tmp_path):
    _make_mission(tmp_path, "MIS-001")
    out_js = tmp_path / "outputs_data.js"
    gen = OutputViewerDataGenerator()
    path = gen.generate_js(tmp_path, out_js)
    content = path.read_text(encoding="utf-8")
    assert content.startswith("const OUTPUTS_DATA = ")
    assert content.endswith(";\n")
    # extract JSON portion
    json_str = content[len("const OUTPUTS_DATA = "):-2]
    data = json.loads(json_str)
    assert "missions" in data


def test_filter_by_type(tmp_path):
    _make_mission(tmp_path, "MIS-001", setor="marketing")
    _make_mission(tmp_path, "MIS-002", setor="app_factory")
    gen = OutputViewerDataGenerator()
    result = gen.generate(tmp_path)
    content_missions = [m for m in result["missions"] if m["type"] == "content"]
    app_missions = [m for m in result["missions"] if m["type"] == "app"]
    assert len(content_missions) == 1
    assert len(app_missions) == 1


def test_status_pronto_when_zip_exists(tmp_path):
    _make_mission(tmp_path, "MIS-001", with_exports=True)
    gen = OutputViewerDataGenerator()
    result = gen.generate(tmp_path)
    assert result["missions"][0]["status"] == "pronto"
    assert result["missions"][0]["zip_path"] != ""


def test_status_falta_when_no_exports(tmp_path):
    _make_mission(tmp_path, "MIS-001", with_exports=False)
    gen = OutputViewerDataGenerator()
    result = gen.generate(tmp_path)
    assert result["missions"][0]["status"] == "falta"
