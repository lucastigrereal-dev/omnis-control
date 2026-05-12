"""PRD Generator — produces deterministic markdown from a Blueprint."""
from __future__ import annotations

from datetime import datetime, timezone

from src.app_factory.models import AppBlueprint, AppIdea, AppRequirement


def generate_prd(blueprint: AppBlueprint, req: AppRequirement, idea: AppIdea) -> str:
    """Generate a Product Requirements Document in markdown format."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []

    # ── Header ──────────────────────────────────────────────────────────
    lines.append(f"# PRD: {idea.title}")
    lines.append("")
    lines.append(f"> Generated: {now} | App Factory v0.1 | Dry-Run")
    lines.append(f"> Blueprint ID: `{blueprint.blueprint_id}`")
    lines.append(f"> App Type: **{req.app_type.upper()}**")
    lines.append("")

    # ── Overview ────────────────────────────────────────────────────────
    lines.append("## 1. Overview")
    lines.append("")
    lines.append(f"**Title:** {idea.title}")
    lines.append(f"**Domain:** {idea.domain or 'General'}")
    lines.append(f"**Target Audience:** {idea.target_audience or 'General users'}")
    lines.append("")
    lines.append(idea.description)
    lines.append("")

    # ── Features ────────────────────────────────────────────────────────
    lines.append("## 2. Features")
    lines.append("")
    if idea.features:
        for i, feat in enumerate(idea.features, 1):
            lines.append(f"{i}. {feat}")
    else:
        lines.append("- _(No explicit features provided — derived from requirements)_")
    lines.append("")

    # ── Requirements ────────────────────────────────────────────────────
    lines.append("## 3. Requirements")
    lines.append("")
    lines.append("### 3.1 Functional Requirements")
    lines.append("")
    for i, fr in enumerate(req.functional, 1):
        lines.append(f"- **FR-{i:02d}:** {fr}")
    lines.append("")
    lines.append("### 3.2 Non-Functional Requirements")
    lines.append("")
    for i, nfr in enumerate(req.non_functional, 1):
        lines.append(f"- **NFR-{i:02d}:** {nfr}")
    lines.append("")

    # ── Domain Model ────────────────────────────────────────────────────
    lines.append("## 4. Domain Model")
    lines.append("")
    if req.domain_entities:
        lines.append(f"**Entities:** {', '.join(e.capitalize() for e in req.domain_entities)}")
    if req.user_roles:
        lines.append(f"**User Roles:** {', '.join(r.capitalize() for r in req.user_roles)}")
    lines.append("")

    if blueprint.data_models:
        lines.append("### 4.1 Data Models")
        lines.append("")
        for model in blueprint.data_models:
            lines.append(f"#### {model['name']} (`{model['table']}`)")
            lines.append("")
            lines.append("| Field | Type | Constraints |")
            lines.append("|-------|------|-------------|")
            for field in model.get("fields", []):
                constraints = []
                if field.get("pk"):
                    constraints.append("PK")
                if not field.get("nullable", True):
                    constraints.append("NOT NULL")
                if field.get("unique"):
                    constraints.append("UNIQUE")
                con_str = ", ".join(constraints) if constraints else "-"
                lines.append(f"| {field['name']} | {field['type']} | {con_str} |")
            lines.append("")

    # ── Architecture ─────────────────────────────────────────────────────
    lines.append("## 5. Architecture")
    lines.append("")
    lines.append("### 5.1 Modules")
    lines.append("")
    for mod in blueprint.modules:
        deps = f" (depends on: {', '.join(mod.get('depends_on', []))})" if mod.get("depends_on") else ""
        lines.append(f"- **{mod['name']}:** {mod['purpose']}{deps}")
    lines.append("")

    lines.append("### 5.2 Tech Stack")
    lines.append("")
    for key, val in blueprint.tech_stack.items():
        label = key.replace("_", " ").title()
        lines.append(f"- **{label}:** {val}")
    lines.append("")

    # ── API Endpoints ────────────────────────────────────────────────────
    if blueprint.api_endpoints:
        lines.append("### 5.3 API Endpoints")
        lines.append("")
        lines.append("| Method | Path | Description |")
        lines.append("|--------|------|-------------|")
        for ep in blueprint.api_endpoints:
            lines.append(f"| {ep['method']} | `{ep['path']}` | {ep['description']} |")
        lines.append("")

    # ── UI Components ────────────────────────────────────────────────────
    if blueprint.component_tree.get("components"):
        lines.append("### 5.4 UI Components")
        lines.append("")
        _render_component_tree(lines, blueprint.component_tree, indent=0)
        lines.append("")

    # ── Constraints ──────────────────────────────────────────────────────
    if idea.constraints:
        lines.append("## 6. Constraints")
        lines.append("")
        for c in idea.constraints:
            lines.append(f"- {c}")
        lines.append("")

    # ── Footer ───────────────────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append("*Generated by OMNIS App Factory Skeleton v0.1 — deterministic, no LLM, no network.*")
    lines.append("")

    return "\n".join(lines)


def _render_component_tree(lines: list[str], node: dict, indent: int) -> None:
    prefix = "  " * indent
    if node.get("name"):
        lines.append(f"{prefix}- **{node['name']}**")
    for child in node.get("components", []) or node.get("children", []):
        _render_component_tree(lines, child, indent + 1)
