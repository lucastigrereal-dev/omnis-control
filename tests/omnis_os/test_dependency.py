"""Tests for P29 dependency resolution."""
import pytest

from src.omnis_os.dependency import resolve_order, detect_cycles, validate_dependencies
from src.omnis_os.errors import DependencyCycleError
from src.omnis_os.models import ModuleInfo


def _mod(name: str, deps=None) -> ModuleInfo:
    m = ModuleInfo.new(name)
    m.dependencies = deps or []
    return m


class TestResolveOrder:
    def test_empty(self):
        assert resolve_order([]) == []

    def test_single_module(self):
        assert resolve_order([_mod("a")]) == ["a"]

    def test_linear_chain(self):
        mods = [_mod("c", ["b"]), _mod("b", ["a"]), _mod("a")]
        order = resolve_order(mods)
        assert order.index("a") < order.index("b") < order.index("c")

    def test_diamond(self):
        mods = [_mod("d", ["b", "c"]), _mod("b", ["a"]), _mod("c", ["a"]), _mod("a")]
        order = resolve_order(mods)
        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    def test_independent(self):
        mods = [_mod("a"), _mod("b")]
        order = resolve_order(mods)
        assert set(order) == {"a", "b"}

    def test_cycle_raises(self):
        mods = [_mod("a", ["b"]), _mod("b", ["a"])]
        with pytest.raises(DependencyCycleError):
            resolve_order(mods)

    def test_self_loop_raises(self):
        mods = [_mod("a", ["a"])]
        with pytest.raises(DependencyCycleError):
            resolve_order(mods)

    def test_three_node_cycle(self):
        mods = [_mod("a", ["b"]), _mod("b", ["c"]), _mod("c", ["a"])]
        with pytest.raises(DependencyCycleError):
            resolve_order(mods)

    def test_dict_modules(self):
        mods = [{"name": "a"}, {"name": "b", "dependencies": ["a"]}]
        order = resolve_order(mods)
        assert order.index("a") < order.index("b")

    def test_external_dep_ignored(self):
        """Dependency not in module set should be ignored."""
        mods = [_mod("a", ["external_thing"])]
        order = resolve_order(mods)
        assert order == ["a"]


class TestDetectCycles:
    def test_no_cycle(self):
        assert detect_cycles([_mod("a"), _mod("b", ["a"])]) == []

    def test_simple_cycle(self):
        cycles = detect_cycles([_mod("a", ["b"]), _mod("b", ["a"])])
        assert len(cycles) >= 1

    def test_self_loop(self):
        cycles = detect_cycles([_mod("a", ["a"])])
        assert len(cycles) >= 1

    def test_three_node_cycle(self):
        mods = [_mod("a", ["b"]), _mod("b", ["c"]), _mod("c", ["a"])]
        cycles = detect_cycles(mods)
        assert len(cycles) >= 1

    def test_dict_input(self):
        cycles = detect_cycles([
            {"name": "a", "dependencies": ["b"]},
            {"name": "b", "dependencies": ["a"]},
        ])
        assert len(cycles) >= 1


class TestValidateDependencies:
    def test_all_present(self):
        ok, missing = validate_dependencies([
            _mod("a"), _mod("b", ["a"])
        ])
        assert ok
        assert missing == []

    def test_missing_dep(self):
        ok, missing = validate_dependencies([
            _mod("a", ["ghost"])
        ])
        assert not ok
        assert len(missing) == 1

    def test_empty_modules(self):
        ok, missing = validate_dependencies([])
        assert ok

    def test_multiple_missing(self):
        mods = [_mod("a", ["x"]), _mod("b", ["y", "z"])]
        ok, missing = validate_dependencies(mods)
        assert not ok
        assert len(missing) == 3
