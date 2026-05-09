"""Tests for metadata module — media type detection, file size via stat()."""
import pytest
from pathlib import Path
from src.asset_inbox.metadata import get_media_type, is_supported, get_file_size


def test_get_media_type_images():
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        assert get_media_type(ext) == "image", f"Expected image for {ext}"


def test_get_media_type_videos():
    for ext in (".mp4", ".mov", ".m4v"):
        assert get_media_type(ext) == "video", f"Expected video for {ext}"


def test_get_media_type_unknown():
    assert get_media_type(".pdf") == "unknown"
    assert get_media_type(".txt") == "unknown"
    assert get_media_type(".exe") == "unknown"
    assert get_media_type("") == "unknown"


def test_is_supported_true():
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".m4v"):
        assert is_supported(ext), f"Expected supported: {ext}"


def test_is_supported_false():
    for ext in (".pdf", ".doc", ".zip", ".py", ".sh"):
        assert not is_supported(ext), f"Expected unsupported: {ext}"


def test_get_file_size_existing(tmp_path):
    f = tmp_path / "img.jpg"
    f.write_bytes(b"x" * 1234)
    size, err = get_file_size(f)
    assert err == ""
    assert size == 1234


def test_get_file_size_missing(tmp_path):
    f = tmp_path / "ghost.jpg"
    size, err = get_file_size(f)
    assert size == 0
    assert err != ""


def test_get_file_size_never_raises(tmp_path):
    f = tmp_path / "missing.jpg"
    try:
        size, err = get_file_size(f)
    except Exception as exc:
        pytest.fail(f"get_file_size raised: {exc}")


def test_case_insensitive_extension():
    assert get_media_type(".JPG") == "image"
    assert get_media_type(".MP4") == "video"
    assert is_supported(".PNG")
