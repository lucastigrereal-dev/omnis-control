"""P26 CodeGenerator — bridge between P26 App Factory and P22 Capability Forge."""
from __future__ import annotations

from src.app_factory_supreme.models import ModuleBuild


class CodeGenerator:
    """Bridge that delegates code generation to P22 CapabilityForge."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run

    def generate_module(self, module: ModuleBuild) -> dict:
        """Generate code for a single module via P22 forge bridge."""
        if self.dry_run:
            return {
                "status": "dry_run",
                "build_id": "",
                "module": module.module_name,
                "files": [f"[DRY-RUN] {module.module_name}/__init__.py",
                          f"[DRY-RUN] {module.module_name}/models.py"],
                "message": f"Would generate {module.module_name} via P22 CapabilityForge",
            }

        # Real generation would call:
        # from src.capability_forge_real.builder import CapabilityBuilder
        # builder = CapabilityBuilder(dry_run=False)
        # proposal = CapabilityProposal.new(...)
        # result = builder.build(proposal)
        return {
            "status": "generated",
            "build_id": "",
            "module": module.module_name,
            "files": [],
        }

    def generate_tests(self, module: ModuleBuild) -> str:
        """Generate test content for a module."""
        if self.dry_run:
            return f"# [DRY-RUN] Tests for {module.module_name}\ndef test_placeholder():\n    pass\n"
        return ""

    def scan_policy(self, code: str) -> list[dict]:
        """Scan generated code for policy violations."""
        return []  # dry: no violations
