"""Cockpit Data Generator - produces cockpit/data/*.json from all local sources.

Usage:
    python -m src.reports.cockpit_data_all          # generate all data files
    python -m src.reports.cockpit_data_all --quiet  # suppress output
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

BASE = Path(__file__).resolve().parent.parent.parent
COCKPIT_DATA = BASE / "cockpit" / "data"
MISSIONS_ROOT = BASE / "missions"
DATA_DIR = BASE / "data"
TEMPLATES_DIR = BASE / "templates"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_data_dir() -> Path:
    COCKPIT_DATA.mkdir(parents=True, exist_ok=True)
    return COCKPIT_DATA


def _write_json(filename: str, data: dict | list) -> Path:
    path = ensure_data_dir() / filename
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# ── Mission data ──────────────────────────────────────────────────────────────

def collect_missions() -> dict:
    missions: list[dict] = []
    if not MISSIONS_ROOT.exists():
        return {"missions": [], "generated_at": _now_iso()}

    stats = {"total": 0, "open": 0, "closed": 0, "pending_approval": 0}

    for md in sorted(MISSIONS_ROOT.iterdir()):
        if not md.is_dir() or md.name.startswith("."):
            continue

        contract = md / "mission_contract.json"
        entry: dict = {
            "mission_id": md.name,
            "path": str(md.relative_to(BASE)).replace("\\", "/"),
            "status": "unknown",
            "setor": "general",
            "objetivo": "",
            "criado_por": "",
            "timestamp": "",
            "closed_at": None,
            "outputs_count": 0,
            "exports_count": 0,
            "has_approval_pending": False,
            "has_report": False,
            "logs_count": 0,
        }

        if contract.exists():
            try:
                raw = json.loads(contract.read_text(encoding="utf-8"))
                entry.update({
                    "status": raw.get("status", "unknown"),
                    "setor": raw.get("setor", "general"),
                    "objetivo": raw.get("objetivo", ""),
                    "criado_por": raw.get("criado_por", ""),
                    "timestamp": raw.get("timestamp", ""),
                    "closed_at": raw.get("closed_at"),
                })
            except (json.JSONDecodeError, KeyError):
                pass

        # Count outputs, exports, approvals, logs
        for sub, key in [("05_outputs", "outputs_count"), ("06_exports", "exports_count"),
                         ("08_logs", "logs_count")]:
            d = md / sub
            if d.exists():
                entry[key] = sum(1 for f in d.iterdir() if f.is_file())

        if (md / "07_approval").exists():
            entry["has_approval_pending"] = any(
                (md / "07_approval").glob("approval_request.md")
            )
        if (md / "relatorio_final.md").exists():
            entry["has_report"] = True

        stats["total"] += 1
        if entry["status"] == "open":
            stats["open"] += 1
        elif entry["status"] == "closed":
            stats["closed"] += 1
        if entry["has_approval_pending"]:
            stats["pending_approval"] += 1

        missions.append(entry)

    return {"missions": missions, "stats": stats, "generated_at": _now_iso()}


# ── Backlog data ──────────────────────────────────────────────────────────────

def collect_backlog() -> dict:
    path = DATA_DIR / "backlog.json"
    if not path.exists():
        return {"items": [], "counts": {}, "generated_at": _now_iso(), "available": False}

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        items = raw.get("items", [])
        counts = {
            "total": len(items),
            "pending": sum(1 for i in items if i.get("status") == "pending"),
            "in_progress": sum(1 for i in items if i.get("status") == "in_progress"),
            "blocked": sum(1 for i in items if i.get("status") == "blocked"),
            "completed": sum(1 for i in items if i.get("status") == "completed"),
            "cancelled": sum(1 for i in items if i.get("status") == "cancelled"),
        }
        return {"items": items, "counts": counts, "generated_at": _now_iso(), "available": True}
    except (json.JSONDecodeError, KeyError):
        return {"items": [], "counts": {}, "generated_at": _now_iso(), "available": False}


# ── Quality data ──────────────────────────────────────────────────────────────

def collect_quality() -> dict:
    path = DATA_DIR / "quality_scores.jsonl"
    if not path.exists():
        return {"scores": [], "summary": {}, "generated_at": _now_iso(), "available": False}

    scores: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                scores.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not scores:
        return {"scores": [], "summary": {}, "generated_at": _now_iso(), "available": True}

    # Normalize field names: JSONL source uses package_id, HTML expects output_id
    for s in scores:
        if "package_id" in s and "output_id" not in s:
            s["output_id"] = s["package_id"]
        if "output_type" not in s:
            s["output_type"] = "quality_check"

    avg = round(sum(s.get("overall", s.get("score", 0)) for s in scores) / len(scores), 1)
    grades = {}
    for s in scores:
        g = s.get("grade", "N/A")
        grades[g] = grades.get(g, 0) + 1
    ready_count = sum(1 for s in scores if s.get("ready", False))

    summary = {
        "total": len(scores),
        "avg_score": avg,
        "grade_distribution": grades,
        "ready_count": ready_count,
        "last_scored": scores[-1].get("generated_at", scores[-1].get("output_id", "")) if scores else "",
    }

    return {"scores": scores[-50:], "summary": summary, "generated_at": _now_iso(), "available": True}


# ── Template data ─────────────────────────────────────────────────────────────

def collect_templates() -> dict:
    path = TEMPLATES_DIR / "template_registry.json"
    if not path.exists():
        return {"templates": [], "categories": {}, "generated_at": _now_iso(), "available": False}

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        templates_raw = raw.get("templates", {})
        if isinstance(templates_raw, dict):
            entries = list(templates_raw.values())
        elif isinstance(templates_raw, list):
            entries = templates_raw
        else:
            entries = []

        categories: dict[str, int] = {}
        for e in entries:
            cat = e.get("category", "uncategorized")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "templates": entries,
            "categories": categories,
            "total": len(entries),
            "generated_at": _now_iso(),
            "available": True,
        }
    except (json.JSONDecodeError, KeyError):
        return {"templates": [], "categories": {}, "generated_at": _now_iso(), "available": False}


# ── Runs data ─────────────────────────────────────────────────────────────────

def collect_runs() -> dict:
    runs_dir = DATA_DIR / "runs"
    if not runs_dir.exists():
        return {"batches": [], "summary": {}, "generated_at": _now_iso(), "available": False}

    batches = []
    for f in sorted(runs_dir.glob("*.json")):
        try:
            batch = json.loads(f.read_text(encoding="utf-8"))
            batches.append({
                "batch_id": batch.get("batch_id", f.stem),
                "status": batch.get("status", "unknown"),
                "task_count": len(batch.get("tasks", [])),
                "succeeded": sum(1 for r in batch.get("results", []) if r.get("success")),
                "failed": sum(1 for r in batch.get("results", []) if not r.get("success")),
                "total_duration": sum(r.get("duration", 0) for r in batch.get("results", [])),
                "created_at": batch.get("created_at", ""),
                "finished_at": batch.get("finished_at", ""),
            })
        except (json.JSONDecodeError, KeyError):
            continue

    if not batches:
        return {"batches": [], "summary": {}, "generated_at": _now_iso(), "available": True}

    total_tasks = sum(b["task_count"] for b in batches)
    total_succeeded = sum(b["succeeded"] for b in batches)
    summary = {
        "total_batches": len(batches),
        "total_tasks": total_tasks,
        "total_succeeded": total_succeeded,
        "total_failed": sum(b["failed"] for b in batches),
        "success_rate": round(total_succeeded / max(1, total_tasks), 2),
    }

    return {"batches": batches, "summary": summary, "generated_at": _now_iso(), "available": True}


# ── System health ─────────────────────────────────────────────────────────────

def collect_system() -> dict:
    # Disk
    disk = {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent_free": 0}
    try:
        usage = shutil.disk_usage(str(BASE))
        disk = {
            "total_gb": round(usage.total / (1024**3), 1),
            "used_gb": round(usage.used / (1024**3), 1),
            "free_gb": round(usage.free / (1024**3), 1),
            "percent_free": round((usage.free / usage.total) * 100, 1),
        }
    except Exception:
        pass

    # Module health (basic import check)
    modules_to_check = [
        ("live_cockpit", "src.live_cockpit"),
        ("offline_dashboard", "src.offline_dashboard"),
        ("local_search", "src.local_search"),
        ("quality_gate", "src.quality_gate"),
        ("mission_replay", "src.mission_replay"),
    ]
    modules = []
    for name, namespace in modules_to_check:
        try:
            __import__(namespace)
            modules.append({"name": name, "namespace": namespace, "status": "healthy", "imports_ok": True})
        except ImportError:
            modules.append({"name": name, "namespace": namespace, "status": "unknown", "imports_ok": False})

    return {
        "disk": disk,
        "modules": modules,
        "modules_healthy": sum(1 for m in modules if m["status"] == "healthy"),
        "modules_total": len(modules),
        "generated_at": _now_iso(),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def generate_all(quiet: bool = False) -> dict[str, Path]:
    collectors = [
        ("missions.json", collect_missions),
        ("backlog.json", collect_backlog),
        ("quality.json", collect_quality),
        ("templates.json", collect_templates),
        ("runs.json", collect_runs),
        ("system.json", collect_system),
    ]

    generated: dict[str, Path] = {}
    for filename, collector in collectors:
        try:
            data = collector()
            path = _write_json(filename, data)
            generated[filename] = path
            if not quiet:
                print(f"  {filename} — {_summary_line(filename, data)}")
        except Exception as e:
            if not quiet:
                print(f"  {filename} — ERROR: {e}")

    return generated


def _summary_line(filename: str, data: dict) -> str:
    if filename == "missions.json":
        s = data.get("stats", {})
        return f"{s.get('total', 0)} missions ({s.get('open', 0)} open, {s.get('closed', 0)} closed)"
    elif filename == "backlog.json":
        if not data.get("available"):
            return "no data"
        c = data.get("counts", {})
        return f"{c.get('total', 0)} items ({c.get('pending', 0)} pending)"
    elif filename == "quality.json":
        if not data.get("available"):
            return "no data"
        s = data.get("summary", {})
        return f"{s.get('total', 0)} scores, avg {s.get('avg_score', 0)}"
    elif filename == "templates.json":
        cats = data.get("categories", {})
        return f"{data.get('total', 0)} templates in {list(cats.keys())}"
    elif filename == "runs.json":
        s = data.get("summary", {})
        return f"{s.get('total_batches', 0)} batches, {s.get('success_rate', 0)} success rate"
    elif filename == "system.json":
        d = data.get("disk", {})
        m = f"{data.get('modules_healthy', 0)}/{data.get('modules_total', 0)} modules healthy"
        return f"{d.get('percent_free', 0)}% disk free, {m}"
    return "ok"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate cockpit data files")
    parser.add_argument("--quiet", action="store_true", help="Suppress output")
    args = parser.parse_args()

    print(f"Cockpit Data Generator — {_now_iso()}")
    paths = generate_all(quiet=args.quiet)
    print(f"\nGenerated {len(paths)} files -> cockpit/data/")


if __name__ == "__main__":
    main()
