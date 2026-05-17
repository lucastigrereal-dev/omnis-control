"""Test filesystem helpers for App Factory."""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest


@pytest.fixture
def app_factory_tmp_dir() -> Path:
    base = Path(".test_tmp") / "app_factory"
    path = base / uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    return path


@pytest.fixture
def tmp_path(app_factory_tmp_dir: Path) -> Path:
    return app_factory_tmp_dir
