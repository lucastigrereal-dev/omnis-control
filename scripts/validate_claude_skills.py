"""Validate the 11 OMNIS skills in .claude/skills/."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SKILLS_DIR = ROOT / ".claude" / "skills"

EXPECTED_SKILLS = [
    "context-engineering",
    "git-workflow",
    "governance-review",
    "architecture-review",
    "technical-writing",
    "schema-design",
    "security-review",
    "dependency-analysis",
    "artifact-analysis",
    "registry-analysis",
    "capability-assessment",
]

REQUIRED_JSON_FIELDS = [
    "name", "version", "description", "status", "risk_level",
    "mode", "owner", "tags", "approval_required", "lifecycle",
    "created_at", "updated_at",
]

VALID_RISK_LEVELS = {"low", "medium", "high"}
VALID_MODES = {"read_only", "draft_only", "local_write", "external_action", "dangerous"}
VALID_STATUSES = {"draft", "proposed", "approved", "deprecated", "blocked"}

errors: list[str] = []
warnings: list[str] = []


def check_skill(name: str) -> None:
    skill_dir = SKILLS_DIR / name

    if not skill_dir.exists():
        errors.append(f"[{name}] directory missing: {skill_dir}")
        return

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append(f"[{name}] SKILL.md missing")
    else:
        content = skill_md.read_text(encoding="utf-8")
        if not content.startswith("---"):
            errors.append(f"[{name}] SKILL.md missing YAML frontmatter")
        if len(content.strip()) < 100:
            warnings.append(f"[{name}] SKILL.md content very short ({len(content)} chars)")

    skill_json = skill_dir / "skill.json"
    if not skill_json.exists():
        errors.append(f"[{name}] skill.json missing")
        return

    try:
        data = json.loads(skill_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"[{name}] skill.json invalid JSON: {e}")
        return

    for field in REQUIRED_JSON_FIELDS:
        if field not in data:
            errors.append(f"[{name}] skill.json missing field: {field}")

    if data.get("name") != name:
        errors.append(
            f"[{name}] skill.json name mismatch: expected '{name}', got '{data.get('name')}'"
        )

    if data.get("risk_level") not in VALID_RISK_LEVELS:
        errors.append(f"[{name}] invalid risk_level: {data.get('risk_level')!r}")

    if data.get("mode") not in VALID_MODES:
        errors.append(f"[{name}] invalid mode: {data.get('mode')!r}")

    if data.get("status") not in VALID_STATUSES:
        errors.append(f"[{name}] invalid status: {data.get('status')!r}")

    if data.get("mode") in {"external_action", "dangerous"} and not data.get("approval_required"):
        errors.append(f"[{name}] mode={data['mode']} requires approval_required=true")


def main() -> int:
    print(f"Validating {len(EXPECTED_SKILLS)} OMNIS skills in {SKILLS_DIR}\n")

    for skill_name in EXPECTED_SKILLS:
        check_skill(skill_name)

    extra_dirs = [
        d.name for d in SKILLS_DIR.iterdir()
        if d.is_dir() and d.name not in EXPECTED_SKILLS and not d.name.startswith(".")
    ]
    if extra_dirs:
        print(f"  INFO  {len(extra_dirs)} extra skill dirs (not in EXPECTED list): {extra_dirs}")

    for w in warnings:
        print(f"  WARN  {w}")

    if errors:
        for e in errors:
            print(f"  FAIL  {e}")
        print(f"\n{len(errors)} error(s) — fix before continuing.")
        return 1

    print(f"  PASS  All {len(EXPECTED_SKILLS)} skills valid.")
    if warnings:
        print(f"  ({len(warnings)} warning(s) above)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
