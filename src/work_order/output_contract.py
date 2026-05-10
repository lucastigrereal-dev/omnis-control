"""Output Contract definitions — typed contracts for work order outputs."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.work_order.models import OutputType


@dataclass
class ContentRule:
    """A validation rule for output content."""
    rule_id: str
    field: str  # e.g. "title", "hashtags", "alt_text"
    rule_type: str  # "required", "min_length", "max_length", "pattern", "enum"
    value: str | int | list[str] = ""
    message: str = ""

    def validate(self, content: dict | str) -> tuple[bool, str]:
        if isinstance(content, dict):
            field_val = content.get(self.field)
        else:
            field_val = content

        if self.rule_type == "required":
            if field_val is None or field_val == "" or (isinstance(field_val, list) and len(field_val) == 0):
                return False, self.message or f"{self.field} is required"
            return True, ""

        if self.rule_type == "min_length":
            if field_val is None or (isinstance(field_val, (str, list)) and len(field_val) < int(self.value)):
                return False, self.message or f"{self.field} min length is {self.value}"
            return True, ""

        if self.rule_type == "max_length":
            if field_val and isinstance(field_val, (str, list)) and len(field_val) > int(self.value):
                return False, self.message or f"{self.field} max length is {self.value}"
            return True, ""

        if self.rule_type == "pattern":
            import re
            if field_val and not re.match(str(self.value), str(field_val)):
                return False, self.message or f"{self.field} must match pattern {self.value}"
            return True, ""

        if self.rule_type == "enum":
            allowed = self.value if isinstance(self.value, list) else [self.value]
            if field_val and field_val not in allowed:
                return False, self.message or f"{self.field} must be one of {allowed}"
            return True, ""

        return True, ""

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "field": self.field,
            "rule_type": self.rule_type,
            "value": self.value,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ContentRule":
        return cls(
            rule_id=d["rule_id"],
            field=d["field"],
            rule_type=d["rule_type"],
            value=d.get("value", ""),
            message=d.get("message", ""),
        )


@dataclass
class OutputContractSpec:
    """Complete specification for a work order output contract."""
    contract_id: str
    output_type: OutputType
    description: str
    required: bool = True
    min_count: int = 1
    max_count: int = 1
    content_rules: list[ContentRule] = field(default_factory=list)
    accepts_multiple: bool = False

    def validate_output(self, content: dict | str | None = None) -> tuple[bool, list[str]]:
        """Validate content against all rules. Returns (passed, failures)."""
        failures: list[str] = []
        if content is None:
            if self.required:
                failures.append(f"Contract {self.contract_id}: output is required but not provided")
            return len(failures) == 0, failures

        for rule in self.content_rules:
            ok, msg = rule.validate(content)
            if not ok:
                failures.append(f"Rule {rule.rule_id}: {msg}")

        return len(failures) == 0, failures

    def matches_type(self, output_type: OutputType) -> bool:
        return self.output_type == output_type

    def to_dict(self) -> dict:
        return {
            "contract_id": self.contract_id,
            "output_type": self.output_type.value,
            "description": self.description,
            "required": self.required,
            "min_count": self.min_count,
            "max_count": self.max_count,
            "content_rules": [r.to_dict() for r in self.content_rules],
            "accepts_multiple": self.accepts_multiple,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "OutputContractSpec":
        return cls(
            contract_id=d["contract_id"],
            output_type=OutputType(d["output_type"]),
            description=d["description"],
            required=d.get("required", True),
            min_count=int(d.get("min_count", 1)),
            max_count=int(d.get("max_count", 1)),
            content_rules=[ContentRule.from_dict(r) for r in d.get("content_rules", [])],
            accepts_multiple=d.get("accepts_multiple", False),
        )
