"""W184 — Tests for MissionResultStore."""
import pytest
from src.first_missions.models import Mission, MissionStatus, MissionType
from src.first_missions.result_store import MissionResultStore, StoredResult


# ---------------------------------------------------------------------------
# StoredResult
# ---------------------------------------------------------------------------

def test_stored_result_to_dict():
    r = StoredResult(mission_id="mss_abc", mission_name="test", result={"x": 1})
    d = r.to_dict()
    assert d["result_id"].startswith("res_")
    assert d["mission_id"] == "mss_abc"
    assert d["mission_name"] == "test"
    assert d["result"] == {"x": 1}
    assert "stored_at" in d


def test_stored_result_from_dict_round_trip():
    r = StoredResult(mission_id="mss_x", mission_name="rt", status="COMPLETED")
    d = r.to_dict()
    r2 = StoredResult.from_dict(d)
    assert r2.mission_id == r.mission_id
    assert r2.mission_name == r.mission_name
    assert r2.status == r.status


def test_stored_result_from_dict_defaults():
    r = StoredResult.from_dict({})
    assert r.result_id.startswith("res_")
    assert r.status == "COMPLETED"


def test_stored_result_from_mission():
    m = Mission(name="test_msn", mission_type=MissionType.CONTENT_GENERATION)
    m.status = MissionStatus.COMPLETED
    m.result = {"caption": "hi"}
    r = StoredResult.from_mission(m, duration_ms=42.0)
    assert r.mission_id == m.mission_id
    assert r.mission_name == "test_msn"
    assert r.result == {"caption": "hi"}
    assert r.status == "COMPLETED"
    assert r.duration_ms == 42.0
    assert r.dry_run is True


# ---------------------------------------------------------------------------
# MissionResultStore — in-memory
# ---------------------------------------------------------------------------

def test_store_save_and_get():
    store = MissionResultStore(dry_run=True)
    r = store.save(StoredResult(mission_id="mss_1"))
    assert store.get(r.result_id) is r


def test_store_get_missing():
    store = MissionResultStore(dry_run=True)
    assert store.get("nonexistent") is None


def test_store_save_mission():
    store = MissionResultStore(dry_run=True)
    m = Mission(name="m1")
    r = store.save_mission(m, duration_ms=10.0)
    assert r.mission_id == m.mission_id
    assert r.mission_name == "m1"
    assert r.duration_ms == 10.0


def test_store_by_mission():
    store = MissionResultStore(dry_run=True)
    m = Mission(name="target")
    store.save_mission(m)
    store.save(StoredResult(mission_id="other"))
    results = store.by_mission(m.mission_id)
    assert len(results) == 1
    assert results[0].mission_name == "target"


def test_store_query_by_status():
    store = MissionResultStore(dry_run=True)
    store.save(StoredResult(mission_id="a", status="COMPLETED"))
    store.save(StoredResult(mission_id="b", status="FAILED"))
    results = store.query(status="FAILED")
    assert len(results) == 1
    assert results[0].mission_id == "b"


def test_store_query_by_mission_type():
    store = MissionResultStore(dry_run=True)
    store.save(StoredResult(mission_id="a", mission_type="CONTENT_GENERATION"))
    store.save(StoredResult(mission_id="b", mission_type="METRIC_REPORT"))
    results = store.query(mission_type="METRIC_REPORT")
    assert len(results) == 1
    assert results[0].mission_id == "b"


def test_store_query_by_dry_run():
    store = MissionResultStore(dry_run=True)
    store.save(StoredResult(mission_id="a", dry_run=True))
    store.save(StoredResult(mission_id="b", dry_run=False))
    assert len(store.query(dry_run=True)) == 1
    assert len(store.query(dry_run=False)) == 1


def test_store_query_limit():
    store = MissionResultStore(dry_run=True)
    for i in range(5):
        store.save(StoredResult(mission_id=f"mss_{i}"))
    assert len(store.query(limit=2)) == 2


def test_store_successful_helper():
    store = MissionResultStore(dry_run=True)
    store.save(StoredResult(mission_id="a", status="COMPLETED"))
    store.save(StoredResult(mission_id="b", status="FAILED"))
    assert len(store.successful()) == 1


def test_store_failed_helper():
    store = MissionResultStore(dry_run=True)
    store.save(StoredResult(mission_id="a", status="COMPLETED"))
    store.save(StoredResult(mission_id="b", status="FAILED"))
    assert len(store.failed()) == 1


def test_store_stats():
    store = MissionResultStore(dry_run=True)
    store.save(StoredResult(mission_id="a", status="COMPLETED", mission_type="CUSTOM"))
    store.save(StoredResult(mission_id="b", status="FAILED", mission_type="CUSTOM"))
    s = store.stats()
    assert s["total"] == 2
    assert s["by_status"]["COMPLETED"] == 1
    assert s["by_status"]["FAILED"] == 1
    assert s["by_type"]["CUSTOM"] == 2


# ---------------------------------------------------------------------------
# JSONL persistence
# ---------------------------------------------------------------------------

def test_jsonl_save_and_load(tmp_path):
    path = tmp_path / "results.jsonl"
    store = MissionResultStore(path=path, dry_run=False)
    m = Mission(name="persisted")
    store.save_mission(m, duration_ms=5.0)

    # Reload from file
    store2 = MissionResultStore(path=path, dry_run=False)
    assert store2.stats()["total"] == 1
    loaded = store2.by_mission(m.mission_id)
    assert len(loaded) == 1
    assert loaded[0].mission_name == "persisted"
    assert loaded[0].duration_ms == 5.0


def test_jsonl_dry_run_does_not_write(tmp_path):
    path = tmp_path / "dry.jsonl"
    store = MissionResultStore(path=path, dry_run=True)
    store.save_mission(Mission(name="dry"))
    # Should not have written anything
    store2 = MissionResultStore(path=path, dry_run=False)
    assert store2.stats()["total"] == 0
