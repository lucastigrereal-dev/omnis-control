"""Tests for MissionEngine and MissionContract."""
import json

import pytest

from src.agentic.mission_engine import (
    MissionContract,
    MissionEngine,
    MISSION_STATUS_OPEN,
    MISSION_STATUS_CLOSED,
    MISSION_SUBDIRS,
    _today_str,
)


class TestMissionContract:
    def test_to_dict_contains_all_fields(self):
        c = MissionContract(
            mission_id="MIS-20260518-001",
            timestamp="2026-05-18T10:00:00Z",
            status=MISSION_STATUS_OPEN,
            setor="marketing",
            objetivo="criar campanha hotel",
            criado_por="OMNIS",
        )
        d = c.to_dict()
        assert d["mission_id"] == "MIS-20260518-001"
        assert d["status"] == MISSION_STATUS_OPEN
        assert d["setor"] == "marketing"
        assert d["objetivo"] == "criar campanha hotel"
        assert d["closed_at"] is None
        assert d["mission_path"] is None

    def test_to_dict_from_dict_round_trip(self):
        c = MissionContract(
            mission_id="MIS-20260518-002",
            timestamp="2026-05-18T12:00:00Z",
            status=MISSION_STATUS_OPEN,
            setor="sales",
            objetivo="qualificar leads SP",
            criado_por="Lucas",
            closed_at=None,
            mission_path="/tmp/missions/MIS-20260518-002",
        )
        d = c.to_dict()
        c2 = MissionContract.from_dict(d)
        assert c2.mission_id == c.mission_id
        assert c2.objetivo == c.objetivo
        assert c2.setor == c.setor
        assert c2.criado_por == c.criado_por
        assert c2.mission_path == c.mission_path

    def test_from_dict_ignores_extra_keys(self):
        d = {
            "mission_id": "MIS-1",
            "timestamp": "t",
            "status": "open",
            "setor": "s",
            "objetivo": "o",
            "criado_por": "c",
            "extra_field": "should be ignored",
        }
        c = MissionContract.from_dict(d)
        assert c.mission_id == "MIS-1"
        assert not hasattr(c, "extra_field")


class TestMissionEngine:
    def test_generate_id_format(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        mid = engine._generate_id()
        today = _today_str()
        assert mid.startswith(f"MIS-{today}-")
        assert mid.endswith("001")
        assert len(mid) == len(f"MIS-{today}-001")

    def test_generate_id_increments(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        mid1 = engine._generate_id()
        (tmp_path / mid1).mkdir()
        mid2 = engine._generate_id()
        assert mid1 != mid2
        assert mid2.endswith("002")

    def test_open_mission_creates_structure(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        contract = engine.open_mission("testar estrutura", setor="tech")

        mission_dir = tmp_path / contract.mission_id
        assert mission_dir.exists()
        for subdir in MISSION_SUBDIRS:
            assert (mission_dir / subdir).is_dir()

    def test_open_mission_writes_contract(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        contract = engine.open_mission("criar carrossel hotel", setor="marketing")

        contract_path = tmp_path / contract.mission_id / "mission_contract.json"
        assert contract_path.exists()
        data = json.loads(contract_path.read_text(encoding="utf-8"))
        assert data["status"] == MISSION_STATUS_OPEN
        assert data["setor"] == "marketing"
        assert data["objetivo"] == "criar carrossel hotel"
        assert data["mission_id"] == contract.mission_id
        assert "timestamp" in data

    def test_open_mission_returns_contract(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        contract = engine.open_mission("objetivo X", setor="vendas", criado_por="Lucas")

        assert isinstance(contract, MissionContract)
        assert contract.status == MISSION_STATUS_OPEN
        assert contract.setor == "vendas"
        assert contract.objetivo == "objetivo X"
        assert contract.criado_por == "Lucas"
        assert contract.closed_at is None
        assert contract.mission_path is not None

    def test_close_mission_updates_status(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        contract = engine.open_mission("missão para fechar", setor="ops")
        mission_id = contract.mission_id

        closed = engine.close_mission(mission_id)
        assert closed is not None
        assert closed.status == MISSION_STATUS_CLOSED
        assert closed.closed_at is not None

        # Verify persistence
        reloaded = engine.get_mission(mission_id)
        assert reloaded is not None
        assert reloaded.status == MISSION_STATUS_CLOSED
        assert reloaded.closed_at is not None

    def test_close_mission_nonexistent_returns_none(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        result = engine.close_mission("MIS-99999999-999")
        assert result is None

    def test_get_mission_returns_contract(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        created = engine.open_mission("buscar depois", setor="finance")

        found = engine.get_mission(created.mission_id)
        assert found is not None
        assert found.mission_id == created.mission_id
        assert found.objetivo == "buscar depois"

    def test_get_mission_nonexistent_returns_none(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        result = engine.get_mission("MIS-00000000-000")
        assert result is None

    def test_multiple_missions_independent_folders(self, tmp_path):
        engine = MissionEngine(missions_root=tmp_path)
        c1 = engine.open_mission("missão 1")
        c2 = engine.open_mission("missão 2")

        assert c1.mission_id != c2.mission_id
        assert (tmp_path / c1.mission_id).exists()
        assert (tmp_path / c2.mission_id).exists()

    def test_custom_missions_root(self, tmp_path):
        custom = tmp_path / "custom_missions"
        engine = MissionEngine(missions_root=custom)
        contract = engine.open_mission("root customizado")
        assert custom.exists()
        assert (custom / contract.mission_id).exists()
