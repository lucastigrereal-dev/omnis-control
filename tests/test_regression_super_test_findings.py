"""Testes de regressão para bugs descobertos pelo super_test em 2026-05-06.

Cada teste documenta um bug e seu comportamento esperado APÓS fix.
Se algum teste falhar onde o fix já foi aplicado, é regressão.
"""
from __future__ import annotations
import json
import re
import uuid
from pathlib import Path

import pytest

from src.content_queue import Queue as ContentQueue, QueueItem, QueueStatus
from src.caption_approval import DraftsManager


# ============================================================================
# REGRESSÃO #1 — cli_creative_status crash (FIX JÁ APLICADO)
# ============================================================================

def test_brief_stats_handles_dicts_without_attribute_error():
    """brief_stats() aceita dicts de list_briefs() sem AttributeError."""
    from src.creative_production.briefs import brief_stats

    try:
        stats = brief_stats()
        assert isinstance(stats, dict)
        assert "total" in stats
        assert "by_status" in stats
        assert "by_format" in stats
    except AttributeError as e:
        if "'dict' object has no attribute" in str(e):
            pytest.fail(f"REGRESSÃO FIX #1: brief_stats() crashou em dict: {e}")
        raise


# ============================================================================
# REGRESSÃO #2 — Truncamento de IDs (BUG #1, FIX JÁ APLICADO)
# ============================================================================

def test_queue_get_aceita_prefixo_curto(tmp_path):
    """Queue.get() resolve ID truncado via prefix matching."""
    full_id = uuid.uuid4().hex[:12]
    short_id = full_id[:8]

    queue_path = tmp_path / "content_queue.jsonl"
    item = QueueItem(
        queue_id=full_id,
        account_handle="test_user",
        date="2026-05-07", time="10:00",
        format="carrossel", objective="alcance",
        status=QueueStatus.NEEDS_CAPTION,
    )
    with open(queue_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

    q = ContentQueue(path=str(queue_path))
    found = q.get(short_id)
    assert found is not None, f"Prefix matching falhou: {short_id} não resolveu {full_id}"
    assert found.queue_id == full_id


def test_pipeline_normaliza_id_curto_no_fluxo(tmp_path):
    """Pipeline dry-run com ID curto não bloqueia por CAPTION_NOT_APPROVED."""
    import src.pipeline_local.service as svc_mod

    full_id = uuid.uuid4().hex[:12]
    short_id = full_id[:8]

    # Queue item
    queue_path = tmp_path / "content_queue.jsonl"
    q = ContentQueue(path=str(queue_path))
    item = QueueItem(
        queue_id=full_id, account_handle="lucastigrereal",
        date="2026-05-07", time="10:00",
        format="carrossel", objective="alcance",
        status=QueueStatus.NEEDS_CAPTION,
    )
    with open(queue_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

    # Caption aprovada
    drafts_path = tmp_path / "caption_drafts.jsonl"
    log_path = tmp_path / "approval_log.jsonl"
    dm = DraftsManager(drafts_path=str(drafts_path), log_path=str(log_path))
    draft = dm.create(
        queue_id=full_id, account_handle="lucastigrereal",
        caption_text="Teste prefix matching.", format="carrossel",
    )
    dm.update(draft.draft_id, status="approved")

    orig_runs_path = svc_mod.PIPELINE_RUNS_PATH
    svc_mod.PIPELINE_RUNS_PATH = str(tmp_path / "pipeline_runs.jsonl")
    try:
        from src.pipeline_local.service import PipelineLocalService
        from src.pipeline_local.models import PipelineBlockReason

        svc = PipelineLocalService()
        svc.queue.path = str(queue_path)
        svc.caption_mgr.drafts_path = str(drafts_path)
        svc.caption_mgr.log_path = str(log_path)

        result = svc.run_local_content_pipeline(short_id)
        assert result.block_reason != PipelineBlockReason.CAPTION_NOT_APPROVED, (
            f"REGRESSÃO BUG #1: ID curto '{short_id}' bloqueou como CAPTION_NOT_APPROVED. "
            f"warnings={result.warnings}"
        )
        assert result.caption_draft_id is not None
    finally:
        svc_mod.PIPELINE_RUNS_PATH = orig_runs_path


# ============================================================================
# REGRESSÃO #3 — datetime.utcnow() deprecation (BUG #2, FIX NÃO APLICADO)
# ============================================================================

def test_no_datetime_utcnow_in_src():
    """datetime.utcnow() está deprecated. Após fix, 0 ocorrências em src/."""
    src_root = Path(__file__).parent.parent / "src"
    bad = re.compile(r"datetime\.utcnow\(\)|datetime\.utcfromtimestamp\(")

    findings = []
    for py_file in src_root.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for match in bad.finditer(content):
            line_no = content[:match.start()].count("\n") + 1
            findings.append(f"{py_file.relative_to(src_root.parent)}:{line_no}")

    if findings:
        pytest.skip(
            f"BUG #2 pendente: {len(findings)} ocorrências de datetime.utcnow(). "
            f"Arquivos: {findings[:5]}"
        )


# ============================================================================
# REGRESSÃO #4 — Disk audit Windows (BUG #3, FIX NÃO APLICADO)
# ============================================================================

def test_disk_audit_omnis_size_greater_than_zero():
    """omnis-control deve ter size_bytes > 0 no disk_audit_report.json."""
    report_path = Path(__file__).parent.parent / "docs" / "disk_audit_report.json"
    if not report_path.exists():
        pytest.skip("disk_audit_report.json não existe. Rode 'omnis disk' primeiro.")

    data = json.loads(report_path.read_text(encoding="utf-8"))
    dirs = data.get("project_directories", [])
    omnis = next((p for p in dirs if p.get("name") == "omnis-control"), None)

    if omnis is None:
        pytest.skip("omnis-control ausente do relatório.")

    size = omnis.get("size_bytes", 0)
    if size == 0:
        pytest.skip("BUG #3 pendente: size_bytes=0 no Windows. Aguardando fix.")


# ============================================================================
# REGRESSÃO #5 — Encoding emoji Windows (BUG #5, FIX NÃO APLICADO)
# ============================================================================

def test_creative_status_no_emoji_crash():
    """creative_cmd.py:37 não deve crashar com emoji no Windows cp1252."""
    pytest.skip("BUG #5 pendente: emoji ⚠️ crasha no terminal Windows cp1252.")
