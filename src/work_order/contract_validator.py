"""Contract Validator — validates work order outputs against contract specs."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.work_order.models import OutputEntry, OutputType, WorkOrder
from src.work_order.output_contract import ContentRule, OutputContractSpec


@dataclass
class ContractValidationResult:
    """Result of validating outputs against contracts."""
    contract_id: str
    is_satisfied: bool
    output_count: int = 0
    min_required: int = 0
    max_allowed: int = 0
    failures: list[str] = field(default_factory=list)
    satisfied_by: list[str] = field(default_factory=list)  # output_ids

    @property
    def remaining(self) -> int:
        return max(0, self.min_required - self.output_count)


def validate_contracts_for_work_order(
    wo: WorkOrder,
    contract_specs: list[OutputContractSpec] | None = None,
) -> list[ContractValidationResult]:
    """Validate all outputs in a work order against their contract specs."""
    results: list[ContractValidationResult] = []

    specs_by_id: dict[str, OutputContractSpec] = {}
    if contract_specs:
        specs_by_id = {s.contract_id: s for s in contract_specs}

    outputs_by_contract: dict[str, list[OutputEntry]] = {}
    for o in wo.outputs:
        outputs_by_contract.setdefault(o.contract_id, []).append(o)

    for contract in wo.contracts:
        spec = specs_by_id.get(contract.contract_id)
        entries = outputs_by_contract.get(contract.contract_id, [])
        result = ContractValidationResult(
            contract_id=contract.contract_id,
            is_satisfied=False,
            output_count=len(entries),
            min_required=contract.min_count,
            max_allowed=contract.max_count,
            satisfied_by=[e.output_id for e in entries],
        )

        if len(entries) < contract.min_count:
            result.failures.append(
                f"Need {contract.min_count} outputs, got {len(entries)}"
            )

        if len(entries) > contract.max_count:
            result.failures.append(
                f"Max {contract.max_count} outputs, got {len(entries)}"
            )

        for entry in entries:
            if entry.output_type != contract.output_type:
                result.failures.append(
                    f"Output {entry.output_id} type {entry.output_type.value} "
                    f"!= contract type {contract.output_type.value}"
                )

            if spec and spec.content_rules:
                ok, rule_failures = spec.validate_output(_entry_to_dict(entry))
                if not ok:
                    result.failures.extend(rule_failures)

        result.is_satisfied = len(result.failures) == 0
        results.append(result)

    return results


def all_contracts_satisfied(results: list[ContractValidationResult]) -> bool:
    return all(r.is_satisfied for r in results)


def get_missing_contracts(results: list[ContractValidationResult]) -> list[str]:
    return [r.contract_id for r in results if not r.is_satisfied]


def _entry_to_dict(entry: OutputEntry) -> dict:
    return {
        "output_id": entry.output_id,
        "output_type": entry.output_type.value,
        "contract_id": entry.contract_id,
        "file_path": entry.file_path,
    }


# ── Contract spec templates by role ──────────────────────────────

_ROLE_CONTRACT_SPECS: dict[str, list[dict]] = {
    "copywriter": [
        {
            "contract_id": "contract_00",
            "output_type": "markdown",
            "description": "Legenda final com hashtags",
            "required": True,
            "min_count": 1,
            "max_count": 1,
            "content_rules": [
                {"rule_id": "r01", "field": "title", "rule_type": "required", "value": "", "message": "Titulo obrigatorio"},
                {"rule_id": "r02", "field": "body", "rule_type": "min_length", "value": "50", "message": "Corpo deve ter pelo menos 50 caracteres"},
            ],
        },
    ],
    "creative_director": [
        {
            "contract_id": "contract_00",
            "output_type": "image_asset",
            "description": "Imagem final 1080x1080",
            "required": True,
            "min_count": 1,
            "max_count": 3,
            "accepts_multiple": True,
            "content_rules": [
                {"rule_id": "r01", "field": "alt_text", "rule_type": "required", "value": "", "message": "Alt text obrigatorio"},
            ],
        },
    ],
}


def get_contract_specs_for_role(role: str) -> list[OutputContractSpec]:
    """Get contract specs for a role from templates."""
    specs: list[OutputContractSpec] = []
    templates = _ROLE_CONTRACT_SPECS.get(role, [])

    for t in templates:
        rules = [ContentRule(
            rule_id=r["rule_id"],
            field=r["field"],
            rule_type=r["rule_type"],
            value=r.get("value", ""),
            message=r.get("message", ""),
        ) for r in t.get("content_rules", [])]

        specs.append(OutputContractSpec(
            contract_id=t["contract_id"],
            output_type=OutputType(t["output_type"]),
            description=t["description"],
            required=t.get("required", True),
            min_count=t.get("min_count", 1),
            max_count=t.get("max_count", 1),
            content_rules=rules,
            accepts_multiple=t.get("accepts_multiple", False),
        ))

    return specs
