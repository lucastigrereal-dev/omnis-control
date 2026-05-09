"""Tests for MissionReport model."""
import pytest
from src.mission_report.models import MissionReport


def test_new_creates_unique_ids():
    r1 = MissionReport.new("mb_abc", "carousel", "oinatalrn", "completed")
    r2 = MissionReport.new("mb_abc", "carousel", "oinatalrn", "completed")
    assert r1.report_id.startswith("mr_")
    assert r1.report_id != r2.report_id


def test_to_dict_roundtrip():
    r = MissionReport.new("mb_abc12345", "campaign", "lucastigrereal", "completed", notes="ok")
    d = r.to_dict()
    assert d["mission_id"] == "mb_abc12345"
    assert d["outcome"] == "completed"
    assert d["notes"] == "ok"
    assert "closed_at" in d


def test_from_dict():
    r = MissionReport.new("mb_xyz", "reels", "afamiliatigrereal", "cancelled", notes="sem tempo")
    restored = MissionReport.from_dict(r.to_dict())
    assert restored.report_id == r.report_id
    assert restored.outcome == "cancelled"
    assert restored.notes == "sem tempo"
