"""Output Generator registry — load from config YAML."""
from __future__ import annotations

from pathlib import Path

import yaml

from .models import OutputGeneratorDefinition, GeneratorStatus
from .errors import GeneratorNotFoundError


_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "output_generators.yaml"


class OutputGeneratorRegistry:
    """Load and query registered output generators."""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or _DEFAULT_CONFIG_PATH
        self._generators: dict[str, OutputGeneratorDefinition] = {}
        self._load()

    def _load(self) -> None:
        if not self.config_path.is_file():
            return
        raw = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
        entries = raw.get("generators", {})
        for gen_id, data in entries.items():
            if not isinstance(data, dict):
                continue
            status_str = data.get("status", "planned")
            try:
                status = GeneratorStatus(status_str)
            except ValueError:
                status = GeneratorStatus.PLANNED

            self._generators[gen_id] = OutputGeneratorDefinition(
                generator_id=gen_id,
                name=data.get("name", gen_id),
                output_types=data.get("output_types", []),
                mode=data.get("mode", "deterministic"),
                risk_level=data.get("risk_level", "low"),
                status=status,
                description=data.get("description", ""),
            )

    def list_all(self) -> list[OutputGeneratorDefinition]:
        return list(self._generators.values())

    def get(self, generator_id: str) -> OutputGeneratorDefinition:
        gen = self._generators.get(generator_id)
        if gen is None:
            raise GeneratorNotFoundError(f"Generator '{generator_id}' not found")
        return gen

    def count(self) -> int:
        return len(self._generators)
