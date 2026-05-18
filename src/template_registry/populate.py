"""Populate Template Registry from existing assets.

Scans: caption templates, squad templates, n8n templates, skill manifests,
mission packages, and creative packages. Generates initial template_registry.json
and populates the templates/ directory with concrete template files.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import TemplateEntry, TemplateCategory, TemplateStatus
from .registry import TemplateRegistry

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _read_json(path: Path) -> dict | list | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _import_caption_templates(registry: TemplateRegistry) -> int:
    """Import caption templates from data/caption_templates.json."""
    path = PROJECT_ROOT / "data" / "caption_templates.json"
    data = _read_json(path)
    if not data:
        return 0
    count = 0
    for ct in data:
        tid = f"marketing_caption_{ct['template_id']}"
        entry = TemplateEntry(
            template_id=tid,
            name=ct["name"],
            category=TemplateCategory.MARKETING,
            description=ct.get("notes", ""),
            status=TemplateStatus.ACTIVE,
            tags=["caption", ct.get("objective", ""), ct.get("format", "feed")],
            content={
                "hook_template": ct.get("hook_template", ""),
                "body_template": ct.get("body_template", ""),
                "cta_template": ct.get("cta_template", ""),
                "hashtag_suggestions": ct.get("hashtag_suggestions", []),
            },
            source_output_path=str(path),
            score=7.0,
        )
        registry.add(entry)
        count += 1
    return count


def _import_squad_templates(registry: TemplateRegistry) -> int:
    """Import squad templates from src/squad_composer/templates.py metadata."""
    squads = [
        {
            "id": "squad_marketing",
            "name": "Marketing Squad",
            "desc": "Squad especializada em campanhas de marketing, carrosséis, reels e stories",
            "roles": ["estrategista", "copywriter", "designer", "social_media"],
            "risk": "medium",
        },
        {
            "id": "squad_sales",
            "name": "Sales Squad",
            "desc": "Squad de prospecção, pitch comercial e follow-up",
            "roles": ["sdr", "closer", "copywriter"],
            "risk": "low",
        },
        {
            "id": "squad_app_factory",
            "name": "App Factory Squad",
            "desc": "Squad para geração de aplicações completas a partir de briefing",
            "roles": ["architect", "backend_dev", "frontend_dev", "qa"],
            "risk": "medium",
        },
        {
            "id": "squad_ops",
            "name": "Ops Squad",
            "desc": "Squad de operações: auditoria, health check, relatórios",
            "roles": ["auditor", "devops", "analyst"],
            "risk": "low",
        },
        {
            "id": "squad_security",
            "name": "Security Squad",
            "desc": "Squad de segurança: audit, scan, compliance",
            "roles": ["security_engineer", "auditor"],
            "risk": "high",
        },
    ]
    for sq in squads:
        entry = TemplateEntry(
            template_id=sq["id"],
            name=sq["name"],
            category=TemplateCategory.OPS,
            description=sq["desc"],
            status=TemplateStatus.ACTIVE,
            tags=["squad", "orchestrator"],
            content={"roles": sq["roles"], "risk_level": sq["risk"]},
            score=8.0,
        )
        registry.add(entry)
    return len(squads)


def _import_skill_manifests(registry: TemplateRegistry) -> int:
    """Import skill manifests as automation templates."""
    skills_dir = PROJECT_ROOT / "skills"
    if not skills_dir.is_dir():
        return 0
    count = 0
    for manifest_path in skills_dir.glob("*/manifest.json"):
        data = _read_json(manifest_path)
        if not data:
            continue
        tid = f"automation_skill_{data['name']}"
        entry = TemplateEntry(
            template_id=tid,
            name=data.get("name", manifest_path.parent.name),
            category=TemplateCategory.AUTOMATION,
            description=data.get("description", ""),
            status=TemplateStatus.ACTIVE if data.get("status") == "active" else TemplateStatus.DRAFT,
            tags=data.get("tags", []) + ["skill"],
            content={
                "version": data.get("version", "0.0.0"),
                "risk_level": data.get("risk_level", "low"),
                "mode": data.get("mode", "read_only"),
            },
            source_output_path=str(manifest_path),
            score=7.5,
        )
        registry.add(entry)
        count += 1
    return count


def _import_mission_outputs(registry: TemplateRegistry) -> int:
    """Scan mission packages for reusable output templates."""
    missions_dir = PROJECT_ROOT / "missions"
    if not missions_dir.is_dir():
        return 0
    count = 0
    for mission_dir in sorted(missions_dir.iterdir()):
        if not mission_dir.is_dir():
            continue
        contract = _read_json(mission_dir / "mission_contract.json")
        if not contract:
            continue
        mission_id = mission_dir.name
        target = contract.get("target", "unknown")
        mission_type = contract.get("type", "unknown")

        tid = f"mission_{mission_id}"
        entry = TemplateEntry(
            template_id=tid,
            name=f"Mission: {target}",
            category=TemplateCategory.OPS,
            description=f"Mission output — type: {mission_type}, target: {target}",
            status=TemplateStatus.APPROVED,
            tags=["mission", mission_type, target],
            content={"contract": contract},
            source_mission_id=mission_id,
            score=6.0,
        )
        registry.add(entry)
        count += 1
        if count >= 20:
            break
    return count


def _populate_template_files(registry: TemplateRegistry, templates_dir: Path) -> int:
    """Write concrete template files into templates/<category>/ directories."""
    count = 0
    for entry in registry.list_all():
        cat_dir = templates_dir / entry.category.value
        cat_dir.mkdir(parents=True, exist_ok=True)
        file_path = cat_dir / f"{entry.template_id}.json"
        file_path.write_text(
            json.dumps(entry.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        entry.files.append(str(file_path.relative_to(templates_dir)))
        count += 1
    return count


def run(dry_run: bool = False) -> dict:
    """Run full population. Returns summary dict."""
    registry_path = PROJECT_ROOT / "templates" / "template_registry.json"
    templates_dir = PROJECT_ROOT / "templates"

    registry = TemplateRegistry(registry_path=registry_path, templates_dir=templates_dir)

    results = {
        "caption_templates": _import_caption_templates(registry),
        "squad_templates": _import_squad_templates(registry),
        "skill_manifests": _import_skill_manifests(registry),
        "mission_outputs": _import_mission_outputs(registry),
    }

    if not dry_run:
        _populate_template_files(registry, templates_dir)
        registry.save()

    results["total_entries"] = registry.count
    results["registry_path"] = str(registry_path)
    results["dry_run"] = dry_run
    return results
