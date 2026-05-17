"""W178 — Tests for DependencyChecker."""
import pytest
from src.production_hardening.dependency_checker import (
    DepResult,
    DepStatus,
    DependencyChecker,
    DependencyReport,
    ModuleDescriptor,
    _parse_dep,
)


def _mod(name: str, requires=None, optional=None, version="0.1.0") -> ModuleDescriptor:
    return ModuleDescriptor(name=name, version=version, requires=requires or [], optional=optional or [])


def _checker(*mods: ModuleDescriptor) -> DependencyChecker:
    c = DependencyChecker()
    c.register_many(list(mods))
    return c


# ---------------------------------------------------------------------------
# _parse_dep
# ---------------------------------------------------------------------------

def test_parse_dep_simple():
    name, constraint = _parse_dep("omnis")
    assert name == "omnis"
    assert constraint is None


def test_parse_dep_with_constraint():
    name, constraint = _parse_dep("omnis:>=0.2.0")
    assert name == "omnis"
    assert constraint == ">=0.2.0"


# ---------------------------------------------------------------------------
# ModuleDescriptor
# ---------------------------------------------------------------------------

def test_module_round_trip():
    m = _mod("bridge", requires=["core"], version="1.2.0")
    m2 = ModuleDescriptor.from_dict(m.to_dict())
    assert m2.name == "bridge"
    assert "core" in m2.requires
    assert m2.version == "1.2.0"


# ---------------------------------------------------------------------------
# No dependencies
# ---------------------------------------------------------------------------

def test_no_deps_ok():
    c = _checker(_mod("core"), _mod("bridge"))
    r = c.check()
    assert r.ok


def test_empty_registry_ok():
    c = DependencyChecker()
    r = c.check()
    assert r.ok
    assert r.results == []


# ---------------------------------------------------------------------------
# Satisfied dependencies
# ---------------------------------------------------------------------------

def test_satisfied_dep():
    c = _checker(_mod("core"), _mod("bridge", requires=["core"]))
    r = c.check()
    assert r.ok
    satisfied = [x for x in r.results if x.status == DepStatus.SATISFIED]
    assert len(satisfied) == 1


def test_chain_of_deps():
    c = _checker(
        _mod("a"),
        _mod("b", requires=["a"]),
        _mod("c", requires=["b"]),
    )
    r = c.check()
    assert r.ok


# ---------------------------------------------------------------------------
# Missing dependency
# ---------------------------------------------------------------------------

def test_missing_dep_fails():
    c = _checker(_mod("bridge", requires=["core"]))
    r = c.check()
    assert not r.ok
    missing = [x for x in r.results if x.status == DepStatus.MISSING]
    assert len(missing) == 1
    assert missing[0].dep_name == "core"


def test_missing_dep_required_by():
    c = _checker(_mod("bridge", requires=["core"]))
    r = c.check()
    missing = [x for x in r.results if x.status == DepStatus.MISSING]
    assert missing[0].required_by == "bridge"


# ---------------------------------------------------------------------------
# Version mismatch
# ---------------------------------------------------------------------------

def test_version_satisfied():
    c = _checker(
        _mod("core", version="0.3.0"),
        _mod("bridge", requires=["core:>=0.2.0"]),
    )
    r = c.check()
    assert r.ok


def test_version_mismatch():
    c = _checker(
        _mod("core", version="0.1.0"),
        _mod("bridge", requires=["core:>=0.5.0"]),
    )
    r = c.check()
    assert not r.ok
    mismatch = [x for x in r.results if x.status == DepStatus.VERSION_MISMATCH]
    assert len(mismatch) == 1


# ---------------------------------------------------------------------------
# Optional dependencies
# ---------------------------------------------------------------------------

def test_optional_missing_not_failure():
    c = _checker(_mod("bridge", optional=["cache"]))
    r = c.check()
    assert r.ok
    opt_missing = [x for x in r.results if x.status == DepStatus.OPTIONAL_MISSING]
    assert len(opt_missing) == 1


def test_optional_present_no_warning():
    c = _checker(_mod("cache"), _mod("bridge", optional=["cache"]))
    r = c.check()
    assert r.ok
    opt_missing = [x for x in r.results if x.status == DepStatus.OPTIONAL_MISSING]
    assert len(opt_missing) == 0


# ---------------------------------------------------------------------------
# Circular dependency detection
# ---------------------------------------------------------------------------

def test_circular_detected():
    c = _checker(
        _mod("a", requires=["b"]),
        _mod("b", requires=["a"]),
    )
    r = c.check()
    assert not r.ok
    circular = [x for x in r.results if x.status == DepStatus.CIRCULAR]
    assert len(circular) >= 1


def test_self_cycle():
    c = _checker(_mod("a", requires=["a"]))
    r = c.check()
    assert not r.ok


def test_no_cycle():
    c = _checker(
        _mod("a"),
        _mod("b", requires=["a"]),
        _mod("c", requires=["a", "b"]),
    )
    r = c.check()
    assert r.ok


# ---------------------------------------------------------------------------
# Topological load order
# ---------------------------------------------------------------------------

def test_load_order_computed():
    c = _checker(
        _mod("a"),
        _mod("b", requires=["a"]),
        _mod("c", requires=["b"]),
    )
    r = c.check()
    assert r.ok
    assert r.load_order.index("a") < r.load_order.index("b")
    assert r.load_order.index("b") < r.load_order.index("c")


def test_load_order_empty_on_failure():
    c = _checker(_mod("a", requires=["missing"]))
    r = c.check()
    assert not r.ok
    assert r.load_order == []


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def test_report_to_dict():
    c = _checker(_mod("a"), _mod("b", requires=["a"]))
    r = c.check()
    d = r.to_dict()
    assert "ok" in d
    assert "results" in d
    assert "load_order" in d
    assert "summary" in d


def test_report_summary_counts():
    c = _checker(
        _mod("core"),
        _mod("bridge", requires=["core"], optional=["cache"]),
    )
    r = c.check()
    d = r.to_dict()
    assert d["summary"]["satisfied"] == 1
    assert d["summary"]["optional_missing"] == 1


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def test_modules_list():
    c = _checker(_mod("a"), _mod("b"))
    assert set(c.modules()) == {"a", "b"}


def test_register_many():
    c = DependencyChecker()
    c.register_many([_mod("a"), _mod("b"), _mod("c")])
    assert len(c.modules()) == 3
