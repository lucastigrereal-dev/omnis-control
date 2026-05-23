import os
import yaml

SKILLS_DIR = os.path.expanduser("~/.claude/skills")
REGISTRY_FILE = os.path.expanduser("~/.claude/registry/skills.yaml")


def _list_skill_entries() -> list[dict[str, object]]:
    if not os.path.isdir(SKILLS_DIR):
        return []
    items = []
    try:
        for entry in sorted(os.listdir(SKILLS_DIR)):
            entry_path = os.path.join(SKILLS_DIR, entry)
            has_run = os.path.isfile(os.path.join(entry_path, "run.py"))
            has_skill_md = os.path.isfile(os.path.join(entry_path, "SKILL.md"))
            if os.path.isdir(entry_path):
                if has_run:
                    skill_type = "executable"
                elif has_skill_md:
                    skill_type = "doc_folder"
                else:
                    skill_type = "doc_folder"
                items.append({
                    "name": entry,
                    "type": skill_type,
                    "path": entry_path,
                    "has_run": has_run,
                    "has_skill_md": has_skill_md,
                })
            elif entry.endswith(".md"):
                items.append({
                    "name": entry.replace(".md", ""),
                    "type": "doc_file",
                    "path": entry_path,
                    "has_run": False,
                    "has_skill_md": False,
                })
    except OSError:
        pass
    return items


def _load_registry_skills() -> set[str]:
    if not os.path.isfile(REGISTRY_FILE):
        return set()
    try:
        with open(REGISTRY_FILE, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            skills = data.get("skills", [])
            if isinstance(skills, list):
                return {s.get("name", "") for s in skills if isinstance(s, dict)}
            return set(data.keys())
        return set()
    except (yaml.YAMLError, OSError):
        return set()


def check() -> dict[str, object]:
    entries = _list_skill_entries()
    registry_names = _load_registry_skills()
    disk_names = {e["name"] for e in entries}

    executables = [e for e in entries if e["type"] == "executable"]
    doc_folders = [e for e in entries if e["type"] == "doc_folder"]
    doc_files = [e for e in entries if e["type"] == "doc_file"]

    orphans = disk_names - registry_names if registry_names else set()
    missing_from_disk = registry_names - disk_names if registry_names else set()

    return {
        "total": len(entries),
        "executable": len(executables),
        "executable_list": [e["name"] for e in executables],
        "doc_folder": len(doc_folders),
        "doc_folder_list": [e["name"] for e in doc_folders],
        "doc_file": len(doc_files),
        "doc_file_list": [e["name"] for e in doc_files],
        "orphan_skills": sorted(orphans) if orphans else [],
        "registry_missing_from_disk": sorted(missing_from_disk) if missing_from_disk else [],
        "registry_available": bool(registry_names),
    }
