"""Tests for WorkOrder validator."""
from __future__ import annotations

import pytest

from src.work_order.models import (
    OutputContract,
    OutputEntry,
    OutputType,
    WorkOrder,
    WorkOrderStatus,
    make_work_order_id,
)
from src.work_order.validator import (
    ValidationResult,
    validate_work_order,
    _validate_required_fields,
    _validate_contracts,
    _validate_outputs,
)


def make_valid_wo(**overrides) -> WorkOrder:
    kwargs = dict(
        work_order_id=make_work_order_id(),
        graph_step_id="step_abc",
        graph_run_id="grun_xyz",
        role="copywriter",
        step_label="Criar legenda",
        status=WorkOrderStatus.DRAFT,
        contracts=[
            OutputContract("c01", OutputType.MARKDOWN, "Texto do post"),
        ],
    )
    kwargs.update(overrides)
    return WorkOrder(**kwargs)


class TestValidationResult:
    def test_starts_valid(self):
        r = ValidationResult(is_valid=True)
        assert r.is_valid is True
        assert r.errors == []
        assert r.warnings == []

    def test_add_error_sets_invalid(self):
        r = ValidationResult(is_valid=True)
        r.add_error("bad field")
        assert r.is_valid is False
        assert len(r.errors) == 1

    def test_add_warning_does_not_invalidate(self):
        r = ValidationResult(is_valid=True)
        r.add_warning("minor issue")
        assert r.is_valid is True
        assert len(r.warnings) == 1


class TestValidateRequiredFields:
    def test_valid_wo_passes(self):
        wo = make_valid_wo()
        result = ValidationResult(is_valid=True)
        _validate_required_fields(wo, result)
        assert result.is_valid is True
        assert result.errors == []

    def test_missing_work_order_id(self):
        wo = make_valid_wo(work_order_id="")
        result = ValidationResult(is_valid=True)
        _validate_required_fields(wo, result)
        assert result.is_valid is False
        assert any("work_order_id" in e for e in result.errors)

    def test_wrong_id_prefix(self):
        wo = make_valid_wo(work_order_id="bad_123")
        result = ValidationResult(is_valid=True)
        _validate_required_fields(wo, result)
        assert result.is_valid is False
        assert any("must start with 'wo_'" in e for e in result.errors)

    def test_missing_graph_step_id(self):
        wo = make_valid_wo(graph_step_id="")
        result = ValidationResult(is_valid=True)
        _validate_required_fields(wo, result)
        assert any("graph_step_id" in e for e in result.errors)

    def test_missing_role(self):
        wo = make_valid_wo(role="")
        result = ValidationResult(is_valid=True)
        _validate_required_fields(wo, result)
        assert any("role" in e for e in result.errors)


class TestValidateContracts:
    def test_no_contracts_adds_warning(self):
        wo = make_valid_wo(contracts=[])
        result = ValidationResult(is_valid=True)
        _validate_contracts(wo, result)
        assert any("no output contracts" in w for w in result.warnings)

    def test_duplicate_contract_id(self):
        wo = make_valid_wo(contracts=[
            OutputContract("c01", OutputType.MARKDOWN, "A"),
            OutputContract("c01", OutputType.JSON, "B"),
        ])
        result = ValidationResult(is_valid=True)
        _validate_contracts(wo, result)
        assert any("Duplicate contract_id" in e for e in result.errors)

    def test_negative_min_count(self):
        wo = make_valid_wo(contracts=[
            OutputContract("c01", OutputType.MARKDOWN, "A", min_count=-1),
        ])
        result = ValidationResult(is_valid=True)
        _validate_contracts(wo, result)
        assert any("min_count cannot be negative" in e for e in result.errors)

    def test_max_less_than_min(self):
        wo = make_valid_wo(contracts=[
            OutputContract("c01", OutputType.MARKDOWN, "A", min_count=3, max_count=2),
        ])
        result = ValidationResult(is_valid=True)
        _validate_contracts(wo, result)
        assert any("max_count" in e for e in result.errors)

    def test_missing_description_adds_warning(self):
        wo = make_valid_wo(contracts=[
            OutputContract("c01", OutputType.MARKDOWN, ""),
        ])
        result = ValidationResult(is_valid=True)
        _validate_contracts(wo, result)
        assert any("no description" in w for w in result.warnings)


class TestValidateOutputs:
    def test_outputs_in_draft_status_triggers_warning(self):
        wo = make_valid_wo(status=WorkOrderStatus.DRAFT, outputs=[
            OutputEntry("out_a", OutputType.MARKDOWN, "c01"),
        ])
        result = ValidationResult(is_valid=True)
        _validate_outputs(wo, result)
        assert any("has outputs but status is draft" in w for w in result.warnings)

    def test_duplicate_output_id(self):
        wo = make_valid_wo(status=WorkOrderStatus.OUTPUT_SUBMITTED, outputs=[
            OutputEntry("out_a", OutputType.MARKDOWN, "c01"),
            OutputEntry("out_a", OutputType.JSON, "c01"),
        ])
        result = ValidationResult(is_valid=True)
        _validate_outputs(wo, result)
        assert any("Duplicate output_id" in e for e in result.errors)

    def test_output_references_unknown_contract(self):
        wo = make_valid_wo(
            contracts=[OutputContract("c01", OutputType.MARKDOWN, "Texto")],
            status=WorkOrderStatus.OUTPUT_SUBMITTED,
            outputs=[OutputEntry("out_a", OutputType.MARKDOWN, "c02")],
        )
        result = ValidationResult(is_valid=True)
        _validate_outputs(wo, result)
        assert any("references unknown contract" in e for e in result.errors)

    def test_empty_outputs_ok_for_submitted(self):
        wo = make_valid_wo(status=WorkOrderStatus.OUTPUT_SUBMITTED, outputs=[])
        result = ValidationResult(is_valid=True)
        _validate_outputs(wo, result)
        assert result.is_valid is True


class TestFullValidation:
    def test_valid_work_order_passes_full(self):
        wo = make_valid_wo()
        result = validate_work_order(wo)
        assert result.is_valid is True

    def test_full_validation_catches_multiple_issues(self):
        wo = make_valid_wo(
            work_order_id="bad_id",
            graph_step_id="",
            contracts=[
                OutputContract("c01", OutputType.MARKDOWN, "Texto", min_count=-1),
                OutputContract("c01", OutputType.JSON, "Dados"),
            ],
        )
        result = validate_work_order(wo)
        assert result.is_valid is False
        assert len(result.errors) >= 3  # prefix + empty step + dup contract + negative min
