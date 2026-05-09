"""Shared fixtures for asset_assignment tests."""
import pytest
from unittest.mock import MagicMock

import src.asset_assignment.service as svc_mod


FAKE_QUEUE_ITEM = MagicMock()
FAKE_QUEUE_ITEM.queue_id = "0b79aa1c"
FAKE_QUEUE_ITEM.account_handle = "afamiliatigrereal"
FAKE_QUEUE_ITEM.status = "caption_ready"
FAKE_QUEUE_ITEM.asset_id = None
FAKE_QUEUE_ITEM.date = "2026-05-10"

FAKE_QUEUE_ITEM_WITH_ASSET = MagicMock()
FAKE_QUEUE_ITEM_WITH_ASSET.queue_id = "0b79aa1c"
FAKE_QUEUE_ITEM_WITH_ASSET.account_handle = "afamiliatigrereal"
FAKE_QUEUE_ITEM_WITH_ASSET.status = "caption_ready"
FAKE_QUEUE_ITEM_WITH_ASSET.asset_id = "mock_test_001"
FAKE_QUEUE_ITEM_WITH_ASSET.date = "2026-05-10"

FAKE_ASSET = MagicMock()
FAKE_ASSET.asset_id = "mock_test_001"
FAKE_ASSET.format = "carousel"
FAKE_ASSET.source_path = "[MOCK] test_asset.jpg"

FAKE_DRAFT = MagicMock()
FAKE_DRAFT.queue_id = "0b79aa1c"
FAKE_DRAFT.draft_id = "1d482d82"
FAKE_DRAFT.status = "approved"
