"""P29 OMNIS OS Layer — dependency resolution and cycle detection."""
from collections import deque

from src.omnis_os.errors import DependencyCycleError


def resolve_order(modules: list, name_fn=None, deps_fn=None) -> list[str]:
    """Topological sort returning ordered list of module names.

    Args:
        modules: List of modules (objects or dicts).
        name_fn: Callable to get module name. Defaults to .name or ["name"].
        deps_fn: Callable to get dependency list. Defaults to .dependencies or ["dependencies"].

    Returns:
        Ordered list of module names (first = no dependencies).

    Raises:
        DependencyCycleError: If a cycle is detected.
    """
    if name_fn is None:
        name_fn = _auto_name
    if deps_fn is None:
        deps_fn = _auto_deps

    # Build adjacency
    names = {name_fn(m) for m in modules}
    in_degree: dict[str, int] = {n: 0 for n in names}
    adjacency: dict[str, list[str]] = {n: [] for n in names}

    for m in modules:
        src = name_fn(m)
        for dep in deps_fn(m):
            if dep in names:
                adjacency[dep].append(src)
                in_degree[src] += 1

    # Kahn's algorithm
    queue = deque([n for n, d in in_degree.items() if d == 0])
    result: list[str] = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in adjacency[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(names):
        raise DependencyCycleError("Circular dependency detected during resolution")

    return result


def detect_cycles(modules: list, name_fn=None, deps_fn=None) -> list[list[str]]:
    """Detect all dependency cycles using depth-first search.

    Returns:
        List of cycles, each cycle is a list of module names.
    """
    if name_fn is None:
        name_fn = _auto_name
    if deps_fn is None:
        deps_fn = _auto_deps

    names = {name_fn(m) for m in modules}
    adjacency: dict[str, list[str]] = {n: [] for n in names}
    for m in modules:
        src = name_fn(m)
        for dep in deps_fn(m):
            if dep in names:
                adjacency[src].append(dep)

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {n: WHITE for n in names}
    cycles: list[list[str]] = []

    def _dfs(node: str, stack: list[str]):
        color[node] = GRAY
        stack.append(node)
        for neighbor in adjacency.get(node, []):
            if color.get(neighbor) == WHITE:
                _dfs(neighbor, stack)
            elif color.get(neighbor) == GRAY:
                # Found a cycle — extract from stack
                idx = stack.index(neighbor)
                cycles.append(stack[idx:] + [neighbor])
        stack.pop()
        color[node] = BLACK

    for n in names:
        if color[n] == WHITE:
            _dfs(n, [])

    return cycles


def validate_dependencies(modules: list, name_fn=None, deps_fn=None) -> tuple[bool, list[str]]:
    """Check all declared dependencies exist in the module set.

    Returns:
        (is_valid, list_of_missing_refs).
    """
    if name_fn is None:
        name_fn = _auto_name
    if deps_fn is None:
        deps_fn = _auto_deps

    names = {name_fn(m) for m in modules}
    missing: list[str] = []

    for m in modules:
        src = name_fn(m)
        for dep in deps_fn(m):
            if dep not in names:
                missing.append(f"{src} → {dep}")

    return len(missing) == 0, missing


# ── Internal helpers ──────────────────────────────────────────────


def _auto_name(m) -> str:
    if isinstance(m, dict):
        return m.get("name", "")
    return getattr(m, "name", str(m))


def _auto_deps(m) -> list:
    if isinstance(m, dict):
        return m.get("dependencies", [])
    return getattr(m, "dependencies", [])
