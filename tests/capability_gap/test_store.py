"""Tests for gap store."""
import pytest
from pathlib import Path
from src.capability_gap.models import CapabilityGap
from src.capability_gap.store import GapStore


def make_gap(suffix: str = "001") -> CapabilityGap:
    return CapabilityGap.new(f"request {suffix}", "marketing", "some_cap", "some_output")


def test_store_save_and_list(tmp_path):
    store = GapStore(tmp_path / "gaps.jsonl")
    gap = make_gap()
    store.save(gap)
    gaps = store.list_all()
    assert len(gaps) == 1
    assert gaps[0].gap_id == gap.gap_id


def test_store_list_empty(tmp_path):
    store = GapStore(tmp_path / "empty.jsonl")
    assert store.list_all() == []


def test_store_get_found(tmp_path):
    store = GapStore(tmp_path / "gaps.jsonl")
    gap = make_gap()
    store.save(gap)
    found = store.get(gap.gap_id)
    assert found is not None
    assert found.gap_id == gap.gap_id


def test_store_get_not_found(tmp_path):
    store = GapStore(tmp_path / "gaps.jsonl")
    assert store.get("gap_nonexistent") is None


def test_store_newest_first(tmp_path):
    store = GapStore(tmp_path / "gaps.jsonl")
    g1 = make_gap("001")
    g2 = make_gap("002")
    store.save(g1)
    store.save(g2)
    gaps = store.list_all()
    assert gaps[0].gap_id == g2.gap_id
