"""Campaign exporter — writes campaign files to disk."""
import csv
import json
from pathlib import Path

from src.campaign_package.models import Campaign


def export_campaign(campaign: Campaign, output_dir: Path) -> list[str]:
    """Write all campaign files. Returns list of created filenames."""
    output_dir.mkdir(parents=True, exist_ok=True)
    created = []

    # campaign_manifest.json
    manifest_path = output_dir / "campaign_manifest.json"
    manifest_path.write_text(
        json.dumps(campaign.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    created.append("campaign_manifest.json")

    # calendar.csv
    csv_path = output_dir / "calendar.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["post_number", "title", "account_handle", "scheduled_date", "status", "package_id"])
        writer.writeheader()
        for post in campaign.posts:
            writer.writerow(post.to_dict())
    created.append("calendar.csv")

    # README.md
    readme = output_dir / "README.md"
    lines = [
        f"# Campaign: {campaign.name}",
        "",
        f"- ID: {campaign.campaign_id}",
        f"- Posts: {campaign.post_count}",
        f"- Conta: {campaign.account_handle}",
        f"- Status: {campaign.status.value}",
        f"- Criado: {campaign.created_at}",
        "",
        "## Posts",
        "",
    ]
    for post in campaign.posts:
        lines.append(f"- Post {post.post_number:02d}: {post.title} ({post.scheduled_date})")
    readme.write_text("\n".join(lines), encoding="utf-8")
    created.append("README.md")

    # publishing_checklist.md
    checklist = output_dir / "publishing_checklist.md"
    checklist_lines = [
        "# Campaign Publishing Checklist",
        "",
        f"Campaign: {campaign.name}",
        "",
    ]
    for post in campaign.posts:
        checklist_lines.append(f"- [ ] Post {post.post_number:02d}: {post.title}")
    checklist_lines += ["", "## Pre-publicacao", "- [ ] Revisar todas as legendas", "- [ ] Confirmar assets", "- [ ] Aprovar com Lucas"]
    checklist.write_text("\n".join(checklist_lines), encoding="utf-8")
    created.append("publishing_checklist.md")

    # posts/ subdirectory — one stub dir per post
    posts_dir = output_dir / "posts"
    posts_dir.mkdir(exist_ok=True)
    for post in campaign.posts:
        post_dir = posts_dir / f"post_{post.post_number:02d}"
        post_dir.mkdir(exist_ok=True)
        (post_dir / "README.md").write_text(
            f"# Post {post.post_number:02d}: {post.title}\n\nStatus: {post.status}\nData: {post.scheduled_date}\n",
            encoding="utf-8",
        )
    created.append(f"posts/ ({campaign.post_count} posts)")

    return created
