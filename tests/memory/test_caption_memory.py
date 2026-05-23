"""Testes para CaptionMemoryWriter + CaptionMemoryReader."""
from src.memory.caption_memory import CaptionMemoryEntry, CaptionMemoryWriter, CaptionMemoryReader


# ── CaptionMemoryEntry ────────────────────────────────────────────────────────

def test_entry_to_dict():
    e = CaptionMemoryEntry(
        entry_id="abc", account_handle="@oinatalrn", objective="alcance",
        format="feed", caption_text="texto", run_id="r1", draft_id="d1",
    )
    d = e.to_dict()
    assert d["account_handle"] == "@oinatalrn"
    assert d["caption_text"] == "texto"


def test_entry_roundtrip():
    e = CaptionMemoryEntry(
        entry_id="abc", account_handle="@x", objective="alcance",
        format="feed", caption_text="texto", run_id="r1", draft_id="d1",
    )
    restored = CaptionMemoryEntry.from_dict(e.to_dict())
    assert restored.entry_id == "abc"
    assert restored.caption_text == "texto"


# ── CaptionMemoryWriter ───────────────────────────────────────────────────────

def test_writer_creates_entry(tmp_path):
    writer = CaptionMemoryWriter(path=str(tmp_path / "mem.jsonl"))
    entry = writer.write(
        account_handle="@oinatalrn",
        objective="alcance",
        format="feed",
        caption_text="Você precisa conhecer esse lugar",
        run_id="r1",
        draft_id="d1",
    )
    assert entry.entry_id is not None
    assert entry.account_handle == "@oinatalrn"


def test_writer_persists_to_file(tmp_path):
    path = str(tmp_path / "mem.jsonl")
    writer = CaptionMemoryWriter(path=path)
    writer.write("@x", "alcance", "feed", "texto", "r1", "d1")
    import os
    assert os.path.exists(path)
    with open(path) as f:
        lines = [l for l in f if l.strip()]
    assert len(lines) == 1


def test_writer_appends_multiple(tmp_path):
    path = str(tmp_path / "mem.jsonl")
    writer = CaptionMemoryWriter(path=path)
    for i in range(3):
        writer.write(f"@acc{i}", "alcance", "feed", f"texto {i}", f"r{i}", f"d{i}")
    with open(path) as f:
        lines = [l for l in f if l.strip()]
    assert len(lines) == 3


# ── CaptionMemoryReader ───────────────────────────────────────────────────────

def test_reader_empty_file(tmp_path):
    reader = CaptionMemoryReader(path=str(tmp_path / "nonexistent.jsonl"))
    assert reader.find_similar("@x", "alcance") == []


def test_reader_finds_by_account_and_objective(tmp_path):
    path = str(tmp_path / "mem.jsonl")
    writer = CaptionMemoryWriter(path=path)
    writer.write("@oinatalrn", "alcance", "feed", "Legenda A", "r1", "d1")
    writer.write("@oinatalrn", "conversao", "feed", "Legenda B", "r2", "d2")
    writer.write("@outro", "alcance", "feed", "Legenda C", "r3", "d3")

    reader = CaptionMemoryReader(path=path)
    results = reader.find_similar("@oinatalrn", "alcance")
    assert results == ["Legenda A"]


def test_reader_top_k_limit(tmp_path):
    path = str(tmp_path / "mem.jsonl")
    writer = CaptionMemoryWriter(path=path)
    for i in range(5):
        writer.write("@x", "alcance", "feed", f"Legenda {i}", f"r{i}", f"d{i}")
    reader = CaptionMemoryReader(path=path)
    results = reader.find_similar("@x", "alcance", top_k=3)
    assert len(results) == 3


def test_reader_most_recent_first(tmp_path):
    import json
    path = str(tmp_path / "mem.jsonl")
    old = CaptionMemoryEntry(
        entry_id="e1", account_handle="@x", objective="alcance",
        format="feed", caption_text="Antiga", run_id="r1", draft_id="d1",
        approved_at="2026-01-01T10:00:00Z",
    )
    new = CaptionMemoryEntry(
        entry_id="e2", account_handle="@x", objective="alcance",
        format="feed", caption_text="Nova", run_id="r2", draft_id="d2",
        approved_at="2026-06-01T10:00:00Z",
    )
    with open(path, "w") as f:
        f.write(json.dumps(old.to_dict()) + "\n")
        f.write(json.dumps(new.to_dict()) + "\n")
    reader = CaptionMemoryReader(path=path)
    results = reader.find_similar("@x", "alcance", top_k=1)
    assert results == ["Nova"]


def test_reader_count_all(tmp_path):
    path = str(tmp_path / "mem.jsonl")
    writer = CaptionMemoryWriter(path=path)
    writer.write("@a", "alcance", "feed", "T1", "r1", "d1")
    writer.write("@b", "alcance", "feed", "T2", "r2", "d2")
    reader = CaptionMemoryReader(path=path)
    assert reader.count() == 2


def test_reader_count_by_account(tmp_path):
    path = str(tmp_path / "mem.jsonl")
    writer = CaptionMemoryWriter(path=path)
    writer.write("@a", "alcance", "feed", "T1", "r1", "d1")
    writer.write("@a", "conversao", "reels", "T2", "r2", "d2")
    writer.write("@b", "alcance", "feed", "T3", "r3", "d3")
    reader = CaptionMemoryReader(path=path)
    assert reader.count("@a") == 2
    assert reader.count("@b") == 1
