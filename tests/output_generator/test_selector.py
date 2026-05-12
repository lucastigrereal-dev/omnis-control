"""Tests for OutputGenerator selector."""
from __future__ import annotations

import tempfile
import yaml
from pathlib import Path

from src.output_generator.models import SelectionStatus
from src.output_generator.registry import OutputGeneratorRegistry
from src.output_generator.selector import select_generator


def _make_registry(generators: dict) -> OutputGeneratorRegistry:
    config = {"generators": generators}
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    yaml.dump(config, f)
    f.close()
    return OutputGeneratorRegistry(config_path=Path(f.name))


def test_selects_active_generator():
    reg = _make_registry({
        "md": {"name": "MD", "output_types": ["markdown"], "status": "active"},
    })
    result = select_generator("markdown", registry=reg)
    assert result.status == SelectionStatus.SELECTED
    assert result.selected_generator_id == "md"


def test_prefers_first_active_when_multiple():
    reg = _make_registry({
        "a": {"name": "A", "output_types": ["markdown"], "status": "active"},
        "b": {"name": "B", "output_types": ["markdown"], "status": "active"},
    })
    result = select_generator("markdown", registry=reg)
    assert result.status == SelectionStatus.SELECTED
    assert result.selected_generator_id == "a"
    assert len(result.warnings) == 1


def test_planned_only_returns_planned_only():
    reg = _make_registry({
        "z": {"name": "Z", "output_types": ["html_preview"], "status": "planned"},
    })
    result = select_generator("html_preview", registry=reg)
    assert result.status == SelectionStatus.PLANNED_ONLY
    assert result.selected_generator_id is None


def test_no_match_returns_no_generator():
    reg = _make_registry({})
    result = select_generator("zip", registry=reg)
    assert result.status == SelectionStatus.NO_GENERATOR
    assert len(result.blockers) == 1


def test_active_wins_over_planned():
    reg = _make_registry({
        "planned_md": {
            "name": "P", "output_types": ["markdown"], "status": "planned",
        },
        "active_md": {
            "name": "A", "output_types": ["markdown"], "status": "active",
        },
    })
    result = select_generator("markdown", registry=reg)
    assert result.status == SelectionStatus.SELECTED
    assert result.selected_generator_id == "active_md"
