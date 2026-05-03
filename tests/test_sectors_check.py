"""Testes do Sectors Checker — Fase Estruturação M1."""

from src.checkers import sectors_check


class TestSectorsCheck:
    def test_all_9_sectors_present(self):
        result = sectors_check.check()
        assert result["total"] == 9, f"Esperado 9 setores, got {result['total']}"

    def test_each_sector_has_valid_status(self):
        result = sectors_check.check()
        valid = {"operational", "partial", "blueprint"}
        for s in result["sectors"]:
            assert s["status"] in valid, f"{s['id']}: status '{s['status']}' invalido"

    def test_each_sector_has_id_and_objective(self):
        result = sectors_check.check()
        for s in result["sectors"]:
            assert s["id"], "Setor sem ID"
            assert s["objective"], f"{s['id']} sem objective"

    def test_operational_count(self):
        result = sectors_check.check()
        op = [s for s in result["sectors"] if s["status"] == "operational"]
        assert len(op) >= 3  # marketing_enterprise, memory_knowledge, security_audit, mission_control

    def test_partial_sectors_have_skills(self):
        result = sectors_check.check()
        for s in result["sectors"]:
            if s["status"] == "partial":
                assert s.get("available_skills"), f"{s['id']} partial sem available_skills"
                assert s.get("next_action"), f"{s['id']} partial sem next_action"

    def test_by_status_grouping(self):
        grouped = sectors_check.by_status()
        assert "operational" in grouped
        assert "partial" in grouped
        assert all(isinstance(v, list) for v in grouped.values())

    def test_get_sector_found(self):
        s = sectors_check.get_sector("marketing_enterprise")
        assert s is not None
        assert s["id"] == "marketing_enterprise"
        assert s["status"] == "operational"

    def test_get_sector_not_found(self):
        s = sectors_check.get_sector("fake_sector")
        assert s is None
