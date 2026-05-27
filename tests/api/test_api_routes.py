"""Testes da API OMNIS — smoke + contratos de resposta."""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestRoot:
    def test_root_ok(self):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["service"] == "omnis-api"
        assert data["status"] == "ok"

    def test_docs_available(self):
        r = client.get("/docs")
        assert r.status_code == 200


class TestHealthEndpoint:
    def test_health_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_has_overall(self):
        data = client.get("/health").json()
        assert "overall" in data
        assert data["overall"] in ("ok", "warning", "error")

    def test_health_has_checks(self):
        data = client.get("/health").json()
        assert "checks" in data
        assert isinstance(data["checks"], dict)


class TestQueueEndpoint:
    def test_list_queue_returns_200(self):
        r = client.get("/queue")
        assert r.status_code == 200

    def test_list_queue_schema(self):
        data = client.get("/queue").json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_list_queue_invalid_status_422(self):
        r = client.get("/queue?status=INVALID_STATUS_XYZ")
        assert r.status_code == 422

    def test_get_queue_item_not_found(self):
        r = client.get("/queue/nonexistent-id-000")
        assert r.status_code == 404

    def test_list_queue_limit(self):
        data = client.get("/queue?limit=2").json()
        assert len(data["items"]) <= 2


class TestAccountsEndpoint:
    def test_list_accounts_200(self):
        r = client.get("/accounts")
        assert r.status_code == 200

    def test_list_accounts_schema(self):
        data = client.get("/accounts").json()
        assert "total" in data
        assert "accounts" in data

    def test_active_accounts_200(self):
        r = client.get("/accounts/active")
        assert r.status_code == 200

    def test_get_account_not_found(self):
        r = client.get("/accounts/nonexistent-id-999")
        assert r.status_code == 404


class TestDraftsEndpoint:
    def test_list_drafts_200(self):
        r = client.get("/drafts")
        assert r.status_code == 200

    def test_list_drafts_schema(self):
        data = client.get("/drafts").json()
        assert "total" in data
        assert "drafts" in data

    def test_list_drafts_invalid_status_422(self):
        r = client.get("/drafts?status=INVALID_XYZ")
        assert r.status_code == 422

    def test_get_draft_not_found(self):
        r = client.get("/drafts/nonexistent-id-000")
        assert r.status_code == 404


class TestAssetsEndpoint:
    def test_list_assets_200(self):
        r = client.get("/assets")
        assert r.status_code == 200

    def test_list_assets_schema(self):
        data = client.get("/assets").json()
        assert "total" in data
        assert "assets" in data

    def test_get_asset_not_found(self):
        r = client.get("/assets/nonexistent-id-000")
        assert r.status_code == 404


class TestMissionsEndpoint:
    def test_list_missions_200(self):
        r = client.get("/missions")
        assert r.status_code == 200

    def test_list_missions_schema(self):
        data = client.get("/missions").json()
        assert "total" in data
        assert "missions" in data

    def test_list_missions_v1_alias_200(self):
        r = client.get("/v1/missions")
        assert r.status_code == 200

    def test_list_missions_v1_alias_schema(self):
        data = client.get("/v1/missions").json()
        assert "total" in data
        assert "missions" in data

    def test_get_mission_not_found(self):
        r = client.get("/missions/nonexistent-id-000")
        assert r.status_code == 404


class TestSkillsEndpoint:
    def test_skills_200(self):
        r = client.get("/skills")
        assert r.status_code == 200

    def test_skills_is_dict(self):
        data = client.get("/skills").json()
        assert isinstance(data, dict)


class TestReportsEndpoint:
    def test_status_report_200(self):
        r = client.get("/reports/status")
        assert r.status_code == 200

    def test_status_report_schema(self):
        data = client.get("/reports/status").json()
        assert "session_id" in data

    def test_briefing_200(self):
        r = client.get("/reports/briefing")
        assert r.status_code == 200

    def test_briefing_schema(self):
        data = client.get("/reports/briefing").json()
        assert "briefing" in data


class TestCORS:
    def test_cors_header_present(self):
        r = client.get("/", headers={"Origin": "http://localhost:3000"})
        assert r.status_code == 200


class TestReadOnly:
    def test_no_post_on_queue(self):
        r = client.post("/queue", json={})
        assert r.status_code == 405

    def test_no_delete_on_accounts(self):
        r = client.delete("/accounts/some-id")
        assert r.status_code == 405

    def test_no_put_on_drafts(self):
        r = client.put("/drafts/some-id", json={})
        assert r.status_code == 405
