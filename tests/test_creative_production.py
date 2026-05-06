"""Tests for Creative Production OS module."""
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.creative_production.models import CreativeBrief, ProductionItem, CreativeReview
from src.creative_production.briefs import (
    create_brief, list_briefs, get_brief, update_brief_status, create_review
)
from src.creative_production.production_queue import (
    create_production_item, list_production_items, update_item_status,
    attach_asset, get_queue_stats
)
from src.creative_production.exporter import export_package, list_packages
from src.creative_production.review import approve_brief, reject_brief, is_ready_for_argos


def test_create_brief(empty_data):
    brief = create_brief(
        queue_id="q-001",
        account_handle="@lucastigrereal",
        format="carrossel",
        objective="engajar",
        visual_direction="colorido e moderno",
    )
    assert brief.creative_brief_id is not None
    assert brief.queue_id == "q-001"
    assert brief.account_handle == "@lucastigrereal"
    assert brief.status == "draft"
    assert "CAPTION_NOT_APPROVED" in brief.warnings


def test_create_brief_with_caption(empty_data):
    """Create a brief without caption approved warning."""
    brief = create_brief(
        queue_id="q-001",
        account_handle="@lucastigrereal",
        format="reel",
        objective="venda",
        visual_direction="clean",
    )
    assert "CAPTION_NOT_APPROVED" in brief.warnings


def test_list_briefs(empty_data):
    create_brief(queue_id="q-001", account_handle="@lucastigrereal",
                 format="carrossel", objective="engajar", visual_direction="moderno")
    create_brief(queue_id="q-002", account_handle="@afamiliatigrereal",
                 format="reel", objective="educar", visual_direction="clean")
    briefs = list_briefs()
    assert len(briefs) == 2


def test_get_brief(empty_data):
    brief = create_brief(queue_id="q-001", account_handle="@lucastigrereal",
                         format="carrossel", objective="engajar", visual_direction="moderno")
    found = get_brief(brief.creative_brief_id)
    assert found is not None
    assert found.queue_id == "q-001"


def test_update_brief_status(empty_data):
    brief = create_brief(queue_id="q-001", account_handle="@lucastigrereal",
                         format="carrossel", objective="engajar", visual_direction="moderno")
    result = update_brief_status(brief.creative_brief_id, "approved")
    assert result is True
    updated = get_brief(brief.creative_brief_id)
    assert updated.status == "approved"


def test_create_production_item(empty_data):
    item = create_production_item(
        queue_id="q-001",
        creative_brief_id="br-001",
        asset_type="video",
        tool_target="capcut"
    )
    assert item.production_id is not None
    assert item.asset_type == "video"
    assert item.tool_target == "capcut"
    assert item.status == "pending"


def test_list_production_items(empty_data):
    create_production_item(queue_id="q-001", creative_brief_id="br-001",
                           asset_type="video")
    create_production_item(queue_id="q-002", creative_brief_id="br-002",
                           asset_type="image")
    items = list_production_items()
    assert len(items) == 2


def test_attach_asset(empty_data):
    item = create_production_item(queue_id="q-001", creative_brief_id="br-001",
                                  asset_type="video")
    attach_asset(item.production_id, "/path/to/video.mp4", asset_id="ast-001")
    items = list_production_items()
    updated = [i for i in items if i.get("production_id") == item.production_id][0]
    assert updated["status"] == "done"
    assert updated["asset_path"] == "/path/to/video.mp4"
    assert updated["asset_id"] == "ast-001"


def test_get_queue_stats(empty_data):
    stats = get_queue_stats()
    assert stats["total"] == 0
    assert stats["pending"] == 0

    create_production_item(queue_id="q-001", creative_brief_id="br-001",
                           asset_type="video")
    stats = get_queue_stats()
    assert stats["total"] == 1
    assert stats["pending"] == 1


def test_export_package(empty_data):
    brief = create_brief(queue_id="q-001", account_handle="@lucastigrereal",
                         format="carrossel", objective="engajar",
                         visual_direction="moderno",
                         script="Check this out!", shot_list="1. Intro\n2. CTA")
    package_path = export_package(brief.creative_brief_id)
    assert package_path is not None
    assert package_path.exists()
    assert (package_path / "brief.md").exists()
    assert (package_path / "script.md").exists()
    assert (package_path / "shot_list.md").exists()
    assert (package_path / "production_checklist.md").exists()


def test_export_package_invalid_brief(empty_data):
    result = export_package("nonexistent")
    assert result is None


def test_review_approve(empty_data):
    brief = create_brief(queue_id="q-001", account_handle="@lucastigrereal",
                         format="carrossel", objective="engajar",
                         visual_direction="moderno")
    result = approve_brief(brief.creative_brief_id, notes="Looks good!")
    assert result is True
    updated = get_brief(brief.creative_brief_id)
    assert updated.status == "approved"


def test_review_reject(empty_data):
    brief = create_brief(queue_id="q-001", account_handle="@lucastigrereal",
                         format="carrossel", objective="engajar",
                         visual_direction="moderno")
    result = reject_brief(brief.creative_brief_id, notes="Fix design")
    assert result is True
    updated = get_brief(brief.creative_brief_id)
    assert updated.status == "rejected"


def test_approve_nonexistent_brief(empty_data):
    result = approve_brief("fake-id")
    assert result is False


def test_is_ready_for_argos_not_approved(empty_data):
    brief = create_brief(queue_id="q-001", account_handle="@lucastigrereal",
                         format="carrossel", objective="engajar",
                         visual_direction="moderno")
    ready, reason = is_ready_for_argos(brief.creative_brief_id)
    assert ready is False
    assert "CAPTION_NOT_APPROVED" in reason


def test_is_ready_for_argos_nonexistent(empty_data):
    ready, reason = is_ready_for_argos("fake-id")
    assert ready is False
    assert reason == "BRIEF_NOT_FOUND"


def test_list_packages_empty(empty_data):
    pkgs = list_packages()
    assert pkgs == []


def test_model_creative_brief_defaults():
    brief = CreativeBrief(
        creative_brief_id="test-1", queue_id="q-001",
        account_handle="@test", format="reel", objective="x",
        visual_direction="y"
    )
    assert brief.status == "draft"
    assert brief.created_at != ""


def test_model_production_item_defaults():
    item = ProductionItem(
        production_id="p-1", queue_id="q-001",
        creative_brief_id="br-001", asset_type="video",
        tool_target="canva"
    )
    assert item.status == "pending"


def test_no_external_calls(empty_data):
    """Verify the module doesn't call external APIs."""
    import src.creative_production.briefs as bmod
    import src.creative_production.production_queue as qmod

    for mod in [bmod, qmod]:
        source = Path(mod.__file__).read_text(encoding="utf-8")
        assert "requests." not in source, f"{mod.__name__} imports requests"
        assert "urllib" not in source, f"{mod.__name__} imports urllib"
        assert "httpx" not in source, f"{mod.__name__} imports httpx"
