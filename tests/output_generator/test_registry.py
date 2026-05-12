"""Tests for OutputGeneratorRegistry."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from src.output_generator.errors import GeneratorNotFoundError
from src.output_generator.models import GeneratorStatus
from src.output_generator.registry import OutputGeneratorRegistry


class TestOutputGeneratorRegistry:
    def test_loads_from_yaml(self):
        config = {
            "generators": {
                "test_writer": {
                    "name": "Test Writer",
                    "output_types": ["markdown"],
                    "mode": "deterministic",
                    "risk_level": "low",
                    "status": "active",
                    "description": "Test generator",
                },
            },
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(config, f)
            path = Path(f.name)

        try:
            registry = OutputGeneratorRegistry(config_path=path)
            assert registry.count() == 1
            gen = registry.get("test_writer")
            assert gen.name == "Test Writer"
            assert gen.output_types == ["markdown"]
            assert gen.status == GeneratorStatus.ACTIVE
        finally:
            path.unlink(missing_ok=True)

    def test_multiple_generators(self):
        config = {
            "generators": {
                "a": {"name": "A", "output_types": ["json"], "status": "active"},
                "b": {"name": "B", "output_types": ["markdown"], "status": "planned"},
            },
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(config, f)
            path = Path(f.name)

        try:
            registry = OutputGeneratorRegistry(config_path=path)
            assert registry.count() == 2
        finally:
            path.unlink(missing_ok=True)

    def test_list_all_returns_all(self):
        config = {"generators": {"x": {"name": "X", "output_types": ["json"]}}}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(config, f)
            path = Path(f.name)

        try:
            registry = OutputGeneratorRegistry(config_path=path)
            result = registry.list_all()
            assert len(result) == 1
            assert result[0].generator_id == "x"
        finally:
            path.unlink(missing_ok=True)

    def test_get_raises_on_missing(self):
        config = {"generators": {}}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(config, f)
            path = Path(f.name)

        try:
            registry = OutputGeneratorRegistry(config_path=path)
            with pytest.raises(GeneratorNotFoundError):
                registry.get("nonexistent")
        finally:
            path.unlink(missing_ok=True)

    def test_missing_config_file_returns_empty(self):
        registry = OutputGeneratorRegistry(config_path=Path("/nonexistent/path.yaml"))
        assert registry.count() == 0
        assert registry.list_all() == []

    def test_invalid_status_defaults_to_planned(self):
        config = {
            "generators": {
                "weird": {"name": "Weird", "output_types": ["json"], "status": "bogus"},
            },
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            yaml.dump(config, f)
            path = Path(f.name)

        try:
            registry = OutputGeneratorRegistry(config_path=path)
            gen = registry.get("weird")
            assert gen.status == GeneratorStatus.PLANNED
        finally:
            path.unlink(missing_ok=True)
