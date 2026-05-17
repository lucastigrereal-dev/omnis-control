"""W178 — Dependency Checker: validates inter-module dependencies before startup."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.remote_control.models import _new_id, _now_iso


class DepStatus(str, Enum):
    SATISFIED = "SATISFIED"
    MISSING = "MISSING"
    VERSION_MISMATCH = "VERSION_MISMATCH"
    CIRCULAR = "CIRCULAR"
    OPTIONAL_MISSING = "OPTIONAL_MISSING"


# ---------------------------------------------------------------------------
# Module descriptor
# ---------------------------------------------------------------------------

@dataclass
class ModuleDescriptor:
    name: str
    version: str = "0.1.0"
    requires: list[str] = field(default_factory=list)       # "module_name:>=version" or "module_name"
    optional: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "requires": self.requires,
            "optional": self.optional,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ModuleDescriptor":
        return cls(
            name=d.get("name", ""),
            version=d.get("version", "0.1.0"),
            requires=d.get("requires", []),
            optional=d.get("optional", []),
        )


# ---------------------------------------------------------------------------
# Dependency result
# ---------------------------------------------------------------------------

@dataclass
class DepResult:
    dep_name: str
    status: DepStatus
    required_by: str = ""
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "dep_name": self.dep_name,
            "status": self.status.value,
            "required_by": self.required_by,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Check report
# ---------------------------------------------------------------------------

@dataclass
class DependencyReport:
    report_id: str = field(default_factory=lambda: _new_id("dep"))
    ok: bool = True
    results: list[DepResult] = field(default_factory=list)
    load_order: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "ok": self.ok,
            "results": [r.to_dict() for r in self.results],
            "load_order": self.load_order,
            "generated_at": self.generated_at,
            "summary": {
                "satisfied": sum(1 for r in self.results if r.status == DepStatus.SATISFIED),
                "missing": sum(1 for r in self.results if r.status == DepStatus.MISSING),
                "circular": sum(1 for r in self.results if r.status == DepStatus.CIRCULAR),
                "optional_missing": sum(1 for r in self.results if r.status == DepStatus.OPTIONAL_MISSING),
            },
        }


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------

def _parse_dep(dep_str: str) -> tuple[str, Optional[str]]:
    """Parse 'module_name:>=0.2.0' → (module_name, '>=0.2.0') or ('module_name', None)."""
    if ":" in dep_str:
        parts = dep_str.split(":", 1)
        return parts[0].strip(), parts[1].strip()
    return dep_str.strip(), None


def _version_satisfies(available: str, constraint: Optional[str]) -> bool:
    """Simple version comparison supporting >=, <=, ==."""
    if constraint is None:
        return True
    try:
        from packaging.version import Version
        v = Version(available)
        if constraint.startswith(">="):
            return v >= Version(constraint[2:])
        if constraint.startswith("<="):
            return v <= Version(constraint[2:])
        if constraint.startswith("=="):
            return v == Version(constraint[2:])
    except Exception:
        pass
    # Fallback: string equality
    return available == constraint.lstrip(">=<= ")


class DependencyChecker:
    """Validates module dependency graph and computes topological load order."""

    def __init__(self) -> None:
        self._modules: dict[str, ModuleDescriptor] = {}

    def register(self, module: ModuleDescriptor) -> None:
        self._modules[module.name] = module

    def register_many(self, modules: list[ModuleDescriptor]) -> None:
        for m in modules:
            self.register(m)

    # ------------------------------------------------------------------
    def check(self) -> DependencyReport:
        report = DependencyReport()

        for mod in self._modules.values():
            # Required deps
            for dep_str in mod.requires:
                dep_name, constraint = _parse_dep(dep_str)
                if dep_name not in self._modules:
                    report.ok = False
                    report.results.append(DepResult(
                        dep_name=dep_name,
                        status=DepStatus.MISSING,
                        required_by=mod.name,
                        message=f"{mod.name} requires {dep_str}",
                    ))
                else:
                    dep_mod = self._modules[dep_name]
                    if not _version_satisfies(dep_mod.version, constraint):
                        report.ok = False
                        report.results.append(DepResult(
                            dep_name=dep_name,
                            status=DepStatus.VERSION_MISMATCH,
                            required_by=mod.name,
                            message=f"{mod.name} needs {dep_str}, found {dep_mod.version}",
                        ))
                    else:
                        report.results.append(DepResult(
                            dep_name=dep_name,
                            status=DepStatus.SATISFIED,
                            required_by=mod.name,
                        ))

            # Optional deps
            for dep_str in mod.optional:
                dep_name, _ = _parse_dep(dep_str)
                if dep_name not in self._modules:
                    report.results.append(DepResult(
                        dep_name=dep_name,
                        status=DepStatus.OPTIONAL_MISSING,
                        required_by=mod.name,
                        message=f"{mod.name} optional dep {dep_name} not found",
                    ))

        # Detect circular deps
        circular = self._detect_cycles()
        for cycle in circular:
            report.ok = False
            report.results.append(DepResult(
                dep_name=" → ".join(cycle),
                status=DepStatus.CIRCULAR,
                message=f"Circular dependency: {' → '.join(cycle)}",
            ))

        # Compute load order (topo sort)
        if report.ok:
            report.load_order = self._topo_sort()

        return report

    def check_module(self, name: str) -> DependencyReport:
        """Check only deps for a single module."""
        mod = self._modules.get(name)
        if not mod:
            r = DependencyReport(ok=False)
            r.results.append(DepResult(dep_name=name, status=DepStatus.MISSING, message="module_not_registered"))
            return r
        # Temporarily check just this module
        orig = self._modules
        self._modules = {k: v for k, v in orig.items()}
        report = self.check()
        return report

    def modules(self) -> list[str]:
        return list(self._modules.keys())

    # ------------------------------------------------------------------
    def _detect_cycles(self) -> list[list[str]]:
        cycles: list[list[str]] = []
        visited: set[str] = set()
        path: list[str] = []

        def dfs(name: str) -> bool:
            if name in path:
                cycle_start = path.index(name)
                cycles.append(list(path[cycle_start:]) + [name])
                return True
            if name in visited:
                return False
            visited.add(name)
            path.append(name)
            mod = self._modules.get(name)
            if mod:
                for dep_str in mod.requires:
                    dep_name, _ = _parse_dep(dep_str)
                    if dfs(dep_name):
                        break
            path.pop()
            return False

        for mod_name in self._modules:
            if mod_name not in visited:
                dfs(mod_name)
        return cycles

    def _topo_sort(self) -> list[str]:
        visited: set[str] = set()
        order: list[str] = []

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            mod = self._modules.get(name)
            if mod:
                for dep_str in mod.requires:
                    dep_name, _ = _parse_dep(dep_str)
                    if dep_name in self._modules:
                        visit(dep_name)
            order.append(name)

        for mod_name in self._modules:
            visit(mod_name)
        return order
