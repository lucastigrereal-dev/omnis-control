#!/usr/bin/env python3
"""
Deploy OMNIS skills from .claude/skills/ to the global ~/.claude/skills/
with the omnis- prefix so they're accessible in any Claude Code session.

Usage:
    python scripts/deploy_claude_skills.py
    python scripts/deploy_claude_skills.py --dry-run
"""
import argparse
import json
import shutil
from pathlib import Path

REPO_SKILLS = Path(__file__).parent.parent / ".claude" / "skills"
GLOBAL_SKILLS = Path.home() / ".claude" / "skills"

# Only the 11 Onda 0 skills (those with skill.json)
ONDA0_SKILLS = [
    "architecture-review",
    "artifact-analysis",
    "capability-assessment",
    "context-engineering",
    "dependency-analysis",
    "git-workflow",
    "governance-review",
    "registry-analysis",
    "schema-design",
    "security-review",
    "technical-writing",
]


def deploy(dry_run: bool = False) -> None:
    results = []
    for skill in ONDA0_SKILLS:
        src = REPO_SKILLS / skill
        dst = GLOBAL_SKILLS / f"omnis-{skill}"
        prefixed = f"omnis-{skill}"

        if not src.exists():
            results.append(f"SKIP  {skill}  (source missing)")
            continue

        if not dry_run:
            dst.mkdir(parents=True, exist_ok=True)

        for filename in ("SKILL.md", "skill.json"):
            src_file = src / filename
            dst_file = dst / filename
            if not src_file.exists():
                continue

            content = src_file.read_text(encoding="utf-8")
            content = content.replace(f"name: {skill}", f"name: {prefixed}")

            if filename == "skill.json":
                try:
                    data = json.loads(content)
                    data["name"] = prefixed
                    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
                except json.JSONDecodeError:
                    content = content.replace(f'"name": "{skill}"', f'"name": "{prefixed}"')

            if not dry_run:
                dst_file.write_text(content, encoding="utf-8")

        action = "DRY-RUN" if dry_run else "OK"
        results.append(f"{action}   omnis-{skill}")

    for r in results:
        print(r)

    if not dry_run:
        print(f"\n{len(ONDA0_SKILLS)} skills deployed to {GLOBAL_SKILLS}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    deploy(dry_run=args.dry_run)
