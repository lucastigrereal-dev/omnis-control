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


class TestAgentStatusEndpoint:
    def test_status_returns_200(self):
        r = client.get("/agent/status")
        assert r.status_code == 200

    def test_status_has_queue(self):
        data = client.get("/agent/status").json()
        assert "queue" in data
        for key in ("total", "pending", "caption_ready"):
            assert key in data["queue"]

    def test_status_has_runs(self):
        data = client.get("/agent/status").json()
        assert "runs" in data
        for key in ("total", "completed", "dry_run", "failed"):
            assert key in data["runs"]

    def test_status_has_schedules(self):
        data = client.get("/agent/status").json()
        assert "schedules" in data
        for key in ("total", "active", "due_now"):
            assert key in data["schedules"]

    def test_status_has_memory(self):
        data = client.get("/agent/status").json()
        assert "memory" in data
        assert "total_entries" in data["memory"]

    def test_status_has_litellm_available(self):
        data = client.get("/agent/status").json()
        assert "litellm_available" in data
        assert isinstance(data["litellm_available"], bool)

    def test_status_counts_are_non_negative(self):
        data = client.get("/agent/status").json()
        assert data["queue"]["total"] >= 0
        assert data["runs"]["total"] >= 0
        assert data["schedules"]["total"] >= 0
        assert data["memory"]["total_entries"] >= 0
