"""Tests for P9.1 — Local Execution Contracts."""
from __future__ import annotations

import pytest

from src.work_order.models import (
    OutputContract,
    OutputEntry,
    OutputType,
    WorkOrder,
    WorkOrderStatus,
    make_output_id,
    make_work_order_id,
)
from src.work_order.output_contract import ContentRule, OutputContractSpec
from src.work_order.contract_validator import (
    ContractValidationResult,
    all_contracts_satisfied,
    get_contract_specs_for_role,
    get_missing_contracts,
    validate_contracts_for_work_order,
)


# ── ContentRule ───────────────────────────────────────────────────

class TestContentRule:
    def test_required_rule_passes(self):
        r = ContentRule("r01", "title", "required")
        ok, msg = r.validate({"title": "Hello"})
        assert ok is True

    def test_required_rule_fails(self):
        r = ContentRule("r01", "title", "required")
        ok, msg = r.validate({"title": ""})
        assert ok is False

    def test_required_rule_fails_missing_key(self):
        r = ContentRule("r01", "title", "required")
        ok, msg = r.validate({"body": "text"})
        assert ok is False

    def test_min_length_passes(self):
        r = ContentRule("r01", "body", "min_length", value=10)
        ok, msg = r.validate({"body": "a" * 15})
        assert ok is True

    def test_min_length_fails(self):
        r = ContentRule("r01", "body", "min_length", value=10)
        ok, msg = r.validate({"body": "abc"})
        assert ok is False

    def test_min_length_none_value(self):
        r = ContentRule("r01", "body", "min_length", value=10)
        ok, msg = r.validate({"body": None})
        assert ok is False

    def test_max_length_passes(self):
        r = ContentRule("r01", "body", "max_length", value=100)
        ok, msg = r.validate({"body": "a" * 50})
        assert ok is True

    def test_max_length_fails(self):
        r = ContentRule("r01", "body", "max_length", value=10)
        ok, msg = r.validate({"body": "a" * 20})
        assert ok is False

    def test_pattern_passes(self):
        r = ContentRule("r01", "email", "pattern", value=r"^.+@.+\..+$")
        ok, msg = r.validate({"email": "test@example.com"})
        assert ok is True

    def test_pattern_fails(self):
        r = ContentRule("r01", "email", "pattern", value=r"^.+@.+\..+$")
        ok, msg = r.validate({"email": "invalid"})
        assert ok is False

    def test_enum_passes(self):
        r = ContentRule("r01", "status", "enum", value=["draft", "ready", "done"])
        ok, msg = r.validate({"status": "done"})
        assert ok is True

    def test_enum_fails(self):
        r = ContentRule("r01", "status", "enum", value=["draft", "ready", "done"])
        ok, msg = r.validate({"status": "invalid"})
        assert ok is False

    def test_rule_to_dict(self):
        r = ContentRule("r01", "title", "required")
        d = r.to_dict()
        assert d["rule_id"] == "r01"
        assert d["field"] == "title"

    def test_rule_from_dict(self):
        d = {"rule_id": "r01", "field": "title", "rule_type": "required"}
        r = ContentRule.from_dict(d)
        assert r.rule_id == "r01"

    def test_validates_str_content(self):
        r = ContentRule("r01", "text", "min_length", value=5)
        ok, msg = r.validate("hello world")
        assert ok is True


# ── OutputContractSpec ────────────────────────────────────────────

class TestOutputContractSpec:
    def test_create_spec(self):
        spec = OutputContractSpec(
            contract_id="c01",
            output_type=OutputType.MARKDOWN,
            description="Legenda",
            content_rules=[ContentRule("r01", "title", "required")],
        )
        assert spec.contract_id == "c01"
        assert spec.required is True

    def test_validate_output_with_rules_passes(self):
        spec = OutputContractSpec(
            contract_id="c01",
            output_type=OutputType.MARKDOWN,
            description="Legenda",
            content_rules=[ContentRule("r01", "title", "required")],
        )
        ok, failures = spec.validate_output({"title": "Meu Post"})
        assert ok is True
        assert failures == []

    def test_validate_output_with_rules_fails(self):
        spec = OutputContractSpec(
            contract_id="c01",
            output_type=OutputType.MARKDOWN,
            description="Legenda",
            content_rules=[ContentRule("r01", "title", "required")],
        )
        ok, failures = spec.validate_output({"title": ""})
        assert ok is False
        assert len(failures) == 1

    def test_validate_required_output_missing(self):
        spec = OutputContractSpec(
            contract_id="c01",
            output_type=OutputType.MARKDOWN,
            description="Legenda",
            required=True,
        )
        ok, failures = spec.validate_output(None)
        assert ok is False

    def test_validate_optional_output_missing(self):
        spec = OutputContractSpec(
            contract_id="c01",
            output_type=OutputType.MARKDOWN,
            description="Extra",
            required=False,
        )
        ok, failures = spec.validate_output(None)
        assert ok is True

    def test_matches_type(self):
        spec = OutputContractSpec("c01", OutputType.MARKDOWN, "Texto")
        assert spec.matches_type(OutputType.MARKDOWN) is True
        assert spec.matches_type(OutputType.JSON) is False

    def test_to_dict(self):
        spec = OutputContractSpec("c01", OutputType.MARKDOWN, "Texto",
            content_rules=[ContentRule("r01", "title", "required")])
        d = spec.to_dict()
        assert d["contract_id"] == "c01"
        assert len(d["content_rules"]) == 1

    def test_from_dict(self):
        d = {
            "contract_id": "c02", "output_type": "json", "description": "Dados",
            "content_rules": [{"rule_id": "r01", "field": "count", "rule_type": "min_length", "value": 1}],
        }
        spec = OutputContractSpec.from_dict(d)
        assert spec.output_type == OutputType.JSON
        assert len(spec.content_rules) == 1


# ── Contract Validator ────────────────────────────────────────────

def make_wo_with_contracts(**overrides) -> WorkOrder:
    kwargs = dict(
        work_order_id=make_work_order_id(),
        graph_step_id="step_abc",
        graph_run_id="grun_xyz",
        role="copywriter",
        step_label="Criar legenda",
        status=WorkOrderStatus.OUTPUT_PENDING,
        contracts=[
            OutputContract("c01", OutputType.MARKDOWN, "Legenda", required=True, min_count=1, max_count=1),
        ],
    )
    kwargs.update(overrides)
    return WorkOrder(**kwargs)


class TestValidateContractsForWorkOrder:
    def test_single_contract_satisfied_by_output(self):
        wo = make_wo_with_contracts(outputs=[
            OutputEntry("out_a", OutputType.MARKDOWN, "c01"),
        ])
        results = validate_contracts_for_work_order(wo)
        assert len(results) == 1
        assert results[0].is_satisfied is True
        assert results[0].output_count == 1

    def test_contract_not_satisfied_missing_output(self):
        wo = make_wo_with_contracts(outputs=[])
        results = validate_contracts_for_work_order(wo)
        assert results[0].is_satisfied is False
        assert "Need 1 outputs" in results[0].failures[0]

    def test_contract_wrong_output_type(self):
        wo = make_wo_with_contracts(outputs=[
            OutputEntry("out_a", OutputType.JSON, "c01"),
        ])
        results = validate_contracts_for_work_order(wo)
        assert results[0].is_satisfied is False
        assert any("!= contract type" in f for f in results[0].failures)

    def test_contract_too_many_outputs(self):
        wo = make_wo_with_contracts(
            contracts=[OutputContract("c01", OutputType.MARKDOWN, "A", max_count=1)],
            outputs=[
                OutputEntry("out_a", OutputType.MARKDOWN, "c01"),
                OutputEntry("out_b", OutputType.MARKDOWN, "c01"),
            ],
        )
        results = validate_contracts_for_work_order(wo)
        assert results[0].is_satisfied is False

    def test_multiple_contracts(self):
        wo = make_wo_with_contracts(
            contracts=[
                OutputContract("c01", OutputType.MARKDOWN, "Legenda", min_count=1),
                OutputContract("c02", OutputType.JSON, "Meta", required=False, min_count=0),
            ],
            outputs=[
                OutputEntry("out_a", OutputType.MARKDOWN, "c01"),
            ],
        )
        results = validate_contracts_for_work_order(wo)
        assert results[0].is_satisfied is True
        assert results[1].is_satisfied is True

    def test_with_content_rules_spec(self):
        wo = make_wo_with_contracts(
            contracts=[OutputContract("c01", OutputType.MARKDOWN, "Legenda", min_count=1)],
            outputs=[OutputEntry("out_a", OutputType.MARKDOWN, "c01", file_path="post.md")],
        )
        spec = OutputContractSpec("c01", OutputType.MARKDOWN, "Legenda",
            content_rules=[ContentRule("r01", "output_id", "required")])
        results = validate_contracts_for_work_order(wo, contract_specs=[spec])
        assert results[0].is_satisfied is True


class TestHelperFunctions:
    def test_all_contracts_satisfied(self):
        results = [
            ContractValidationResult("c01", True, 1, 1, 1),
            ContractValidationResult("c02", True, 1, 1, 1),
        ]
        assert all_contracts_satisfied(results) is True

    def test_all_contracts_not_satisfied(self):
        results = [
            ContractValidationResult("c01", True, 1, 1, 1),
            ContractValidationResult("c02", False, 0, 1, 1, ["missing"]),
        ]
        assert all_contracts_satisfied(results) is False

    def test_get_missing_contracts(self):
        results = [
            ContractValidationResult("c01", True, 1, 1, 1),
            ContractValidationResult("c02", False, 0, 1, 1, ["missing"]),
            ContractValidationResult("c03", False, 0, 2, 2, ["need 2"]),
        ]
        missing = get_missing_contracts(results)
        assert missing == ["c02", "c03"]

    def test_contract_validation_result_remaining(self):
        r = ContractValidationResult("c01", False, 1, 3, 3)
        assert r.remaining == 2


class TestGetContractSpecsForRole:
    def test_known_role_returns_specs(self):
        specs = get_contract_specs_for_role("copywriter")
        assert len(specs) >= 1
        assert specs[0].output_type == OutputType.MARKDOWN
        assert len(specs[0].content_rules) >= 1

    def test_unknown_role_returns_empty(self):
        specs = get_contract_specs_for_role("nonexistent")
        assert specs == []

    def test_creative_director_accepts_multiple(self):
        specs = get_contract_specs_for_role("creative_director")
        assert specs[0].accepts_multiple is True
        assert specs[0].max_count == 3
