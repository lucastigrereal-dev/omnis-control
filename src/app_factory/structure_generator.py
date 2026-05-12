"""Project Structure Generator — deterministic file/folder tree from a Blueprint."""
from __future__ import annotations

from src.app_factory.models import AppBlueprint, AppRequirement


def generate_project_structure(blueprint: AppBlueprint, req: AppRequirement) -> dict:
    """Generate a planned project directory structure (no files created).

    Returns a nested dict representing the file/folder tree.
    Keys are file/folder names. Dict values are sub-trees. None values are files.
    """
    root: dict = {}

    # Language-specific src layout
    stack = blueprint.tech_stack
    is_python = "python" in str(stack.get("backend", "")).lower()

    if is_python:
        root |= _python_project(blueprint, req)
    else:
        root |= _node_project(blueprint, req)

    # Shared files
    root["README.md"] = None
    root[".gitignore"] = None

    return root


def _python_project(blueprint: AppBlueprint, req: AppRequirement) -> dict:
    tree: dict = {}

    # Package directory
    pkg_name = _slugify(req.app_type if req.app_type else "app")
    pkg: dict = {}
    pkg["__init__.py"] = None
    pkg["core"] = {"__init__.py": None, "config.py": None, "errors.py": None}

    for mod in blueprint.modules:
        name = mod["name"]
        if name in ("core", "tests"):
            continue
        pkg[name] = {"__init__.py": None}
        if mod.get("purpose") and "crud" in mod.get("purpose", "").lower():
            pkg[name]["models.py"] = None
            pkg[name]["service.py"] = None
            pkg[name]["routes.py"] = None

    tree[pkg_name] = pkg

    # Tests
    tests: dict = {"__init__.py": None, "conftest.py": None}
    for mod in blueprint.modules:
        if mod["name"] != "tests":
            tests[f"test_{mod['name']}.py"] = None
    tree["tests"] = tests

    # Config files
    tree["pyproject.toml"] = None
    tree["requirements.txt"] = None

    return tree


def _node_project(blueprint: AppBlueprint, req: AppRequirement) -> dict:
    tree: dict = {}

    src: dict = {}
    src["index.ts"] = None

    for mod in blueprint.modules:
        name = mod["name"]
        if name in ("core", "tests"):
            continue
        src[name] = {}
        if mod.get("purpose") and "crud" in mod.get("purpose", "").lower():
            src[name]["index.ts"] = None
            src[name]["types.ts"] = None

    tree["src"] = src

    # Tests
    tests: dict = {}
    for mod in blueprint.modules:
        if mod["name"] != "tests":
            tests[f"{mod['name']}.test.ts"] = None
    tree["tests"] = tests

    tree["package.json"] = None
    tree["tsconfig.json"] = None

    return tree


def _slugify(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")
