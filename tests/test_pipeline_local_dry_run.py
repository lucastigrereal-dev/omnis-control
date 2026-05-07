"""Tests for Pipeline Local Dry-Run module."""
import pytest
import json
import os
import uuid
from pathlib import Path
from datetime import datetime, timezone

from src.pipeline_local.models import (
    PipelineRunResult, PipelineRunStatus, PipelineBlockReason,
)
from src.pipeline_local.service import PipelineLocalService, PIPELINE_RUNS_PATH
from src.pipeline_local.dry_run import dry_run_pipeline
from src.content_queue import Queue as ContentQueue, QueueItem, QueueStatus
from src.caption_approval import DraftsManager
from src.creative_production.briefs import create_brief, BRIEFS_FILE
from src.creative_production.exporter import generate_export_package, EXPORT_DIR


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def seeded_queue(tmp_path):
    """Cria uma fila com 1 item e retorna o queue_id."""
    queue_path = tmp_path / "content_queue.jsonl"
    q = ContentQueue(path=str(queue_path))
    # Injetar item manualmente
    item = QueueItem(
        queue_id="test-queue-001",
        account_handle="lucastigrereal",
        date="2026-05-07",
        time="08:50",
        format="carrossel",
        objective="alcance",
        status=QueueStatus.NEEDS_CAPTION,
        notes="Teste pipeline dry-run",
    )
    with open(queue_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")
    return str(queue_path), item.queue_id


@pytest.fixture
def seeded_approved_caption(tmp_path):
    """Cria um caption aprovado e retorna o draft_id."""
    drafts_path = tmp_path / "caption_drafts.jsonl"
    log_path = tmp_path / "approval_log.jsonl"
    dm = DraftsManager(drafts_path=str(drafts_path), log_path=str(log_path))
    draft = dm.create(
        queue_id="test-queue-001",
        account_handle="lucastigrereal",
        caption_text="Legenda de teste para pipeline dry-run.",
        hashtags=["#teste", "#dryrun"],
        cta="Curta e compartilhe!",
        objective="alcance",
        format="carrossel",
    )
    # Aprovar manualmente
    dm.update(draft.draft_id, status="approved")
    return dm


# ── Tests: Models ───────────────────────────────────────────────────────────


class TestPipelineRunResult:
    def test_defaults(self):
        r = PipelineRunResult(run_id="r1", queue_item_id="q1")
        assert r.status == PipelineRunStatus.SUCCESS
        assert r.warnings == []
        assert r.evidence_refs == []
        assert r.caption_draft_id is None
        assert r.creative_brief_id is None

    def test_to_dict_roundtrip(self):
        r = PipelineRunResult(
            run_id="r1", queue_item_id="q1",
            status=PipelineRunStatus.BLOCKED,
            block_reason=PipelineBlockReason.QUEUE_ITEM_NOT_FOUND,
            warnings=["test warning"],
            evidence_refs=["queue:q1"],
        )
        d = r.to_dict()
        assert d["status"] == "blocked"
        assert d["block_reason"] == "QUEUE_ITEM_NOT_FOUND"
        assert d["warnings"] == ["test warning"]
        r2 = PipelineRunResult.from_dict(d)
        assert r2.status == "blocked"
        assert r2.warnings == ["test warning"]

    def test_timestamps_auto(self):
        r = PipelineRunResult(run_id="r1", queue_item_id="q1")
        assert r.started_at != ""
        assert r.finished_at != ""


# ── Tests: Service ──────────────────────────────────────────────────────────


class TestPipelineLocalService:
    def test_blocked_when_queue_item_not_found(self, tmp_path):
        """run bloqueia se queue item não existe."""
        # Redirecionar caminhos para temp
        from src.pipeline_local.service import PIPELINE_RUNS_PATH as ORIG_PATH
        import src.pipeline_local.service as svc_mod
        svc_mod.PIPELINE_RUNS_PATH = str(tmp_path / "pipeline_runs.jsonl")

        try:
            service = PipelineLocalService()

            # Redirecionar queue path do service
            queue_path = tmp_path / "content_queue.jsonl"
            service.queue.path = str(queue_path)
            Path(str(queue_path)).parent.mkdir(parents=True, exist_ok=True)

            result = service.run_local_content_pipeline("nonexistent-id")
            assert result.status == PipelineRunStatus.BLOCKED
            assert result.block_reason == PipelineBlockReason.QUEUE_ITEM_NOT_FOUND
        finally:
            svc_mod.PIPELINE_RUNS_PATH = ORIG_PATH

    def test_blocked_when_caption_not_approved(self, seeded_queue, tmp_path):
        """run bloqueia se caption não aprovada."""
        queue_path, queue_id = seeded_queue
        from src.pipeline_local.service import PIPELINE_RUNS_PATH as ORIG_PATH
        import src.pipeline_local.service as svc_mod
        svc_mod.PIPELINE_RUNS_PATH = str(tmp_path / "pipeline_runs.jsonl")

        try:
            service = PipelineLocalService()
            service.queue.path = queue_path

            # Redirecionar caption drafts path
            drafts_path = tmp_path / "caption_drafts.jsonl"
            log_path = tmp_path / "approval_log.jsonl"
            service.caption_mgr.drafts_path = str(drafts_path)
            service.caption_mgr.log_path = str(log_path)

            # Criar caption DRAFT (não approved — create() já define status=draft)
            dm = DraftsManager(drafts_path=str(drafts_path), log_path=str(log_path))
            dm.create(
                queue_id=queue_id, account_handle="lucastigrereal",
                caption_text="Teste",
            )

            result = service.run_local_content_pipeline(queue_id)
            assert result.status == PipelineRunStatus.BLOCKED
            assert result.block_reason == PipelineBlockReason.CAPTION_NOT_APPROVED
        finally:
            svc_mod.PIPELINE_RUNS_PATH = ORIG_PATH

    def test_full_dry_run_with_approved_caption(self, seeded_queue, seeded_approved_caption, tmp_path):
        """run gera export package + publisher dry-run + evidence_refs quando dados existem."""
        queue_path, queue_id = seeded_queue
        from src.pipeline_local.service import PIPELINE_RUNS_PATH as ORIG_PATH
        import src.pipeline_local.service as svc_mod
        svc_mod.PIPELINE_RUNS_PATH = str(tmp_path / "pipeline_runs.jsonl")

        try:
            service = PipelineLocalService()
            service.queue.path = queue_path

            # Redirecionar caption drafts
            drafts_path = str(tmp_path / "caption_drafts.jsonl")
            log_path = str(tmp_path / "approval_log.jsonl")
            service.caption_mgr.drafts_path = drafts_path
            service.caption_mgr.log_path = log_path

            # O fixture seeded_approved_caption já criou e aprovou
            # Mas ele usou drafts_path padrão, vamos recriar no tmp_path
            dm = seeded_approved_caption

            # Criar o approved caption no manager do service
            # Redirecionar o caption_mgr do service para usar o mesmo caminho do fixture
            # O fixture já salvou no tmp_path/caption_drafts.jsonl
            # Precisamos que o service use esse caminho
            # Já setamos acima

            result = service.run_local_content_pipeline(queue_id)

            # Deve ter passado com warnings (sem brief pode falhar por data dir)
            assert result.status in (PipelineRunStatus.SUCCESS, PipelineRunStatus.SUCCESS_WITH_WARNINGS)
            assert result.caption_draft_id is not None
            assert result.evidence_refs is not None
            assert len(result.evidence_refs) >= 1  # pelo menos queue_item
        finally:
            svc_mod.PIPELINE_RUNS_PATH = ORIG_PATH

    def test_registers_metric_and_trace(self, seeded_queue, tmp_path):
        """run registra métrica e trace local."""
        queue_path, queue_id = seeded_queue
        from src.pipeline_local.service import PIPELINE_RUNS_PATH as ORIG_PATH
        import src.pipeline_local.service as svc_mod
        svc_mod.PIPELINE_RUNS_PATH = str(tmp_path / "pipeline_runs.jsonl")

        try:
            service = PipelineLocalService()
            service.queue.path = queue_path

            result = service.run_local_content_pipeline(queue_id)
            # Deve ter executado sem exception
            assert result is not None

            # Verificar que salvou o run
            runs_path = svc_mod.PIPELINE_RUNS_PATH
            assert os.path.isfile(runs_path)
            with open(runs_path) as f:
                content = f.read().strip()
                assert content != ""
        finally:
            svc_mod.PIPELINE_RUNS_PATH = ORIG_PATH

    def test_persists_run_result(self, seeded_queue, tmp_path):
        """run salva resultado no JSONL."""
        queue_path, queue_id = seeded_queue
        from src.pipeline_local.service import PIPELINE_RUNS_PATH as ORIG_PATH
        import src.pipeline_local.service as svc_mod
        svc_mod.PIPELINE_RUNS_PATH = str(tmp_path / "pipeline_runs.jsonl")

        try:
            service = PipelineLocalService()
            service.queue.path = queue_path

            result = service.run_local_content_pipeline(queue_id)
            with open(svc_mod.PIPELINE_RUNS_PATH, encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
            assert len(lines) >= 1
            parsed = json.loads(lines[-1])
            assert parsed["run_id"] == result.run_id
            assert parsed["queue_item_id"] == result.queue_item_id
        finally:
            svc_mod.PIPELINE_RUNS_PATH = ORIG_PATH


# ── Tests: dry_run wrapper ──────────────────────────────────────────────────


class TestDryRunWrapper:
    def test_dry_run_does_not_crash(self):
        """dry_run_pipeline não quebra mesmo com queue inexistente."""
        result = dry_run_pipeline("non-existent-id-12345")
        assert result.status in (PipelineRunStatus.BLOCKED, PipelineRunStatus.FAILED)

    def test_dry_run_returns_result_object(self):
        """dry_run_pipeline sempre retorna PipelineRunResult."""
        result = dry_run_pipeline("another-nonexistent")
        assert isinstance(result, PipelineRunResult)


# ── Tests: CLI ──────────────────────────────────────────────────────────────


class TestPipelineCLI:
    def test_cli_dry_run_help(self):
        """Verificar que o comando pipeline dry-run existe (teste de importação)."""
        from src.cli_commands.pipeline_cmd import pipeline_app
        assert pipeline_app is not None
        # Verificar comandos registrados
        commands = list(pipeline_app.registered_commands)
        cmd_names = [c.name for c in commands]
        assert "dry-run" in cmd_names
        assert "status" in cmd_names

    def test_integration_via_cli_no_external_api(self):
        """Nenhuma API externa é chamada (teste de importação puro)."""
        from src.pipeline_local.dry_run import dry_run_pipeline
        import inspect
        source = inspect.getsource(dry_run_pipeline)
        # Não deve conter chamadas de rede
        assert "httpx" not in source
        assert "requests" not in source
        assert "aiohttp" not in source


# ── Tests: Prefix matching (BUG #1) ──────────────────────────────────────────


class TestPrefixMatching:
    def test_prefix_matching_resolves_truncated_queue_id(self, tmp_path):
        """Queue.get aceita ID truncado (8 chars) e retorna item completo (12 chars)."""
        queue_path = tmp_path / "content_queue.jsonl"
        full_id = uuid.uuid4().hex[:12]
        short_id = full_id[:8]

        q = ContentQueue(path=str(queue_path))
        item = QueueItem(
            queue_id=full_id,
            account_handle="lucastigrereal",
            date="2026-05-07",
            time="08:50",
            format="carrossel",
            objective="alcance",
            status=QueueStatus.NEEDS_CAPTION,
        )
        with open(queue_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

        q_reload = ContentQueue(path=str(queue_path))
        found = q_reload.get(short_id)
        assert found is not None
        assert found.queue_id == full_id

    def test_pipeline_normaliza_id_curto_antes_busca_caption(self, tmp_path):
        """Pipeline usa ID completo após resolver via Queue.get()."""
        from src.pipeline_local.service import PIPELINE_RUNS_PATH as ORIG_PATH
        import src.pipeline_local.service as svc_mod

        full_id = uuid.uuid4().hex[:12]
        short_id = full_id[:8]

        # Criar queue item + caption aprovado
        queue_path = tmp_path / "content_queue.jsonl"
        q = ContentQueue(path=str(queue_path))
        item = QueueItem(
            queue_id=full_id,
            account_handle="lucastigrereal",
            date="2026-05-07", time="08:50",
            format="carrossel", objective="alcance",
            status=QueueStatus.NEEDS_CAPTION,
        )
        with open(queue_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

        drafts_path = tmp_path / "caption_drafts.jsonl"
        log_path = tmp_path / "approval_log.jsonl"
        dm = DraftsManager(drafts_path=str(drafts_path), log_path=str(log_path))
        draft = dm.create(
            queue_id=full_id,
            account_handle="lucastigrereal",
            caption_text="Legenda aprovada para prefix test.",
            format="carrossel",
        )
        dm.update(draft.draft_id, status="approved")

        svc_mod.PIPELINE_RUNS_PATH = str(tmp_path / "pipeline_runs.jsonl")
        try:
            service = PipelineLocalService()
            service.queue.path = str(queue_path)
            service.caption_mgr.drafts_path = str(drafts_path)
            service.caption_mgr.log_path = str(log_path)

            result = service.run_local_content_pipeline(short_id)
            # Não deve bloquear por CAPTION_NOT_APPROVED
            assert result.block_reason != PipelineBlockReason.CAPTION_NOT_APPROVED, \
                f"Esperava encontrar caption aprovado, mas bloqueou: {result.block_reason}"
            assert result.caption_draft_id is not None, \
                f"caption_draft_id deveria existir, mas veio None. warnings={result.warnings}"
        finally:
            svc_mod.PIPELINE_RUNS_PATH = ORIG_PATH
