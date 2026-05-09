"""Tests for fingerprint module — SHA256 chunked, never full load."""
import hashlib
import pytest
from pathlib import Path
from src.asset_inbox.fingerprint import compute_fingerprint, CHUNK_SIZE


def test_fingerprint_stable(tmp_path):
    f = tmp_path / "photo.jpg"
    f.write_bytes(b"fake image content" * 100)
    fp1, err1 = compute_fingerprint(f)
    fp2, err2 = compute_fingerprint(f)
    assert err1 == ""
    assert err2 == ""
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA256 hex


def test_fingerprint_correct_hash(tmp_path):
    data = b"hello world test content"
    f = tmp_path / "test.jpg"
    f.write_bytes(data)
    expected = hashlib.sha256(data).hexdigest()
    fp, err = compute_fingerprint(f)
    assert err == ""
    assert fp == expected


def test_fingerprint_missing_file(tmp_path):
    f = tmp_path / "nonexistent.jpg"
    fp, err = compute_fingerprint(f)
    assert fp == ""
    assert "not found" in err.lower() or err != ""


def test_fingerprint_different_content(tmp_path):
    f1 = tmp_path / "a.jpg"
    f2 = tmp_path / "b.jpg"
    f1.write_bytes(b"content A")
    f2.write_bytes(b"content B")
    fp1, _ = compute_fingerprint(f1)
    fp2, _ = compute_fingerprint(f2)
    assert fp1 != fp2


def test_fingerprint_large_file_chunked(tmp_path):
    # Write 3 chunks worth of data to verify chunk loop
    data = b"x" * (CHUNK_SIZE * 3 + 500)
    f = tmp_path / "big.mp4"
    f.write_bytes(data)
    expected = hashlib.sha256(data).hexdigest()
    fp, err = compute_fingerprint(f)
    assert err == ""
    assert fp == expected


def test_fingerprint_on_directory_returns_error(tmp_path):
    fp, err = compute_fingerprint(tmp_path)
    assert fp == ""
    assert err != ""


def test_fingerprint_never_raises(tmp_path):
    """compute_fingerprint must never raise — errors go into the error string."""
    nonexistent = tmp_path / "ghost.jpg"
    try:
        fp, err = compute_fingerprint(nonexistent)
    except Exception as exc:
        pytest.fail(f"compute_fingerprint raised: {exc}")
