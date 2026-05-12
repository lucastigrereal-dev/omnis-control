"""Output Generator selector — pick generator by output type."""
from __future__ import annotations

from .models import OutputGeneratorDefinition, OutputGeneratorSelection, SelectionStatus, GeneratorStatus
from .registry import OutputGeneratorRegistry
from .errors import NoGeneratorForTypeError


def select_generator(
    output_type: str,
    registry: OutputGeneratorRegistry | None = None,
) -> OutputGeneratorSelection:
    """Select best generator for the given output type.

    Rules:
    - active generators are preferred
    - planned-only returns PLANNED_ONLY status
    - no match at all returns NO_GENERATOR status
    """
    if registry is None:
        registry = OutputGeneratorRegistry()

    active: list[OutputGeneratorDefinition] = []
    planned: list[OutputGeneratorDefinition] = []

    for gen in registry.list_all():
        if output_type in gen.output_types:
            if gen.status == GeneratorStatus.ACTIVE:
                active.append(gen)
            else:
                planned.append(gen)

    if active:
        gen = active[0]
        warnings = [f"Multiple active generators for '{output_type}'"] if len(active) > 1 else []
        return OutputGeneratorSelection(
            output_type=output_type,
            selected_generator_id=gen.generator_id,
            status=SelectionStatus.SELECTED,
            warnings=warnings,
        )

    if planned:
        gen_ids = [g.generator_id for g in planned]
        return OutputGeneratorSelection(
            output_type=output_type,
            selected_generator_id=None,
            status=SelectionStatus.PLANNED_ONLY,
            warnings=[f"Only planned generators for '{output_type}': {', '.join(gen_ids)}"],
        )

    return OutputGeneratorSelection(
        output_type=output_type,
        selected_generator_id=None,
        status=SelectionStatus.NO_GENERATOR,
        blockers=[f"No generator registered for '{output_type}'"],
    )
