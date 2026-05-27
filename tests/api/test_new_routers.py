"""Testes dos novos routers W14: marketing, aurora, cost, events."""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


class TestMarketingEndpoints:
    def test_marketing_sprint_endpoint(self):
        r = client.get("/marketing/sprint")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "sprint" in data

    def test_marketing_mission_post(self):
        r = client.post(
            "/marketing/missions",
            json={"goal": "criar carrossel Instagram", "squad": "instagram"},
        )
        assert r.status_code == 200
        data = r.json()
        # Deve retornar mission_id ou erro descritivo — nunca 500 silencioso
        assert "mission_id" in data or "error" in data

    def test_marketing_agents_list(self):
        r = client.get("/marketing/agents")
        assert r.status_code == 200
        data = r.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)


class TestAuroraEndpoints:
    def test_aurora_state_endpoint(self):
        r = client.get("/aurora/state")
        assert r.status_code == 200
        data = r.json()
        # Pode retornar no_state ou dados reais
        assert "status" in data or "aurora_fio_mental" in data

    def test_aurora_chat_endpoint(self):
        r = client.post("/aurora/chat", json={"message": "oi"})
        assert r.status_code == 200
        data = r.json()
        assert "response" in data
        assert "Aurora recebeu" in data["response"]

    def test_aurora_chat_empty_message(self):
        r = client.post("/aurora/chat", json={})
        assert r.status_code == 200
        data = r.json()
        assert "response" in data


class TestCostEndpoints:
    def test_cost_summary_endpoint(self):
        r = client.get("/cost/summary")
        assert r.status_code == 200
        data = r.json()
        # Pode retornar report ou erro gracioso
        assert "report_id" in data or "error" in data or "total_cost_brl" in data
