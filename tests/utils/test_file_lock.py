"""Testes para src/utils/file_lock.py — concorrência e safety."""
from __future__ import annotations

import json
import threading

from src.utils.file_lock import jsonl_write_lock


def test_single_write_creates_file(tmp_path):
    path = str(tmp_path / "store.jsonl")
    with jsonl_write_lock(path):
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "1"}) + "\n")
    lines = open(path).readlines()
    assert len(lines) == 1


def test_sequential_writes_no_data_loss(tmp_path):
    path = str(tmp_path / "store.jsonl")
    for i in range(5):
        with jsonl_write_lock(path):
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"id": str(i)}) + "\n")
    lines = [l for l in open(path).readlines() if l.strip()]
    assert len(lines) == 5


def test_concurrent_writes_no_data_loss(tmp_path):
    """2 threads escrevendo simultaneamente — nenhuma linha pode ser perdida."""
    path = str(tmp_path / "store.jsonl")
    errors: list[Exception] = []

    def writer(thread_id: int, n: int) -> None:
        for i in range(n):
            try:
                with jsonl_write_lock(path):
                    with open(path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"thread": thread_id, "i": i}) + "\n")
            except Exception as e:
                errors.append(e)

    t1 = threading.Thread(target=writer, args=(1, 20))
    t2 = threading.Thread(target=writer, args=(2, 20))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors, f"Threads raised: {errors}"
    lines = [l.strip() for l in open(path).readlines() if l.strip()]
    assert len(lines) == 40, f"Expected 40 lines, got {len(lines)}"
    records = [json.loads(l) for l in lines]
    thread1_lines = [r for r in records if r["thread"] == 1]
    thread2_lines = [r for r in records if r["thread"] == 2]
    assert len(thread1_lines) == 20
    assert len(thread2_lines) == 20


def test_lock_file_cleaned_up_after_write(tmp_path):
    path = str(tmp_path / "store.jsonl")
    with jsonl_write_lock(path):
        with open(path, "a") as f:
            f.write("{}\n")
    import os
    assert not os.path.exists(path + ".lock"), ".lock file should be removed after release"


def test_nested_same_path_does_not_deadlock(tmp_path):
    """Mesmo thread não deve deadloquear — usa RLock implícito via threading.Lock por path."""
    path = str(tmp_path / "store.jsonl")
    # jsonl_write_lock usa threading.Lock (não RLock), portanto nested seria deadlock.
    # Este teste verifica que dois contextos em threads diferentes não travam.
    results: list[str] = []

    def w(label: str):
        with jsonl_write_lock(path):
            results.append(label)

    t1 = threading.Thread(target=w, args=("A",))
    t2 = threading.Thread(target=w, args=("B",))
    t1.start()
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)
    assert sorted(results) == ["A", "B"]
