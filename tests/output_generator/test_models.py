"""Tests for OutputGenerator models."""
from __future__ import annotations

import pytest

from src.output_generator.models import (
    GeneratorStatus,
    OutputGeneratorDefinition,
    OutputGeneratorSelection,
    SelectionStatus,
)


class TestGeneratorStatus:
    def test_active_and_planned_defined(self):
        assert GeneratorStatus.ACTIVE == "active"
        assert GeneratorStatus.PLANNED == "planned"

    def test_all_statuses(self):
        assert set(GeneratorStatus.__members__) == {"ACTIVE", "PLANNED"}


class TestSelectionStatus:
    def test_all_selection_statuses(self):
        expected = {"SELECTED", "NO_GENERATOR", "PLANNED_ONLY", "BLOCKED"}
        assert set(SelectionStatus.__members__) == expected


class TestOutputGeneratorDefinition:
    def test_default_values(self):
        gen = OutputGeneratorDefinition(generator_id="test", name="Test")
        assert gen.generator_id == "test"
        assert gen.name == "Test"
        assert gen.output_types == []
        assert gen.mode == "deterministic"
        assert gen.risk_level == "low"
        assert gen.status == GeneratorStatus.ACTIVE
        assert gen.description == ""

    def test_custom_values(self):
        gen = OutputGeneratorDefinition(
            generator_id="writer",
            name="Writer",
            output_types=["markdown"],
            mode="deterministic",
            risk_level="medium",
            status=GeneratorStatus.PLANNED,
            description="Writes stuff",
        )
        assert gen.output_types == ["markdown"]
        assert gen.risk_level == "medium"
        assert gen.status == GeneratorStatus.PLANNED


class TestOutputGeneratorSelection:
    def test_no_generator_default(self):
        sel = OutputGeneratorSelection(output_type="json")
        assert sel.output_type == "json"
        assert sel.selected_generator_id is None
        assert sel.status == SelectionStatus.NO_GENERATOR
        assert sel.warnings == []
        assert sel.blockers == []

    def test_selected_with_warnings(self):
        sel = OutputGeneratorSelection(
            output_type="markdown",
            selected_generator_id="md_writer",
            status=SelectionStatus.SELECTED,
            warnings=["Multiple active generators"],
        )
        assert sel.status == SelectionStatus.SELECTED
        assert sel.selected_generator_id == "md_writer"

    def test_blocked(self):
        sel = OutputGeneratorSelection(
            output_type="zip",
            status=SelectionStatus.BLOCKED,
            blockers=["No registered generator"],
        )
        assert sel.status == SelectionStatus.BLOCKED

    def test_to_dict(self):
        sel = OutputGeneratorSelection(
            output_type="markdown",
            selected_generator_id="md_writer",
            status=SelectionStatus.SELECTED,
            warnings=["w1"],
            blockers=["b1"],
        )
        d = sel.to_dict()
        assert d["output_type"] == "markdown"
        assert d["selected_generator_id"] == "md_writer"
        assert d["status"] == "selected"
        assert "w1" in d["warnings"]
        assert "b1" in d["blockers"]
