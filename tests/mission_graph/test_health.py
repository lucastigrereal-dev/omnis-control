"""Tests for MissionGraphHealthMonitor and MissionGraphHealthReport (D1-W10).

Cobre:
  - health sem runs → healthy=True, success_rate=0.0
  - health com runs reais → agrega métricas de state.json
  - to_dict() contém todos os campos obrigatórios
  - write_health_json() cria arquivo legível
  - summary() contém "mission_graph"
"""
from __future__ import annotations

import json

import pytest

from src.mission_graph.runner import run_mission_graph
from src.mission_graph.health import MissionGraphHealthMonitor, MissionGraphHealthReport


class TestMissionGraphHealth:
    def test_health_sem_runs(self, tmp_path):
        monitor = MissionGraphHealthMonitor(output_base=str(tmp_path / "output/mg"))
        report = monitor.collect()
        assert report.total_runs == 0
        assert report.healthy is True  # sem runs = healthy
        assert report.success_rate == 0.0

    def test_health_com_runs(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        run_mission_graph("h1", use_langgraph=True)
        run_mission_graph("h2", use_langgraph=True)
        monitor = MissionGraphHealthMonitor(output_base=str(tmp_path / "output/mission_graph"))
        report = monitor.collect()
        assert report.total_runs == 2
        assert report.total_cost_usd > 0.0
        assert report.total_tokens > 0

    def test_health_to_dict(self, tmp_path):
        monitor = MissionGraphHealthMonitor(output_base=str(tmp_path))
        report = monitor.collect()
        d = report.to_dict()
        assert d["component"] == "mission_graph"
        assert "healthy" in d
        assert "success_rate" in d

    def test_write_health_json(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        run_mission_graph("h_json", use_langgraph=True)
        monitor = MissionGraphHealthMonitor(output_base=str(tmp_path / "output/mission_graph"))
        path = monitor.write_health_json(output_path=tmp_path / "health.json")
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["component"] == "mission_graph"

    def test_summary_string(self, tmp_path):
        monitor = MissionGraphHealthMonitor(output_base=str(tmp_path))
        report = monitor.collect()
        s = report.summary()
        assert "mission_graph" in s
