"""W149 — n8n CLI Commands (dry-run only)."""
from __future__ import annotations

from .n8n_pipeline import N8nPipeline
from .n8n_templates import N8nTemplateLibrary
from .n8n_safety_gate import N8nSafetyGate


def cmd_n8n_list_templates() -> dict:
    templates = N8nTemplateLibrary.all_templates()
    return {
        "templates": [
            {"name": name, "trigger": wf.trigger.trigger_type, "steps": len(wf.steps)}
            for name, wf in templates.items()
        ],
        "count": len(templates),
    }


def cmd_n8n_run_template(template_name: str, cron_expr: str = "0 8 * * *", dry_run: bool = True) -> dict:
    templates = N8nTemplateLibrary.all_templates()
    if template_name not in templates:
        return {"error": f"Template not found: {template_name!r}", "available": list(templates.keys())}
    wf = templates[template_name]
    pipeline = N8nPipeline()
    result = pipeline.run(wf, cron_expr=cron_expr, dry_run=dry_run)
    return result.to_dict()


def cmd_n8n_check_template(template_name: str) -> dict:
    templates = N8nTemplateLibrary.all_templates()
    if template_name not in templates:
        return {"error": f"Template not found: {template_name!r}"}
    wf = templates[template_name]
    gate = N8nSafetyGate()
    result = gate.check(wf)
    return result.to_dict()


def cmd_n8n_export_template(template_name: str, dry_run: bool = True) -> dict:
    from .n8n_bridge import N8nBridge
    templates = N8nTemplateLibrary.all_templates()
    if template_name not in templates:
        return {"error": f"Template not found: {template_name!r}"}
    wf = templates[template_name]
    bridge = N8nBridge()
    export = bridge.export_workflow(wf, dry_run=dry_run)
    return export.to_dict()
