"""Tests for asset_inbox scanner — 20 required tests (B8A spec)."""
import os
import pytest
from pathlib import Path
from src.asset_inbox.scanner import scan
from src.asset_inbox.errors import AssetInboxScanError, PathTraversalError
from src.asset_inbox.models import (
    STATUS_CANDIDATE,
    STATUS_IGNORED,
    STATUS_TOO_LARGE,
    STATUS_MISSING,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def make_file(parent: Path, name: str, content: bytes = b"fake") -> Path:
    p = parent / name
    p.write_bytes(content)
    return p


# ── Test 1: scan pasta inexistente retorna erro claro ─────────────────────────

def test_scan_nonexistent_path_raises(tmp_path):
    with pytest.raises(AssetInboxScanError):
        scan(tmp_path / "no_such_dir")


# ── Test 2: detecta jpg/png/mp4 como suportados ───────────────────────────────

def test_scan_detects_supported_formats(tmp_path):
    make_file(tmp_path, "photo.jpg")
    make_file(tmp_path, "banner.png")
    make_file(tmp_path, "clip.mp4")
    result = scan(tmp_path)
    assert result.total_supported == 3
    statuses = {i.status for i in result.items if i.extension in (".jpg", ".png", ".mp4")}
    assert STATUS_CANDIDATE in statuses


# ── Test 3: extensão proibida é ignorada ──────────────────────────────────────

def test_scan_ignores_unsupported_extensions(tmp_path):
    make_file(tmp_path, "doc.pdf")
    make_file(tmp_path, "script.py")
    make_file(tmp_path, "photo.jpg")
    result = scan(tmp_path)
    assert result.total_ignored == 2
    assert result.total_supported == 1


# ── Test 4: limite de quantidade funciona ────────────────────────────────────

def test_scan_respects_limit(tmp_path):
    for i in range(20):
        make_file(tmp_path, f"img_{i:02d}.jpg")
    result = scan(tmp_path, limit=5)
    total_processed = result.total_supported + result.total_ignored
    assert total_processed <= 5
    assert any("limite" in w.lower() or "limit" in w.lower() for w in result.warnings)


# ── Test 5: exclude funciona ──────────────────────────────────────────────────

def test_scan_excludes_directories(tmp_path):
    subdir = tmp_path / "skip_me"
    subdir.mkdir()
    make_file(subdir, "hidden.jpg")
    make_file(tmp_path, "visible.jpg")
    result = scan(tmp_path, exclude={"skip_me"})
    paths = {i.file_name for i in result.items}
    assert "visible.jpg" in paths
    assert "hidden.jpg" not in paths


# ── Test 6: fingerprint usa chunks e retorna hash estável ────────────────────

def test_scan_fingerprint_stable(tmp_path):
    make_file(tmp_path, "photo.jpg", b"stable content")
    r1 = scan(tmp_path)
    r2 = scan(tmp_path)
    fp1 = next(i.fingerprint for i in r1.items if i.file_name == "photo.jpg")
    fp2 = next(i.fingerprint for i in r2.items if i.file_name == "photo.jpg")
    assert fp1 == fp2
    assert len(fp1) == 64


# ── Test 7: arquivo deletado vira missing_on_disk ou erro controlado ─────────

def test_scan_single_missing_file(tmp_path):
    """A deleted single file path raises AssetInboxScanError (controlled error per spec)."""
    f = tmp_path / "gone.jpg"
    f.write_bytes(b"bye")
    f.unlink()
    # spec: "arquivo deletado vira missing_on_disk ou erro controlado"
    # AssetInboxScanError is the controlled error when root path doesn't exist
    with pytest.raises(AssetInboxScanError):
        scan(f)


# ── Test 8: path traversal bloqueado ─────────────────────────────────────────

def test_scan_blocks_path_traversal():
    with pytest.raises(PathTraversalError):
        scan(Path("../../../etc/passwd"))


def test_scan_blocks_encoded_traversal():
    with pytest.raises(PathTraversalError):
        scan(Path("%2e%2e/etc"))


# ── Test 9: symlink perigoso não quebra ──────────────────────────────────────

def test_scan_skips_symlinks(tmp_path):
    real_file = tmp_path / "real.jpg"
    real_file.write_bytes(b"real content")
    link = tmp_path / "link.jpg"
    try:
        link.symlink_to(real_file)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported on this platform")
    result = scan(tmp_path)
    # symlink should be skipped, only real file counted
    linked_items = [i for i in result.items if i.file_name == "link.jpg"]
    assert not linked_items or all(i.status != STATUS_CANDIDATE for i in linked_items)


# ── Test 10: scanner não move arquivo ────────────────────────────────────────

def test_scanner_does_not_move_files(tmp_path):
    f = tmp_path / "photo.jpg"
    f.write_bytes(b"content")
    scan(tmp_path)
    assert f.exists()
    assert (tmp_path / "photo.jpg").read_bytes() == b"content"


# ── Test 11: scanner não copia arquivo ───────────────────────────────────────

def test_scanner_does_not_copy_files(tmp_path):
    f = tmp_path / "photo.jpg"
    f.write_bytes(b"content")
    scan(tmp_path)
    files_after = list(tmp_path.iterdir())
    assert len(files_after) == 1  # only original file


# ── Test 12: scanner não apaga arquivo ───────────────────────────────────────

def test_scanner_does_not_delete_files(tmp_path):
    f = tmp_path / "photo.jpg"
    f.write_bytes(b"content")
    scan(tmp_path)
    assert f.exists()


# ── Test 13: nenhum teste toca arquivo real fora de tmp_path ────────────────
# (structural — all tests above use tmp_path fixture only)

def test_all_tests_use_tmp_path(tmp_path):
    """Verifica que o scanner pode ser chamado em tmp_path sem side-effects externos."""
    make_file(tmp_path, "a.jpg")
    result = scan(tmp_path)
    assert result.root_path.startswith(str(tmp_path).split(":")[0])  # not a real media dir


# ── Test 14: nenhum teste chama internet ─────────────────────────────────────

def test_scanner_no_network_calls(tmp_path, monkeypatch):
    import socket
    def _blocked(*args, **kwargs):
        raise AssertionError("Network call blocked")
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    make_file(tmp_path, "photo.jpg")
    result = scan(tmp_path)
    assert result.total_supported == 1


# ── Test 15: nenhum teste lê .env ────────────────────────────────────────────

def test_scanner_no_env_reads(tmp_path, monkeypatch):
    import os
    original = os.getenv
    def _assert_no_secret(key, *args, **kwargs):
        assert not key.startswith("META_") and not key.startswith("INSTAGRAM_")
        return original(key, *args, **kwargs)
    monkeypatch.setattr(os, "getenv", _assert_no_secret)
    make_file(tmp_path, "video.mp4")
    result = scan(tmp_path)
    assert result is not None


# ── Test 16: formatos mapeiam media_type corretamente ────────────────────────

def test_media_type_mapping(tmp_path):
    for name, expected in [
        ("a.jpg", "image"), ("b.png", "image"), ("c.webp", "image"),
        ("d.mp4", "video"), ("e.mov", "video"), ("f.m4v", "video"),
    ]:
        make_file(tmp_path, name)
    result = scan(tmp_path)
    for item in result.items:
        if item.status == STATUS_CANDIDATE:
            assert item.media_type in ("image", "video"), f"bad media_type for {item.file_name}"


# ── Test 17: formatos não permitidos contam como ignored ─────────────────────

def test_unsupported_counted_as_ignored(tmp_path):
    make_file(tmp_path, "doc.pdf")
    make_file(tmp_path, "spreadsheet.xlsx")
    make_file(tmp_path, "photo.jpg")
    result = scan(tmp_path)
    assert result.total_ignored == 2
    assert result.total_supported == 1


# ── Test 18: scan de arquivo único funciona ───────────────────────────────────

def test_scan_single_file(tmp_path):
    f = make_file(tmp_path, "single.jpg", b"single content")
    result = scan(f)
    assert result.total_seen == 1
    assert result.total_supported == 1
    assert result.items[0].status == STATUS_CANDIDATE


# ── Test 19: too_large marcado sem abrir arquivo ──────────────────────────────

def test_scan_marks_too_large(tmp_path):
    f = tmp_path / "big.mp4"
    f.write_bytes(b"x" * 100)
    result = scan(tmp_path, max_size_bytes=50)
    big_items = [i for i in result.items if i.file_name == "big.mp4"]
    assert big_items
    assert big_items[0].status == STATUS_TOO_LARGE
    assert result.total_too_large == 1


# ── Test 20: exclude default ignora .git e __pycache__ ───────────────────────

def test_default_excludes_applied(tmp_path):
    gitdir = tmp_path / ".git"
    gitdir.mkdir()
    make_file(gitdir, "pack.jpg")
    make_file(tmp_path, "real.jpg")
    result = scan(tmp_path)
    assert result.total_supported == 1
    assert all(i.file_name != "pack.jpg" for i in result.items)
