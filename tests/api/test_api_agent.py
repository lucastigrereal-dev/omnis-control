"""Testes da API OMNIS — /agent/* endpoints."""
import json
import os

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


class TestAgentRunsEndpoint:
    def test_list_runs_returns_200(self):
        r = client.get("/agent/runs")
        assert r.status_code == 200

    def test_list_runs_has_shape(self):
        data = client.get("/agent/runs").json()
        assert "total" in data
        assert "runs" in data
        assert isinstance(data["runs"], list)

    def test_list_runs_limit_param(self):
        r = client.get("/agent/runs?limit=5")
        assert r.status_code == 200
        data = r.json()
        assert len(data["runs"]) <= 5

    def test_list_runs_account_filter(self):
        r = client.get("/agent/runs?account=@contaquejamaisteve")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0

    def test_list_runs_status_filter(self):
        r = client.get("/agent/runs?status=completed")
        assert r.status_code == 200

    def test_get_run_missing_404(self):
        r = client.get("/agent/runs/nonexistent-run-id")
        assert r.status_code == 404


class TestAgentSchedulesEndpoint:
    def test_list_schedules_returns_200(self):
        r = client.get("/agent/schedules")
        assert r.status_code == 200

    def test_list_schedules_has_shape(self):
        data = client.get("/agent/schedules").json()
        assert "total" in data
        assert "schedules" in data
        assert isinstance(data["schedules"], list)

    def test_list_schedules_enabled_only(self):
        r = client.get("/agent/schedules?enabled_only=true")
        assert r.status_code == 200

    def test_schedule_history_empty(self):
        r = client.get("/agent/schedules/nonexistent/history")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert data["runs"] == []

    def test_schedule_history_has_shape(self):
        data = client.get("/agent/schedules/nonexistent/history").json()
        assert "schedule_id" in data
        assert "total" in data
        assert "runs" in data


class TestAgentMemoryEndpoint:
    def test_memory_stats_returns_200(self):
        r = client.get("/agent/memory")
        assert r.status_code == 200

    def test_memory_stats_has_shape(self):
        data = client.get("/agent/memory").json()
        assert "total_entries" in data
        assert "account_filter" in data

    def test_memory_stats_account_filter(self):
        r = client.get("/agent/memory?account=@contaquejamaisteve")
        assert r.status_code == 200
        data = r.json()
        assert data["account_filter"] == "@contaquejamaisteve"
        assert data["total_entries"] == 0
