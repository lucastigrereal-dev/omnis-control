"""P5 Marketing Supreme — local exporters (markdown, csv, json).

Dry-run only. No upload, no API, no network.
"""

from __future__ import annotations

import csv
import json
import io
from typing import Optional

from src.marketing.models import CampaignPackage, ContentItem


def _md_opt(label: str, value: Optional[str]) -> str:
    """Emit a markdown detail line if value is truthy."""
    if value:
        return f"- **{label}:** {value}\n"
    return ""


def export_campaign_package_markdown(package: CampaignPackage) -> str:
    """Render a CampaignPackage as a readable Markdown spec."""
    buf = io.StringIO()
    buf.write(f"# Campaign: {package.name}\n\n")
    buf.write(f"**ID:** `{package.id}`\n")
    buf.write(f"**Valid:** {'yes' if package.is_valid else 'no — ' + ', '.join(package.validation_issues)}\n\n")

    if package.brief:
        b = package.brief
        buf.write("## Brief\n\n")
        buf.write(f"- **ID:** `{b.id}`\n")
        buf.write(f"- **Name:** {b.name}\n")
        buf.write(f"- **Objective:** `{b.objective_id}`\n")
        buf.write(f"- **Audience:** `{b.audience_id}`\n")
        buf.write(f"- **Pillars:** {', '.join(f'`{p}`' for p in b.pillar_ids)}\n")
        buf.write(f"- **Period:** {b.start_date} → {b.end_date}\n")
        buf.write(f"- **Budget:** {b.budget:.2f}\n")
        buf.write(f"- **Key Message:** {b.key_message}\n")
        buf.write(f"- **CTA:** {b.call_to_action}\n")
        buf.write(f"- **Tone:** {b.tone}\n")
        if b.constraints:
            buf.write(f"- **Constraints:** {', '.join(b.constraints)}\n")
        buf.write("\n")

    if package.plan:
        p = package.plan
        buf.write("## Content Plan\n\n")
        buf.write(f"- **ID:** `{p.id}`\n")
        buf.write(f"- **Period:** {p.schedule_start} → {p.schedule_end}\n")
        buf.write(f"- **Items:** {p.item_count}\n\n")
        if p.items:
            buf.write("| Date | Topic | Format | Platform | CTA |\n")
            buf.write("|---|---|---|---|---|\n")
            for item in p.items:
                buf.write(f"| {item.date} | {item.topic} | {item.content_format} | {item.platform} | {item.cta} |\n")
            buf.write("\n")

    if package.validation_warnings:
        buf.write("## Warnings\n\n")
        for w in package.validation_warnings:
            buf.write(f"- {w}\n")
        buf.write("\n")

    return buf.getvalue()


def export_content_calendar_csv(items: list[ContentItem]) -> str:
    """Export content items as CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "pillar_id", "topic", "content_format", "platform", "hook", "cta", "notes"])
    for item in items:
        writer.writerow([
            item.date,
            item.pillar_id,
            item.topic,
            item.content_format,
            item.platform,
            item.hook,
            item.cta,
            item.notes,
        ])
    return buf.getvalue()


def export_content_calendar_json(items: list[ContentItem]) -> str:
    """Export content items as pretty-printed JSON string."""
    return json.dumps([item.to_dict() for item in items], indent=2, ensure_ascii=False)
