"""Testes de MissionContext e MissionPackage models."""
from __future__ import annotations

import json
from pathlib import Path

from src.mission.models import MissionContext, MissionPackage


class TestMissionContext:
    def test_creation_defaults(self):
        ctx = MissionContext(mission_id="mb_test123")
        assert ctx.mission_id == "mb_test123"
        assert ctx.contract == {}
        assert ctx.plan == {}
        assert ctx.squad is None
        assert ctx.created_at != ""

    def test_creation_with_data(self):
        ctx = MissionContext(
            mission_id="mb_abc",
            contract={"title": "Test"},
            plan={"intent": "carousel"},
            squad={"role": "designer"},
        )
        assert ctx.contract["title"] == "Test"
        assert ctx.plan["intent"] == "carousel"
        assert ctx.squad["role"] == "designer"


class TestMissionPackage:
    def test_creation_defaults(self):
        pkg = MissionPackage(mission_id="mb_test123")
        assert pkg.mission_id == "mb_test123"
        assert pkg.work_orders == []
        assert pkg.output_packages == []
        assert pkg.approval_requests == []
        assert pkg.status == "draft"
        assert pkg.closeout is None

    def test_to_dict_required_fields(self):
        pkg = MissionPackage(mission_id="mb_test")
        d = pkg.to_dict()
        required = [
            "mission_id", "context", "work_orders", "output_packages",
            "approval_requests", "logs", "manifest_registry_entries",
            "closeout", "status", "created_at", "updated_at",
        ]
        for key in required:
            assert key in d, f"Missing required field: {key}"

    def test_to_json_and_from_json_roundtrip(self, tmp_path: Path):
        pkg = MissionPackage(
            mission_id="mb_test_rb",
            context=MissionContext(
                mission_id="mb_test_rb",
                plan={"intent": "reels", "account_handle": "@test"},
            ),
            work_orders=[{"work_order_id": "wo_abc", "step_label": "step1"}],
            output_packages=[{"work_order_id": "wo_abc", "valid": True}],
            approval_requests=[{"work_order_id": "wo_abc", "dry_run": True}],
            logs=[{"level": "INFO", "message": "test"}],
            closeout={"total_wo": 1, "status": "done"},
            status="done",
        )
        path = tmp_path / "mission_package.json"
        pkg.to_json(path)

        loaded = MissionPackage.from_json(path)
        assert loaded.mission_id == pkg.mission_id
        assert loaded.status == "done"
        assert loaded.closeout["total_wo"] == 1
        assert len(loaded.work_orders) == 1
        assert loaded.context.plan["intent"] == "reels"

    def test_from_dict_restores_context(self):
        data = {
            "mission_id": "mb_ctx_test",
            "context": {
                "mission_id": "mb_ctx_test",
                "contract": {"title": "CTR"},
                "plan": {"intent": "carousel"},
                "squad": None,
                "created_at": "2026-05-12T00:00:00Z",
            },
            "work_orders": [],
            "output_packages": [],
            "approval_requests": [],
            "logs": [],
            "manifest_registry_entries": [],
            "closeout": None,
            "status": "draft",
            "created_at": "2026-05-12T00:00:00Z",
            "updated_at": "2026-05-12T00:00:00Z",
        }
        pkg = MissionPackage.from_dict(data)
        assert pkg.context.contract["title"] == "CTR"
        assert pkg.context.plan["intent"] == "carousel"

    def test_status_transitions(self):
        pkg = MissionPackage(mission_id="mb_s")
        assert pkg.status == "draft"
        pkg.status = "generating"
        assert pkg.status == "generating"
        pkg.status = "done"
        assert pkg.status == "done"
