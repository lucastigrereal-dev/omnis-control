"""Tests for CockpitGenerator (Fase F)."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from src.reports.cockpit_generator import CockpitGenerator, MissionMeta, _rel


@pytest.fixture
def tmp_cockpit(tmp_path: Path):
    return tmp_path / "cockpit"


@pytest.fixture
def tmp_missions(tmp_path: Path):
    return tmp_path / "missions"


class TestMissionMeta:
    def test_to_dict(self):
        m = MissionMeta(
            mission_id="MIS-20260518-001",
            status="open",
            setor="marketing",
            objetivo="campanha hotel",
        )
        d = m.to_dict()
        assert d["mission_id"] == "MIS-20260518-001"
        assert d["status"] == "open"
        assert d["setor"] == "marketing"
        assert d["objetivo"] == "campanha hotel"


class TestCockpitGeneratorScan:
    def test_scan_empty(self, tmp_missions: Path):
        gen = CockpitGenerator(missions_root=tmp_missions)
        result = gen._scan_missions()
        assert result == []

    def test_scan_single_mission(self, tmp_missions: Path):
        mission_dir = tmp_missions / "MIS-20260518-001"
        mission_dir.mkdir(parents=True)
        contract = {
            "mission_id": "MIS-20260518-001",
            "timestamp": "2026-05-18T10:00:00Z",
            "status": "open",
            "setor": "sales",
            "objetivo": "prospecting leads",
            "criado_por": "test",
        }
        (mission_dir / "mission_contract.json").write_text(
            json.dumps(contract), encoding="utf-8"
        )
        (mission_dir / "05_outputs").mkdir()
        (mission_dir / "05_outputs" / "file.txt").write_text("x")
        (mission_dir / "06_exports").mkdir()

        gen = CockpitGenerator(missions_root=tmp_missions)
        result = gen._scan_missions()
        assert len(result) == 1
        m = result[0]
        assert m.mission_id == "MIS-20260518-001"
        assert m.status == "open"
        assert m.setor == "sales"
        assert m.outputs_count == 1
        assert m.exports_count == 0
        assert m.has_report is False

    def test_scan_closed_mission(self, tmp_missions: Path):
        mission_dir = tmp_missions / "MIS-20260518-002"
        mission_dir.mkdir(parents=True)
        contract = {
            "mission_id": "MIS-20260518-002",
            "timestamp": "2026-05-18T09:00:00Z",
            "status": "closed",
            "setor": "general",
            "objetivo": "x",
            "criado_por": "test",
            "closed_at": "2026-05-18T12:00:00Z",
        }
        (mission_dir / "mission_contract.json").write_text(
            json.dumps(contract), encoding="utf-8"
        )
        (mission_dir / "relatorio_final.md").write_text("# Report", encoding="utf-8")

        gen = CockpitGenerator(missions_root=tmp_missions)
        result = gen._scan_missions()
        assert result[0].status == "closed"
        assert result[0].has_report is True

    def test_scan_with_approval_pending(self, tmp_missions: Path):
        mission_dir = tmp_missions / "MIS-20260518-003"
        mission_dir.mkdir(parents=True)
        contract = {
            "mission_id": "MIS-20260518-003",
            "timestamp": "2026-05-18T08:00:00Z",
            "status": "open",
            "setor": "general",
            "objetivo": "y",
            "criado_por": "test",
        }
        (mission_dir / "mission_contract.json").write_text(
            json.dumps(contract), encoding="utf-8"
        )
        (mission_dir / "07_approval").mkdir(parents=True)
        (mission_dir / "07_approval" / "approval_request.md").write_text("approve me", encoding="utf-8")

        gen = CockpitGenerator(missions_root=tmp_missions)
        result = gen._scan_missions()
        assert result[0].has_approval_pending is True

    def test_scan_sorts_open_first(self, tmp_missions: Path):
        for mid, status in [("MIS-20260518-004", "closed"), ("MIS-20260518-005", "open")]:
            d = tmp_missions / mid
            d.mkdir(parents=True)
            contract = {
                "mission_id": mid,
                "timestamp": "2026-05-18T10:00:00Z",
                "status": status,
                "setor": "general",
                "objetivo": "z",
                "criado_por": "test",
            }
            (d / "mission_contract.json").write_text(json.dumps(contract), encoding="utf-8")

        gen = CockpitGenerator(missions_root=tmp_missions)
        result = gen._scan_missions()
        assert result[0].status == "open"
        assert result[1].status == "closed"


class TestCockpitGeneratorHtml:
    def test_generate_all_files(self, tmp_missions: Path, tmp_cockpit: Path):
        gen = CockpitGenerator(missions_root=tmp_missions, cockpit_dir=tmp_cockpit)
        files = gen.generate_all()
        assert len(files) == 6
        names = {f.name for f in files}
        assert names == {
            "missions_data.js",
            "index.html",
            "mission.html",
            "approvals.html",
            "outputs.html",
            "styles.css",
        }

    def test_index_html_empty(self, tmp_missions: Path, tmp_cockpit: Path):
        gen = CockpitGenerator(missions_root=tmp_missions, cockpit_dir=tmp_cockpit)
        gen.generate_all()
        index = (tmp_cockpit / "index.html").read_text(encoding="utf-8")
        assert "Nenhuma missão encontrada" in index
        assert "omnis mission" in index

    def test_index_html_with_missions(self, tmp_missions: Path, tmp_cockpit: Path):
        mission_dir = tmp_missions / "MIS-20260518-006"
        mission_dir.mkdir(parents=True)
        contract = {
            "mission_id": "MIS-20260518-006",
            "timestamp": "2026-05-18T10:00:00Z",
            "status": "open",
            "setor": "marketing",
            "objetivo": "campanha hotel",
            "criado_por": "test",
        }
        (mission_dir / "mission_contract.json").write_text(
            json.dumps(contract), encoding="utf-8"
        )

        gen = CockpitGenerator(missions_root=tmp_missions, cockpit_dir=tmp_cockpit)
        gen.generate_all()
        index = (tmp_cockpit / "index.html").read_text(encoding="utf-8")
        assert "MIS-20260518-006" in index
        assert "campanha hotel" in index
        assert "marketing" in index
        assert 'status-open' in index

    def test_approvals_html_pending(self, tmp_missions: Path, tmp_cockpit: Path):
        mission_dir = tmp_missions / "MIS-20260518-007"
        mission_dir.mkdir(parents=True)
        contract = {
            "mission_id": "MIS-20260518-007",
            "timestamp": "2026-05-18T10:00:00Z",
            "status": "open",
            "setor": "sales",
            "objetivo": "prospecting",
            "criado_por": "test",
        }
        (mission_dir / "mission_contract.json").write_text(json.dumps(contract), encoding="utf-8")
        (mission_dir / "07_approval").mkdir(parents=True)
        (mission_dir / "07_approval" / "approval_request.md").write_text("x", encoding="utf-8")

        gen = CockpitGenerator(missions_root=tmp_missions, cockpit_dir=tmp_cockpit)
        gen.generate_all()
        appr = (tmp_cockpit / "approvals.html").read_text(encoding="utf-8")
        assert "MIS-20260518-007" in appr
        assert "prospecting" in appr

    def test_outputs_html_skips_empty(self, tmp_missions: Path, tmp_cockpit: Path):
        mission_dir = tmp_missions / "MIS-20260518-008"
        mission_dir.mkdir(parents=True)
        contract = {
            "mission_id": "MIS-20260518-008",
            "timestamp": "2026-05-18T10:00:00Z",
            "status": "open",
            "setor": "general",
            "objetivo": "x",
            "criado_por": "test",
        }
        (mission_dir / "mission_contract.json").write_text(json.dumps(contract), encoding="utf-8")

        gen = CockpitGenerator(missions_root=tmp_missions, cockpit_dir=tmp_cockpit)
        gen.generate_all()
        out = (tmp_cockpit / "outputs.html").read_text(encoding="utf-8")
        assert "Nenhum output ou export encontrado" in out

    def test_outputs_html_shows_with_data(self, tmp_missions: Path, tmp_cockpit: Path):
        mission_dir = tmp_missions / "MIS-20260518-009"
        mission_dir.mkdir(parents=True)
        contract = {
            "mission_id": "MIS-20260518-009",
            "timestamp": "2026-05-18T10:00:00Z",
            "status": "closed",
            "setor": "general",
            "objetivo": "x",
            "criado_por": "test",
        }
        (mission_dir / "mission_contract.json").write_text(json.dumps(contract), encoding="utf-8")
        (mission_dir / "05_outputs").mkdir()
        (mission_dir / "05_outputs" / "a.txt").write_text("x")
        (mission_dir / "relatorio_final.md").write_text("# Report", encoding="utf-8")

        gen = CockpitGenerator(missions_root=tmp_missions, cockpit_dir=tmp_cockpit)
        gen.generate_all()
        out = (tmp_cockpit / "outputs.html").read_text(encoding="utf-8")
        assert "MIS-20260518-009" in out
        assert "1" in out

    def test_missions_data_js(self, tmp_missions: Path, tmp_cockpit: Path):
        mission_dir = tmp_missions / "MIS-20260518-010"
        mission_dir.mkdir(parents=True)
        contract = {
            "mission_id": "MIS-20260518-010",
            "timestamp": "2026-05-18T10:00:00Z",
            "status": "open",
            "setor": "general",
            "objetivo": "x",
            "criado_por": "test",
        }
        (mission_dir / "mission_contract.json").write_text(json.dumps(contract), encoding="utf-8")

        gen = CockpitGenerator(missions_root=tmp_missions, cockpit_dir=tmp_cockpit)
        gen.generate_all()
        js = (tmp_cockpit / "missions_data.js").read_text(encoding="utf-8")
        assert js.startswith("window.MISSIONS_DATA = ")
        assert "MIS-20260518-010" in js

    def test_escape_html(self, tmp_missions: Path, tmp_cockpit: Path):
        mission_dir = tmp_missions / "MIS-20260518-011"
        mission_dir.mkdir(parents=True)
        contract = {
            "mission_id": "MIS-20260518-011",
            "timestamp": "2026-05-18T10:00:00Z",
            "status": "open",
            "setor": "general",
            "objetivo": "test <script> alert(1) </script>",
            "criado_por": "test",
        }
        (mission_dir / "mission_contract.json").write_text(
            json.dumps(contract), encoding="utf-8"
        )

        gen = CockpitGenerator(missions_root=tmp_missions, cockpit_dir=tmp_cockpit)
        gen.generate_all()
        index = (tmp_cockpit / "index.html").read_text(encoding="utf-8")
        assert "<script>" not in index
        assert "&lt;script&gt;" in index

    def test_mission_html_contains_template(self, tmp_missions: Path, tmp_cockpit: Path):
        gen = CockpitGenerator(missions_root=tmp_missions, cockpit_dir=tmp_cockpit)
        gen.generate_all()
        html = (tmp_cockpit / "mission.html").read_text(encoding="utf-8")
        assert "window.MISSIONS_DATA" in html
        assert "m-id" in html
        assert "m-status" in html


class TestHelpers:
    def test_rel_same_root(self, tmp_path: Path):
        root = tmp_path
        path = tmp_path / "a" / "b"
        assert _rel(path, root) == "a/b"

    def test_rel_outside_root(self, tmp_path: Path):
        root = tmp_path / "a"
        path = tmp_path / "b" / "c"
        # Quando path não está sob root, retorna o path absoluto normalizado
        result = _rel(path, root)
        assert "b/c" in result
