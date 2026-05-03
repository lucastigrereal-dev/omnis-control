"""Testes da Fase 2E — Argos Draft Bridge.

Cobre:
  - Criação de ArgosDraft com dados válidos
  - Bloqueio quando queue não existe
  - Bloqueio quando caption não está approved
  - Warning NO_ASSET_ATTACHED
  - Export CSV e JSON
  - Listagem e stats
"""

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.argos_bridge.models import ArgosDraft, ArgosStatus, WarnCode
from src.argos_bridge.draft_builder import DraftBuilder, list_all, get_by_id, stats, _load_drafts
from src.argos_bridge.exporter import export_csv, export_json, EXPORT_DIR

NON_EXISTENT_QUEUE = "nonexistent1234"

# ── Mock objects ────────────────────────────────────────


class MockQueueItem:
    def __init__(self, queue_id, account_handle, status, asset_id=None,
                 format="feed", date="2026-05-10", time="10:00"):
        self.queue_id = queue_id
        self.account_handle = account_handle
        self.status = status
        self.asset_id = asset_id
        self.format = format
        self.date = date
        self.time = time


class MockCaption:
    def __init__(self, draft_id, queue_id, status, caption_text="Texto da legenda",
                 hashtags=None, cta="Call to action"):
        self.draft_id = draft_id
        self.queue_id = queue_id
        self.status = status
        self.caption_text = caption_text
        self.hashtags = hashtags or ["#tag1", "#tag2", "#tag3"]
        self.cta = cta


# ── Fixtures ────────────────────────────────────────────

_queue_items = {}
_captions = {}


def _setup():
    _queue_items.clear()
    _captions.clear()
    # Clean up data file
    draft_path = os.path.expanduser("~/omnis-control/data/argos_drafts.jsonl")
    if os.path.isfile(draft_path):
        os.remove(draft_path)
    # Clean up exports
    for root, dirs, files in os.walk(EXPORT_DIR):
        for f in files:
            os.remove(os.path.join(root, f))


def _queue_provider(qid):
    return _queue_items.get(qid)


def _caption_provider(qid):
    return _captions.get(qid)


# ── Tests ───────────────────────────────────────────────


def test_create_valid_draft():
    _setup()
    qid = "queue_valid_001"
    _queue_items[qid] = MockQueueItem(qid, "lucastigrereal", "caption_ready",
                                       asset_id="asset_001")
    _captions[qid] = MockCaption("cap_001", qid, "approved")

    builder = DraftBuilder(_queue_provider, _caption_provider)
    draft, errors = builder.create(qid)

    assert draft is not None
    assert len(errors) == 0
    assert draft.queue_id == qid
    assert draft.account_handle == "lucastigrereal"
    assert draft.status == ArgosStatus.LOCAL_DRAFT
    assert draft.asset_id == "asset_001"
    assert len(draft.warnings) == 0  # Tem asset, sem warning


def test_create_without_asset_warns():
    _setup()
    qid = "queue_no_asset"
    _queue_items[qid] = MockQueueItem(qid, "afamiliatigrereal", "caption_ready")
    _captions[qid] = MockCaption("cap_002", qid, "approved")

    builder = DraftBuilder(_queue_provider, _caption_provider)
    draft, errors = builder.create(qid)

    assert draft is not None
    assert len(errors) == 0
    assert WarnCode.NO_ASSET_ATTACHED in draft.warnings
    assert draft.asset_id is None


def test_block_when_queue_not_found():
    _setup()
    builder = DraftBuilder(_queue_provider, _caption_provider)
    draft, errors = builder.create(NON_EXISTENT_QUEUE)
    assert draft is None
    assert len(errors) > 0
    assert "não encontrado" in errors[0]


def test_block_when_queue_not_caption_ready():
    _setup()
    qid = "queue_needs_asset"
    _queue_items[qid] = MockQueueItem(qid, "lucastigrereal", "needs_asset")
    _captions[qid] = MockCaption("cap_003", qid, "approved")

    builder = DraftBuilder(_queue_provider, _caption_provider)
    draft, errors = builder.create(qid)
    assert draft is None
    assert any("caption_ready" in e for e in errors)


def test_block_when_caption_not_approved():
    _setup()
    qid = "queue_needs_review"
    _queue_items[qid] = MockQueueItem(qid, "lucastigrereal", "caption_ready")
    _captions[qid] = MockCaption("cap_004", qid, "needs_review")

    builder = DraftBuilder(_queue_provider, _caption_provider)
    draft, errors = builder.create(qid)
    assert draft is None
    assert any("approved" in e for e in errors)


def test_block_when_no_caption_found():
    _setup()
    qid = "queue_no_caption"
    _queue_items[qid] = MockQueueItem(qid, "lucastigrereal", "caption_ready")
    # No caption registered

    builder = DraftBuilder(_queue_provider, _caption_provider)
    draft, errors = builder.create(qid)
    assert draft is None
    assert any("caption" in e.lower() for e in errors)


def test_list_and_stats():
    _setup()
    # Create 2 drafts
    qid1 = "list_test_1"
    qid2 = "list_test_2"
    _queue_items[qid1] = MockQueueItem(qid1, "lucastigrereal", "caption_ready")
    _queue_items[qid2] = MockQueueItem(qid2, "afamiliatigrereal", "caption_ready")
    _captions[qid1] = MockCaption("cap_l1", qid1, "approved")
    _captions[qid2] = MockCaption("cap_l2", qid2, "approved")

    builder = DraftBuilder(_queue_provider, _caption_provider)
    builder.create(qid1)
    builder.create(qid2)

    all_d = list_all()
    assert len(all_d) == 2

    s = stats()
    assert s["total"] == 2
    assert s["by_account"].get("lucastigrereal", 0) == 1
    assert s["by_account"].get("afamiliatigrereal", 0) == 1


def test_get_by_id():
    _setup()
    qid = "get_by_id_test"
    _queue_items[qid] = MockQueueItem(qid, "lucastigrereal", "caption_ready")
    _captions[qid] = MockCaption("cap_gbi", qid, "approved")

    builder = DraftBuilder(_queue_provider, _caption_provider)
    draft, _ = builder.create(qid)

    found = get_by_id(draft.draft_id)
    assert found is not None
    assert found.draft_id == draft.draft_id

    not_found = get_by_id("invalid_id")
    assert not_found is None


def test_export_csv():
    _setup()
    qid = "export_csv_test"
    _queue_items[qid] = MockQueueItem(qid, "lucastigrereal", "caption_ready")
    _captions[qid] = MockCaption("cap_csv", qid, "approved",
                                  caption_text="Texto para CSV",
                                  hashtags=["#tag1", "#tag2"],
                                  cta="CTA do CSV")

    builder = DraftBuilder(_queue_provider, _caption_provider)
    builder.create(qid)

    drafts = list_all()
    path = export_csv(drafts, filename="test_export.csv")
    assert os.path.isfile(path)
    assert path.endswith(".csv")

    with open(path, "r", encoding="utf-8-sig") as f:
        content = f.read()
    assert "draft_id" in content
    assert "account_handle" in content
    assert "caption_text" in content
    assert "Texto para CSV" in content


def test_export_json():
    _setup()
    qid = "export_json_test"
    _queue_items[qid] = MockQueueItem(qid, "lucastigrereal", "caption_ready")
    _captions[qid] = MockCaption("cap_json", qid, "approved",
                                  caption_text="Texto para JSON")

    builder = DraftBuilder(_queue_provider, _caption_provider)
    builder.create(qid)

    drafts = list_all()
    path = export_json(drafts, filename="test_export.json")
    assert os.path.isfile(path)
    assert path.endswith(".json")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["caption_text"] == "Texto para JSON"
    assert "hashtags" in data[0]


def test_create_preserves_caption_data():
    """Verifica que caption_text, hashtags e cta são copiados do caption."""
    _setup()
    qid = "data_preserve_test"
    _queue_items[qid] = MockQueueItem(qid, "lucastigrereal", "caption_ready")
    _captions[qid] = MockCaption("cap_data", qid, "approved",
                                  caption_text="Legenda preservada",
                                  hashtags=["#tag_a", "#tag_b", "#tag_c"],
                                  cta="CTA preservado")

    builder = DraftBuilder(_queue_provider, _caption_provider)
    draft, _ = builder.create(qid)

    assert draft.caption_text == "Legenda preservada"
    assert draft.hashtags == ["#tag_a", "#tag_b", "#tag_c"]
    assert draft.cta == "CTA preservado"
    assert draft.post_type == "feed"
    assert draft.platform == "instagram"


def test_create_without_caption_provider():
    """Sem provider de caption, retorna erro."""
    _setup()
    qid = "no_provider_test"
    _queue_items[qid] = MockQueueItem(qid, "lucastigrereal", "caption_ready")

    builder = DraftBuilder(_queue_provider, lambda q: None)
    draft, errors = builder.create(qid)
    assert draft is None
    assert len(errors) > 0
