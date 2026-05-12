"""Writer Service — orchestrates output generation for work orders."""
from __future__ import annotations

import json
from pathlib import Path

from src.output_generator.errors import GeneratorNotFoundError, NoGeneratorForTypeError
from src.output_generator.markdown_writer import write_markdown_output
from src.output_generator.csv_writer import write_csv_output
from src.output_generator.json_writer import write_json_output, write_spec_output
from src.output_generator.models import GeneratedOutput, GeneratedOutputStatus
from src.output_generator.registry import OutputGeneratorRegistry
from src.output_generator.selector import select_generator
from src.work_order.models import WorkOrder


class OutputWriterService:
    """Load work order, select generator, invoke writer, return GeneratedOutput."""

    def __init__(
        self,
        work_orders_root: Path | None = None,
        outputs_root: Path | None = None,
        registry: OutputGeneratorRegistry | None = None,
    ):
        self.work_orders_root = work_orders_root or Path("exports/work_orders")
        self.outputs_root = outputs_root or Path("exports/generated_outputs")
        self.registry = registry or OutputGeneratorRegistry()

    def write(self, work_order_id: str) -> GeneratedOutput:
        wo = self._load_work_order(work_order_id)

        md_contracts = [c for c in wo.contracts if c.output_type.value == "markdown"]
        if not md_contracts:
            return GeneratedOutput(
                output_id="",
                work_order_id=work_order_id,
                output_type="markdown",
                generator_id="",
                file_path="",
                status=GeneratedOutputStatus.UNSUPPORTED,
                created_at="",
                blockers=[f"Work order {work_order_id} has no markdown contract"],
            )

        selection = select_generator("markdown", registry=self.registry)
        if selection.status.value not in ("selected",):
            return GeneratedOutput(
                output_id="",
                work_order_id=work_order_id,
                output_type="markdown",
                generator_id=selection.selected_generator_id or "",
                file_path="",
                status=GeneratedOutputStatus.BLOCKED,
                created_at="",
                blockers=selection.blockers,
                warnings=selection.warnings,
            )

        try:
            gen_def = self.registry.get(selection.selected_generator_id)
        except GeneratorNotFoundError:
            return GeneratedOutput(
                output_id="",
                work_order_id=work_order_id,
                output_type="markdown",
                generator_id="",
                file_path="",
                status=GeneratedOutputStatus.FAILED,
                created_at="",
                blockers=["Generator not found after selection"],
            )

        return write_markdown_output(
            wo,
            self.outputs_root,
            generator_id=gen_def.generator_id,
        )

    def write_json(self, work_order_id: str) -> GeneratedOutput:
        wo = self._load_work_order(work_order_id)

        json_contracts = [c for c in wo.contracts if c.output_type.value == "json"]
        if not json_contracts:
            return GeneratedOutput(
                output_id="",
                work_order_id=work_order_id,
                output_type="json",
                generator_id="",
                file_path="",
                status=GeneratedOutputStatus.UNSUPPORTED,
                created_at="",
                blockers=[f"Work order {work_order_id} has no json contract"],
            )

        selection = select_generator("json", registry=self.registry)
        if selection.status.value not in ("selected",):
            return GeneratedOutput(
                output_id="",
                work_order_id=work_order_id,
                output_type="json",
                generator_id=selection.selected_generator_id or "",
                file_path="",
                status=GeneratedOutputStatus.BLOCKED,
                created_at="",
                blockers=selection.blockers,
                warnings=selection.warnings,
            )

        try:
            gen_def = self.registry.get(selection.selected_generator_id)
        except GeneratorNotFoundError:
            return GeneratedOutput(
                output_id="",
                work_order_id=work_order_id,
                output_type="json",
                generator_id="",
                file_path="",
                status=GeneratedOutputStatus.FAILED,
                created_at="",
                blockers=["Generator not found after selection"],
            )

        return write_json_output(
            wo,
            self.outputs_root,
            generator_id=gen_def.generator_id,
        )

    def write_spec(self, work_order_id: str) -> GeneratedOutput:
        wo = self._load_work_order(work_order_id)

        valid_spec_types = {"technical_spec", "app_spec", "data_model"}
        spec_contracts = [c for c in wo.contracts if c.output_type.value in valid_spec_types]
        if not spec_contracts:
            return GeneratedOutput(
                output_id="",
                work_order_id=work_order_id,
                output_type="technical_spec",
                generator_id="",
                file_path="",
                status=GeneratedOutputStatus.UNSUPPORTED,
                created_at="",
                blockers=[f"Work order {work_order_id} has no spec contract"],
            )

        spec_type = spec_contracts[0].output_type.value
        selection = select_generator(spec_type, registry=self.registry)
        if selection.status.value not in ("selected",):
            return GeneratedOutput(
                output_id="",
                work_order_id=work_order_id,
                output_type=spec_type,
                generator_id=selection.selected_generator_id or "",
                file_path="",
                status=GeneratedOutputStatus.BLOCKED,
                created_at="",
                blockers=selection.blockers,
                warnings=selection.warnings,
            )

        try:
            gen_def = self.registry.get(selection.selected_generator_id)
        except GeneratorNotFoundError:
            return GeneratedOutput(
                output_id="",
                work_order_id=work_order_id,
                output_type=spec_type,
                generator_id="",
                file_path="",
                status=GeneratedOutputStatus.FAILED,
                created_at="",
                blockers=["Generator not found after selection"],
            )

        return write_spec_output(
            wo,
            self.outputs_root,
            generator_id=gen_def.generator_id,
        )

    def write_csv(self, work_order_id: str, *, table_type: str = "list") -> GeneratedOutput:
        wo = self._load_work_order(work_order_id)

        csv_contracts = [c for c in wo.contracts if c.output_type.value == "csv"]
        if not csv_contracts:
            return GeneratedOutput(
                output_id="",
                work_order_id=work_order_id,
                output_type="csv",
                generator_id="",
                file_path="",
                status=GeneratedOutputStatus.UNSUPPORTED,
                created_at="",
                blockers=[f"Work order {work_order_id} has no csv contract"],
            )

        selection = select_generator("csv", registry=self.registry)
        if selection.status.value not in ("selected",):
            return GeneratedOutput(
                output_id="",
                work_order_id=work_order_id,
                output_type="csv",
                generator_id=selection.selected_generator_id or "",
                file_path="",
                status=GeneratedOutputStatus.BLOCKED,
                created_at="",
                blockers=selection.blockers,
                warnings=selection.warnings,
            )

        try:
            gen_def = self.registry.get(selection.selected_generator_id)
        except GeneratorNotFoundError:
            return GeneratedOutput(
                output_id="",
                work_order_id=work_order_id,
                output_type="csv",
                generator_id="",
                file_path="",
                status=GeneratedOutputStatus.FAILED,
                created_at="",
                blockers=["Generator not found after selection"],
            )

        return write_csv_output(
            wo,
            self.outputs_root,
            generator_id=gen_def.generator_id,
            table_type=table_type,
        )

    def _load_work_order(self, work_order_id: str) -> WorkOrder:
        wo_dir = self.work_orders_root / work_order_id
        manifest = wo_dir / "work_order.json"
        if not manifest.exists():
            raise FileNotFoundError(f"Work order not found: {work_order_id} (expected at {manifest})")
        data = json.loads(manifest.read_text(encoding="utf-8"))
        return WorkOrder.from_dict(data)
