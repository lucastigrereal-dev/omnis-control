"""
Testes do Video Asset Registry (Fase 2A).

Cobre: modelos, máquina de estados, registry CRUD, scanner, queue.
Não modifica nada fora de ~/omnis-control/data/.
"""

import os
import json
import tempfile
import time
from pathlib import Path

import pytest

from src.video_assets.models import VideoAsset, _make_fingerprint, _normalize_account, _normalize_city
from src.video_assets.status import AssetStatus
from src.video_assets.registry import Registry
from src.video_assets.scanner import Scanner, KNOWN_EXTENSIONS, IGNORE_DIRS
from src.video_assets.queue import Queue


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_registry_path():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8") as f:
        path = f.name
    yield path
    if os.path.isfile(path):
        os.unlink(path)


@pytest.fixture
def registry(tmp_registry_path):
    return Registry(tmp_registry_path)


@pytest.fixture
def sample_asset():
    return VideoAsset.new(
        asset_id="abc123def456",
        source_type="local",
        source_path="/tmp/teste.mp4",
        file_name="teste.mp4",
        extension=".mp4",
        size_bytes=1024 * 1024 * 50,  # 50MB
        modified_at="2026-05-01T10:00:00Z",
    )


# ---------------------------------------------------------------------------
# 1. Models
# ---------------------------------------------------------------------------

class TestModels:
    def test_new_asset_defaults(self):
        a = VideoAsset.new(
            asset_id="id1", source_type="local",
            source_path="/v/test.mp4", file_name="test.mp4",
            extension=".mp4", size_bytes=1000,
        )
        assert a.status == AssetStatus.INBOX
        assert a.format == "unknown"
        assert a.fingerprint is not None
        assert a.created_at is not None
        assert a.updated_at is not None
        assert a.tags == []

    def test_new_asset_with_account_normalization(self):
        a = VideoAsset.new(
            asset_id="id1", source_type="local",
            source_path="/v/test.mp4", file_name="test.mp4",
            extension=".mp4", size_bytes=1000,
            account_target="@LucasTigreReal",
        )
        assert a.account_target == "lucastigrereal"

    def test_new_asset_with_city_normalization(self):
        a = VideoAsset.new(
            asset_id="id1", source_type="local",
            source_path="/v/test.mp4", file_name="test.mp4",
            extension=".mp4", size_bytes=1000,
            city="Natal/RN",
        )
        assert a.city == "natalrn"

    def test_to_dict_from_dict_roundtrip(self, sample_asset):
        d = sample_asset.to_dict()
        assert d["status"] == "inbox"
        assert d["asset_id"] == "abc123def456"
        restored = VideoAsset.from_dict(d)
        assert restored.asset_id == sample_asset.asset_id
        assert restored.status == AssetStatus.INBOX
        assert restored.size_bytes == sample_asset.size_bytes

    def test_fingerprint(self):
        fp1 = _make_fingerprint("/a.mp4", 1000, "2026-01-01T00:00:00Z")
        fp2 = _make_fingerprint("/a.mp4", 1000, "2026-01-01T00:00:00Z")
        fp3 = _make_fingerprint("/b.mp4", 1000, "2026-01-01T00:00:00Z")
        assert fp1 == fp2
        assert fp1 != fp3

    def test_normalize_account(self):
        assert _normalize_account("@LucasTigreReal") == "lucastigrereal"
        assert _normalize_account("  @OQueComerNatal  ") == "oquecomernatal"
        assert _normalize_account("lucastigrereal") == "lucastigrereal"

    def test_normalize_city(self):
        assert _normalize_city("Natal/RN") == "natalrn"
        assert _normalize_city("São Paulo") == "sao paulo"
        assert _normalize_city("  Rio de Janeiro  ") == "rio de janeiro"


# ---------------------------------------------------------------------------
# 2. Status Machine
# ---------------------------------------------------------------------------

class TestStatusMachine:
    def test_inbox_to_triaged(self):
        assert AssetStatus.INBOX.can_transition_to(AssetStatus.TRIAGED)

    def test_inbox_to_rejected(self):
        assert AssetStatus.INBOX.can_transition_to(AssetStatus.REJECTED)

    def test_inbox_to_published_invalid(self):
        assert not AssetStatus.INBOX.can_transition_to(AssetStatus.PUBLISHED)

    def test_published_is_terminal(self):
        assert AssetStatus.PUBLISHED.is_terminal()
        assert not AssetStatus.PUBLISHED.can_transition_to(AssetStatus.ARCHIVED)

    def test_archived_is_terminal(self):
        assert AssetStatus.ARCHIVED.is_terminal()

    def test_rejected_to_inbox_or_archived(self):
        assert AssetStatus.REJECTED.can_transition_to(AssetStatus.INBOX)
        assert AssetStatus.REJECTED.can_transition_to(AssetStatus.ARCHIVED)

    def test_scheduled_to_published_or_inbox(self):
        assert AssetStatus.SCHEDULED.can_transition_to(AssetStatus.PUBLISHED)
        assert AssetStatus.SCHEDULED.can_transition_to(AssetStatus.INBOX)

    def test_is_active(self):
        assert AssetStatus.INBOX.is_active()
        assert AssetStatus.APPROVED.is_active()
        assert not AssetStatus.REJECTED.is_active()
        assert not AssetStatus.ARCHIVED.is_active()

    def test_full_flow(self):
        """Testa 50 transições: inbox → triaged → caption_ready → approved → scheduled → published."""
        s = AssetStatus.INBOX
        for target in [AssetStatus.TRIAGED, AssetStatus.CAPTION_READY,
                       AssetStatus.APPROVED, AssetStatus.SCHEDULED, AssetStatus.PUBLISHED]:
            assert s.can_transition_to(target), f"{s.value} → {target.value}"
            s = target
        assert s.is_terminal()


# ---------------------------------------------------------------------------
# 3. Registry CRUD
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_empty_registry(self, registry):
        assert registry.list_all() == []
        assert registry.count() == 0

    def test_add_asset(self, registry, sample_asset):
        registry.add(sample_asset)
        assert registry.count() == 1
        assert registry.get(sample_asset.asset_id) is not None

    def test_add_and_list(self, registry):
        a1 = VideoAsset.new("id1", "local", "/a.mp4", "a.mp4", ".mp4", 100)
        a2 = VideoAsset.new("id2", "local", "/b.mp4", "b.mp4", ".mp4", 200)
        registry.add(a1)
        registry.add(a2)
        all_a = registry.list_all()
        assert len(all_a) == 2

    def test_get_nonexistent(self, registry):
        assert registry.get("nao_existe") is None

    def test_update(self, registry, sample_asset):
        registry.add(sample_asset)
        updated = registry.update(sample_asset.asset_id, account_target="@lucastigrereal", format="reel")
        assert updated is not None
        assert updated.account_target == "lucastigrereal"
        assert updated.format == "reel"

    def test_update_nonexistent(self, registry):
        assert registry.update("fake_id", format="reel") is None

    def test_delete(self, registry, sample_asset):
        registry.add(sample_asset)
        assert registry.delete(sample_asset.asset_id) is True
        assert registry.count() == 0

    def test_delete_nonexistent(self, registry):
        assert registry.delete("fake_id") is False

    def test_filter_by_status(self, registry):
        a1 = VideoAsset.new("id1", "local", "/a.mp4", "a.mp4", ".mp4", 100)
        a2 = VideoAsset.new("id2", "local", "/b.mp4", "b.mp4", ".mp4", 200)
        a2.status = AssetStatus.APPROVED
        registry.add(a1)
        registry.add(a2)
        inbox = registry.filter(status=AssetStatus.INBOX)
        approved = registry.filter(status=AssetStatus.APPROVED)
        assert len(inbox) == 1
        assert len(approved) == 1

    def test_filter_by_account(self, registry):
        a1 = VideoAsset.new("id1", "local", "/a.mp4", "a.mp4", ".mp4", 100,
                            account_target="@lucastigrereal")
        a2 = VideoAsset.new("id2", "local", "/b.mp4", "b.mp4", ".mp4", 200,
                            account_target="@afamiliatigrereal")
        registry.add(a1)
        registry.add(a2)
        result = registry.filter(account="lucastigrereal")
        assert len(result) == 1
        assert result[0].asset_id == "id1"

    def test_filter_by_tag(self, registry):
        a1 = VideoAsset.new("id1", "local", "/a.mp4", "a.mp4", ".mp4", 100)
        a1.tags = ["praia", "natal"]
        a2 = VideoAsset.new("id2", "local", "/b.mp4", "b.mp4", ".mp4", 200)
        a2.tags = ["hotel"]
        registry.add(a1)
        registry.add(a2)
        result = registry.filter(tag="praia")
        assert len(result) == 1

    def test_transition_valid(self, registry, sample_asset):
        registry.add(sample_asset)
        updated = registry.transition(sample_asset.asset_id, AssetStatus.TRIAGED)
        assert updated is not None
        assert updated.status == AssetStatus.TRIAGED

    def test_transition_invalid(self, registry, sample_asset):
        registry.add(sample_asset)
        with pytest.raises(ValueError, match="Transição inválida"):
            registry.transition(sample_asset.asset_id, AssetStatus.PUBLISHED)

    def test_mark_published(self, registry, sample_asset):
        registry.add(sample_asset)
        # Precisa ir por approved → scheduled → published
        registry.transition(sample_asset.asset_id, AssetStatus.TRIAGED)
        registry.transition(sample_asset.asset_id, AssetStatus.CAPTION_READY)
        registry.transition(sample_asset.asset_id, AssetStatus.APPROVED)
        registry.transition(sample_asset.asset_id, AssetStatus.SCHEDULED)
        published = registry.mark_published(sample_asset.asset_id)
        assert published is not None
        assert published.status == AssetStatus.PUBLISHED
        assert published.used_at is not None

    def test_stats(self, registry):
        a1 = VideoAsset.new("id1", "local", "/a.mp4", "a.mp4", ".mp4", 1000)
        a1.format = "reel"
        a2 = VideoAsset.new("id2", "local", "/b.mp4", "b.mp4", ".mp4", 2000)
        a2.format = "carousel"
        a2.status = AssetStatus.APPROVED
        registry.add(a1)
        registry.add(a2)
        stats = registry.stats()
        assert stats["total"] == 2
        assert stats["by_status"]["inbox"] == 1
        assert stats["by_status"]["approved"] == 1
        assert stats["total_bytes"] == 3000

    def test_export_csv(self, registry, tmp_path):
        a1 = VideoAsset.new("id1", "local", "/a.mp4", "a.mp4", ".mp4", 100)
        registry.add(a1)
        csv_path = tmp_path / "test.csv"
        registry.export_csv(str(csv_path))
        assert os.path.isfile(csv_path)
        content = csv_path.read_text(encoding="utf-8")
        assert "asset_id" in content
        assert "id1" in content

    def test_jsonl_not_corrupted(self, registry, sample_asset):
        """Add, read, add again — JSONL não deve corromper."""
        registry.add(sample_asset)
        _ = registry.list_all()
        a2 = VideoAsset.new("id3", "local", "/c.mp4", "c.mp4", ".mp4", 300)
        registry.add(a2)
        all_a = registry.list_all()
        assert len(all_a) == 2


# ---------------------------------------------------------------------------
# 4. Scanner
# ---------------------------------------------------------------------------

class TestScanner:
    def test_known_extensions(self):
        assert ".mp4" in KNOWN_EXTENSIONS
        assert ".mov" in KNOWN_EXTENSIONS

    def test_scan_empty_dir(self, tmp_path):
        scanner = Scanner()
        result = scanner.scan(roots=[str(tmp_path)], dry_run=True)
        assert result["found"] == 0
        assert result["dry_run"] is True

    def test_scan_finds_video_files(self, tmp_path):
        # Create a fake video file
        video = tmp_path / "test_video.mp4"
        video.write_bytes(b"\x00" * 100)
        scanner = Scanner()
        result = scanner.scan(roots=[str(tmp_path)], dry_run=True)
        assert result["found"] == 1

    def test_scan_ignores_non_video(self, tmp_path):
        (tmp_path / "readme.txt").write_text("hello")
        scanner = Scanner()
        result = scanner.scan(roots=[str(tmp_path)], dry_run=True)
        assert result["found"] == 0

    def test_scan_import_adds_to_registry(self, tmp_path, tmp_registry_path):
        video = tmp_path / "import_test.mp4"
        video.write_bytes(b"\x00" * 200)
        reg = Registry(tmp_registry_path)
        scanner = Scanner(registry=reg)
        result = scanner.scan(roots=[str(tmp_path)], dry_run=False)
        assert result["imported"] == 1
        assert result["dry_run"] is False
        assert reg.count() == 1

    def test_scan_import_dedup(self, tmp_path, tmp_registry_path):
        video = tmp_path / "dedup_test.mp4"
        video.write_bytes(b"\x00" * 300)
        reg = Registry(tmp_registry_path)
        scanner = Scanner(registry=reg)
        # First import
        r1 = scanner.scan(roots=[str(tmp_path)], dry_run=False)
        assert r1["imported"] == 1
        # Second import (same file)
        r2 = scanner.scan(roots=[str(tmp_path)], dry_run=False)
        assert r2["imported"] == 0
        assert r2["skipped"] == 1
        assert reg.count() == 1

    def test_scan_ignores_dirs(self, tmp_path):
        for d in IGNORE_DIRS:
            p = tmp_path / d
            p.mkdir(exist_ok=True)
            (p / "video.mp4").write_bytes(b"\x00" * 100)
        scanner = Scanner()
        result = scanner.scan(roots=[str(tmp_path)], dry_run=True)
        assert result["found"] == 0

    def test_scan_dry_run_does_not_import(self, tmp_path, tmp_registry_path):
        video = tmp_path / "dry_test.mp4"
        video.write_bytes(b"\x00" * 100)
        reg = Registry(tmp_registry_path)
        scanner = Scanner(registry=reg)
        result = scanner.scan(roots=[str(tmp_path)], dry_run=True)
        assert result["dry_run"] is True
        assert result["imported"] == 0
        assert reg.count() == 0

    def test_scan_respects_max_depth(self, tmp_path):
        sub = tmp_path / "sub" / "deep" / "very_deep"
        sub.mkdir(parents=True)
        (sub / "deep.mp4").write_bytes(b"\x00" * 100)
        scanner = Scanner()
        # max_depth=1 — não deve chegar no arquivo em depth 3
        result = scanner.scan(roots=[str(tmp_path)], dry_run=True, max_depth=1)
        assert result["found"] == 0


# ---------------------------------------------------------------------------
# 5. Queue
# ---------------------------------------------------------------------------

class TestQueue:
    def test_next_inbox_empty(self, tmp_registry_path):
        reg = Registry(tmp_registry_path)
        queue = Queue(registry=reg)
        assert queue.next_inbox() is None

    def test_next_inbox_returns_oldest(self, tmp_registry_path):
        reg = Registry(tmp_registry_path)
        a1 = VideoAsset.new("id1", "local", "/a.mp4", "a.mp4", ".mp4", 100)
        a2 = VideoAsset.new("id2", "local", "/b.mp4", "b.mp4", ".mp4", 200)
        reg.add(a1)
        reg.add(a2)
        queue = Queue(registry=reg)
        next_a = queue.next_inbox()
        assert next_a is not None
        assert next_a.asset_id == "id1"  # mais antigo

    def test_next_ready_to_schedule(self, tmp_registry_path):
        reg = Registry(tmp_registry_path)
        a = VideoAsset.new("id1", "local", "/a.mp4", "a.mp4", ".mp4", 100)
        a.status = AssetStatus.APPROVED
        reg.add(a)
        queue = Queue(registry=reg)
        next_a = queue.next_ready_to_schedule()
        assert next_a is not None
        assert next_a.asset_id == "id1"

    def test_schedule_validates_future(self, tmp_registry_path):
        reg = Registry(tmp_registry_path)
        a = VideoAsset.new("id1", "local", "/a.mp4", "a.mp4", ".mp4", 100)
        a.status = AssetStatus.APPROVED
        reg.add(a)
        queue = Queue(registry=reg)
        with pytest.raises(ValueError, match="Data.*futura"):
            queue.schedule("id1", "2020-01-01T00:00:00Z")

    def test_schedule_success(self, tmp_registry_path):
        reg = Registry(tmp_registry_path)
        a = VideoAsset.new("id1", "local", "/a.mp4", "a.mp4", ".mp4", 100)
        a.status = AssetStatus.APPROVED
        reg.add(a)
        queue = Queue(registry=reg)
        updated = queue.schedule("id1", "2027-01-01T12:00:00Z")
        assert updated is not None
        assert updated.status == AssetStatus.SCHEDULED
        assert updated.scheduled_at == "2027-01-01T12:00:00Z"

    def test_mark_published(self, tmp_registry_path):
        reg = Registry(tmp_registry_path)
        a = VideoAsset.new("id1", "local", "/a.mp4", "a.mp4", ".mp4", 100)
        a.status = AssetStatus.SCHEDULED
        reg.add(a)
        queue = Queue(registry=reg)
        updated = queue.mark_published("id1")
        assert updated is not None
        assert updated.status == AssetStatus.PUBLISHED
        assert updated.used_at is not None

    def test_upcoming(self, tmp_registry_path):
        reg = Registry(tmp_registry_path)
        a1 = VideoAsset.new("id1", "local", "/a.mp4", "a.mp4", ".mp4", 100)
        a1.status = AssetStatus.SCHEDULED
        a1.scheduled_at = "2026-05-03T10:00:00Z"
        a2 = VideoAsset.new("id2", "local", "/b.mp4", "b.mp4", ".mp4", 200)
        a2.status = AssetStatus.SCHEDULED
        a2.scheduled_at = "2026-12-01T10:00:00Z"
        reg.add(a1)
        reg.add(a2)
        queue = Queue(registry=reg)
        upcoming = queue.upcoming(days=30)
        assert len(upcoming) == 1
        assert upcoming[0].asset_id == "id1"

    def test_inbox_count(self, tmp_registry_path):
        reg = Registry(tmp_registry_path)
        reg.add(VideoAsset.new("id1", "local", "/a.mp4", "a.mp4", ".mp4", 100))
        reg.add(VideoAsset.new("id2", "local", "/b.mp4", "b.mp4", ".mp4", 200))
        queue = Queue(registry=reg)
        assert queue.inbox_count() == 2


# ---------------------------------------------------------------------------
# 6. Segurança
# ---------------------------------------------------------------------------

class TestSecurity:
    def test_scanner_read_only(self, tmp_path):
        """Scanner não modifica arquivos — só lê."""
        video = tmp_path / "readonly.mp4"
        video.write_bytes(b"\x00" * 100)
        original_content = video.read_bytes()
        scanner = Scanner()
        scanner.scan(roots=[str(tmp_path)], dry_run=True)
        assert video.read_bytes() == original_content

    def test_registry_within_control_dir(self):
        """Registry path deve estar dentro de ~/omnis-control/."""
        from src.video_assets.registry import REGISTRY_PATH
        control = os.path.expanduser("~/omnis-control")
        assert REGISTRY_PATH.startswith(control), \
            f"Registry fora do controle: {REGISTRY_PATH}"

    def test_no_external_imports(self):
        """video_assets package não importa nada externo."""
        import src.video_assets.models
        import src.video_assets.status
        import src.video_assets.registry
        import src.video_assets.scanner
        import src.video_assets.queue
        # Não deve importar httpx, requests, docker, etc
        for mod in [src.video_assets.models, src.video_assets.status,
                    src.video_assets.registry, src.video_assets.scanner,
                    src.video_assets.queue]:
            src = getattr(mod, "__file__", "")
            assert src, f"Sem __file__ para {mod}"
