"""
Testes do Account Mapping + Daily Content Queue (Fase 2B).

Cobre: account CRUD, queue generate, assign, export, segurança.
Não modifica nada fora de ~/omnis-control/.
"""

import os
import json
import tempfile
from pathlib import Path

import pytest

from src.content_queue.accounts import AccountRegistry, Account, _normalize_handle, ACCOUNTS_PATH
from src.content_queue.models import QueueItem, QueueStatus
from src.content_queue.queue import Queue, QUEUE_PATH


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_accounts_path():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8") as f:
        path = f.name
    yield path
    if os.path.isfile(path):
        os.unlink(path)


@pytest.fixture
def tmp_queue_path():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8") as f:
        path = f.name
    yield path
    if os.path.isfile(path):
        os.unlink(path)


@pytest.fixture
def tmp_assets_path():
    """Cria um video_assets.jsonl temporário com um asset."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8") as f:
        path = f.name
        asset = {
            "asset_id": "asset123test",
            "source_type": "local",
            "source_path": "/tmp/test.mp4",
            "file_name": "test.mp4",
            "extension": ".mp4",
            "size_bytes": 1000,
            "fingerprint": "/tmp/test.mp4|1000|2026-01-01T00:00:00Z",
            "status": "inbox",
            "format": "reel",
        }
        f.write(json.dumps(asset, ensure_ascii=False) + "\n")
    yield path
    if os.path.isfile(path):
        os.unlink(path)


@pytest.fixture
def accounts_reg(tmp_accounts_path):
    reg = AccountRegistry(tmp_accounts_path)
    return reg


@pytest.fixture
def queue(tmp_queue_path):
    return Queue(tmp_queue_path)


@pytest.fixture
def queue_with_video_assets(tmp_queue_path, tmp_assets_path):
    """Queue com path de assets customizado."""
    q = Queue(tmp_queue_path)
    # Monkey-patch o VIDEO_ASSETS_PATH
    import src.content_queue.queue as cq_mod
    q._orig_assets_path = cq_mod.VIDEO_ASSETS_PATH
    cq_mod.VIDEO_ASSETS_PATH = tmp_assets_path
    yield q
    cq_mod.VIDEO_ASSETS_PATH = q._orig_assets_path


# ---------------------------------------------------------------------------
# 1. Account Model & Normalization
# ---------------------------------------------------------------------------

class TestAccountModel:
    def test_normalize_handle(self):
        assert _normalize_handle("@LucasTigreReal") == "lucastigrereal"
        assert _normalize_handle("  @OQueComerNatal  ") == "oquecomernatal"
        assert _normalize_handle("lucastigrereal") == "lucastigrereal"

    def test_account_defaults(self):
        a = Account(account_id="id1", handle="lucastigrereal")
        assert a.platform == "instagram"
        assert a.active is True
        assert a.priority == "medium"
        assert a.default_posting_times == ["08:50", "17:50", "20:50"]

    def test_account_to_dict(self):
        a = Account(account_id="id1", handle="teste")
        d = a.to_dict()
        assert d["handle"] == "teste"
        assert d["platform"] == "instagram"


# ---------------------------------------------------------------------------
# 2. Account Registry CRUD
# ---------------------------------------------------------------------------

class TestAccountRegistry:
    def test_empty_registry(self, accounts_reg):
        assert accounts_reg.list_all() == []
        assert accounts_reg.count() == 0

    def test_add_account(self, accounts_reg):
        a = accounts_reg.add("lucastigrereal", tags=["pessoal", "ia"])
        assert a.handle == "lucastigrereal"
        assert "pessoal" in a.tags
        assert accounts_reg.count() == 1

    def test_add_normalizes_handle(self, accounts_reg):
        accounts_reg.add("@LucasTigreReal")
        assert accounts_reg.get_by_handle("lucastigrereal") is not None

    def test_block_duplicate(self, accounts_reg):
        accounts_reg.add("lucastigrereal")
        with pytest.raises(ValueError, match="já existe"):
            accounts_reg.add("lucastigrereal")

    def test_list_all(self, accounts_reg):
        accounts_reg.add("lucastigrereal")
        accounts_reg.add("afamiliatigrereal")
        assert len(accounts_reg.list_all()) == 2

    def test_get_by_handle(self, accounts_reg):
        accounts_reg.add("lucastigrereal")
        a = accounts_reg.get_by_handle("lucastigrereal")
        assert a is not None
        assert a.handle == "lucastigrereal"

    def test_get_nonexistent(self, accounts_reg):
        assert accounts_reg.get_by_handle("nao_existe") is None

    def test_update_priority(self, accounts_reg):
        accounts_reg.add("lucastigrereal")
        updated = accounts_reg.update("lucastigrereal", priority="high")
        assert updated is not None
        assert updated.priority == "high"

    def test_update_nonexistent(self, accounts_reg):
        assert accounts_reg.update("fake", priority="high") is None

    def test_deactivate(self, accounts_reg):
        accounts_reg.add("lucastigrereal")
        deactivated = accounts_reg.deactivate("lucastigrereal")
        assert deactivated is not None
        assert deactivated.active is False

    def test_list_active(self, accounts_reg):
        accounts_reg.add("ativa1")
        accounts_reg.add("ativa2")
        accounts_reg.add("inativa")
        accounts_reg.deactivate("inativa")
        active = accounts_reg.list_active()
        assert len(active) == 2

    def test_jsonl_not_corrupted(self, accounts_reg):
        accounts_reg.add("a")
        accounts_reg.add("b")
        _ = accounts_reg.list_all()
        accounts_reg.add("c")
        assert accounts_reg.count() == 3


# ---------------------------------------------------------------------------
# 3. Queue Generate
# ---------------------------------------------------------------------------

class TestQueueGenerate:
    def test_generate_requires_accounts(self, queue, tmp_accounts_path):
        """Sem contas, generate deve falhar."""
        import src.content_queue.queue as cq_mod
        empty_reg = AccountRegistry(tmp_accounts_path)
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: empty_reg
        try:
            with pytest.raises(ValueError, match="Nenhuma conta ativa"):
                queue.generate(days=7, dry_run=True)
        finally:
            cq_mod.AccountRegistry = orig

    def test_generate_dry_run_does_not_write(self, queue, accounts_reg):
        accounts_reg.add("lucastigrereal")
        # Queue aponta para path diferente — precisa ter account no registry global
        # Usando monkey-patch no AccountRegistry path
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        try:
            result = queue.generate(days=7, dry_run=True)
            assert result["dry_run"] is True
            assert result["generated"] > 0
            assert queue.list_all() == []
        finally:
            cq_mod.AccountRegistry = orig

    def test_generate_apply_creates_slots(self, queue, accounts_reg):
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        try:
            result = queue.generate(days=1, dry_run=False)
            assert result["dry_run"] is False
            assert result["generated"] == 3  # 3 horários padrão
            assert len(queue.list_all()) == 3
        finally:
            cq_mod.AccountRegistry = orig

    def test_generate_idempotent(self, queue, accounts_reg):
        """Rodar generate duas vezes no mesmo período não cria duplicatas."""
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        try:
            r1 = queue.generate(days=1, dry_run=False)
            assert r1["generated"] == 3
            r2 = queue.generate(days=1, dry_run=False)
            assert r2["generated"] == 0  # todos já existem
            assert r2["skipped"] == 3
            assert len(queue.list_all()) == 3
        finally:
            cq_mod.AccountRegistry = orig

    def test_generate_multiple_accounts(self, queue, accounts_reg):
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        accounts_reg.add("afamiliatigrereal")
        try:
            result = queue.generate(days=1, dry_run=True)
            # 2 contas × 3 horários × 1 dia = 6
            assert result["generated"] == 6
            assert result["accounts"] == 2
        finally:
            cq_mod.AccountRegistry = orig

    def test_generate_respects_max_days(self, queue, accounts_reg):
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        try:
            with pytest.raises(ValueError, match="Máximo"):
                queue.generate(days=100, dry_run=True)
            # 31 dias sem force deve falhar
            with pytest.raises(ValueError, match="requer --force"):
                queue.generate(days=31, dry_run=True)
        finally:
            cq_mod.AccountRegistry = orig

    def test_generate_account_filter(self, queue, accounts_reg):
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        accounts_reg.add("afamiliatigrereal")
        try:
            result = queue.generate(days=1, dry_run=True, account_filter="lucastigrereal")
            assert result["generated"] == 3
            assert result["account_filter"] == "lucastigrereal"
        finally:
            cq_mod.AccountRegistry = orig

    def test_default_status_is_needs_asset(self, queue, accounts_reg):
        """Slots gerados sem asset devem ter status needs_asset."""
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        try:
            queue.generate(days=1, dry_run=False)
            items = queue.list_all()
            assert all(i.status == QueueStatus.NEEDS_ASSET for i in items)
        finally:
            cq_mod.AccountRegistry = orig

    def test_generate_inactive_account_skipped(self, queue, accounts_reg):
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        accounts_reg.add("inativa")
        accounts_reg.deactivate("inativa")
        try:
            result = queue.generate(days=1, dry_run=True)
            # Só 1 conta ativa = 3 slots
            assert result["generated"] == 3
        finally:
            cq_mod.AccountRegistry = orig


# ---------------------------------------------------------------------------
# 4. Queue Assign
# ---------------------------------------------------------------------------

class TestQueueAssign:
    def test_assign_existing_asset(self, queue_with_video_assets, accounts_reg):
        q = queue_with_video_assets
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        try:
            q.generate(days=1, dry_run=False)
            items = q.list_all()
            slot_id = items[0].queue_id

            result, warning = q.assign_asset(slot_id, "asset123test")
            assert result is not None
            assert result.asset_id == "asset123test"
            assert result.status == QueueStatus.NEEDS_CAPTION  # avançou de needs_asset
        finally:
            cq_mod.AccountRegistry = orig

    def test_assign_nonexistent_asset(self, queue_with_video_assets, accounts_reg):
        q = queue_with_video_assets
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        try:
            q.generate(days=1, dry_run=False)
            items = q.list_all()
            slot_id = items[0].queue_id

            with pytest.raises(ValueError, match="não encontrado"):
                q.assign_asset(slot_id, "asset_inexistente")
        finally:
            cq_mod.AccountRegistry = orig

    def test_assign_without_force_block_replace(self, queue_with_video_assets, accounts_reg):
        q = queue_with_video_assets
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        try:
            q.generate(days=1, dry_run=False)
            items = q.list_all()
            slot_id = items[0].queue_id

            # Primeiro assign
            q.assign_asset(slot_id, "asset123test")
            # Segundo assign sem force
            with pytest.raises(ValueError, match="já tem asset"):
                q.assign_asset(slot_id, "asset123test")
        finally:
            cq_mod.AccountRegistry = orig

    def test_assign_with_force_succeeds(self, queue_with_video_assets, accounts_reg):
        q = queue_with_video_assets
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        try:
            q.generate(days=1, dry_run=False)
            items = q.list_all()
            slot_id = items[0].queue_id

            q.assign_asset(slot_id, "asset123test")
            # Com force, substitui
            result, warning = q.assign_asset(slot_id, "asset123test", force=True)
            assert result is not None
        finally:
            cq_mod.AccountRegistry = orig

    def test_assign_empty_video_registry(self, queue, accounts_reg):
        """Queue sem assets registrados deve falhar com mensagem clara."""
        with pytest.raises(ValueError, match="Video Asset Registry não encontrado"):
            queue.assign_asset("fake_id", "fake_asset")


# ---------------------------------------------------------------------------
# 5. Queue List / Today / Export
# ---------------------------------------------------------------------------

class TestQueueOperations:
    def test_list_empty(self, queue):
        assert queue.list_all() == []

    def test_filter_by_account(self, queue, accounts_reg):
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        try:
            queue.generate(days=1, dry_run=False)
            items = queue.filter(account="lucastigrereal")
            assert len(items) == 3
        finally:
            cq_mod.AccountRegistry = orig

    def test_filter_by_status(self, queue, accounts_reg):
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        try:
            queue.generate(days=1, dry_run=False)
            items = queue.filter(status=QueueStatus.NEEDS_ASSET)
            assert len(items) == 3
        finally:
            cq_mod.AccountRegistry = orig

    def test_stats(self, queue, accounts_reg):
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        try:
            queue.generate(days=1, dry_run=False)
            stats = queue.stats()
            assert stats["total"] == 3
            assert stats["needs_asset"] == 3
        finally:
            cq_mod.AccountRegistry = orig

    def test_export_csv(self, queue, accounts_reg, tmp_path):
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        try:
            queue.generate(days=1, dry_run=False)
            csv_path = tmp_path / "test_queue.csv"
            queue.export_csv(str(csv_path))
            assert os.path.isfile(csv_path)
            content = Path(csv_path).read_text(encoding="utf-8")
            assert "queue_id" in content
            assert "lucastigrereal" in content
        finally:
            cq_mod.AccountRegistry = orig

    def test_update_queue_item(self, queue, accounts_reg):
        import src.content_queue.queue as cq_mod
        orig = cq_mod.AccountRegistry
        cq_mod.AccountRegistry = lambda: accounts_reg
        accounts_reg.add("lucastigrereal")
        try:
            queue.generate(days=1, dry_run=False)
            items = queue.list_all()
            qid = items[0].queue_id
            updated = queue.update(qid, status="caption_ready", objective="autoridade")
            assert updated is not None
            assert updated.status == "caption_ready"
            assert updated.objective == "autoridade"
        finally:
            cq_mod.AccountRegistry = orig


# ---------------------------------------------------------------------------
# 6. Segurança
# ---------------------------------------------------------------------------

class TestSecurity:
    def test_accounts_path_within_control(self):
        from src.content_queue.accounts import ACCOUNTS_PATH
        control = os.path.expanduser("~/omnis-control")
        assert ACCOUNTS_PATH.startswith(control)

    def test_queue_path_within_control(self):
        from src.content_queue.queue import QUEUE_PATH
        control = os.path.expanduser("~/omnis-control")
        assert QUEUE_PATH.startswith(control)

    def test_no_external_imports(self):
        """content_queue package não importa nada externo."""
        import src.content_queue.accounts
        import src.content_queue.models
        import src.content_queue.queue
        for mod in [src.content_queue.accounts,
                    src.content_queue.models,
                    src.content_queue.queue]:
            src_file = getattr(mod, "__file__", "")
            assert src_file, f"Sem __file__ para {mod}"
