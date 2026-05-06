#!/usr/bin/env python3
"""
disk_audit_readonly.py — Scan disk usage and identify cleanup candidates.

READ-ONLY: This script NEVER deletes, moves, or modifies any files.
Uses bash `du` for fast directory sizing on Windows (Git Bash).
Output: JSON report + human-readable summary.
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
REPO = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO / "docs"

SCAN_TARGETS = [
    ("omnis-control", HOME / "omnis-control"),
    ("publisher-os", HOME / "publisher-os"),
    ("JARVIS_OS", HOME / "JARVIS_OS"),
    ("llm-router", HOME / "llm-router"),
    ("biblioteca_sabedoria", HOME / "biblioteca_sabedoria"),
    ("daily-prophet-hotels", HOME / "daily-prophet-hotels"),
    (".claude", HOME / ".claude"),
    ("Downloads/instagram-publisher", HOME / "Downloads" / "instagram-publisher"),
]

DOCKER_RECLAIM_CMDS = [
    {"cmd": "docker image prune -f", "risk": "safe", "est_gb": 54},
    {"cmd": "docker builder prune -f", "risk": "safe", "est_gb": 16},
    {"cmd": "docker system prune -a --volumes", "risk": "dangerous", "est_gb": 75},
]


def _format_size(bytes_val: int) -> str:
    if bytes_val < 0:
        return "? B"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(bytes_val) < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


def _du(path: Path) -> int:
    """Get directory size via bash du (fast on Windows Git Bash)."""
    try:
        result = subprocess.run(
            ["du", "-sb", str(path)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            size_str = result.stdout.split("\t")[0]
            return int(size_str)
    except (subprocess.TimeoutExpired, OSError, ValueError, IndexError):
        pass
    return -1


def scan_project_dirs() -> list:
    results = []
    for name, path in SCAN_TARGETS:
        if path.exists():
            print(f"  sizing {name}...", end=" ", flush=True)
            size = _du(path)
            status = _format_size(size) if size >= 0 else "ERROR"
            print(status)
            results.append({
                "name": name, "path": str(path),
                "size_bytes": max(size, 0), "size_human": status,
                "exists": True, "accessible": size >= 0
            })
        else:
            results.append({
                "name": name, "path": str(path),
                "size_bytes": 0, "size_human": "0 B",
                "exists": False, "accessible": False
            })
    return results


def find_nm_dirs(base: Path) -> list:
    """Find node_modules dirs using bash find."""
    results = []
    try:
        result = subprocess.run(
            ["find", str(base), "-name", "node_modules", "-type", "d", "-maxdepth", "4"],
            capture_output=True, text=True, timeout=15
        )
        dirs = [d.strip() for d in result.stdout.split("\n") if d.strip()]
        for d in dirs:
            p = Path(d)
            size = _du(p)
            results.append({
                "path": d,
                "size_bytes": max(size, 0),
                "size_human": _format_size(size) if size >= 0 else "ERROR",
                "risk": "safe"
            })
    except (subprocess.TimeoutExpired, OSError):
        pass
    return results


def find_large_files(base: Path, min_mb: int = 100) -> list:
    """Find files > min_mb using bash find (fast)."""
    results = []
    try:
        result = subprocess.run(
            ["find", str(base), "-type", "f", "-size", f"+{min_mb}M",
             "-not", "-path", "*/node_modules/*",
             "-not", "-path", "*/.git/*",
             "-not", "-path", "*/AppData/*"],
            capture_output=True, text=True, timeout=30
        )
        files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
        for fp in files:
            try:
                size = os.path.getsize(fp)
                results.append({"path": fp, "size_bytes": size, "size_human": _format_size(size)})
            except OSError:
                pass
    except (subprocess.TimeoutExpired, OSError):
        pass
    results.sort(key=lambda x: x["size_bytes"], reverse=True)
    return results[:30]


def find_archives(base: Path) -> list:
    """Find zip/tar.gz/rar files."""
    results = []
    total = 0
    count = 0
    try:
        result = subprocess.run(
            ["find", str(base), "-type", "f", "(", "-name", "*.zip", "-o",
             "-name", "*.tar.gz", "-o", "-name", "*.tgz", "-o", "-name", "*.rar",
             ")", "-not", "-path", "*/node_modules/*", "-not", "-path", "*/.git/*"],
            capture_output=True, text=True, timeout=30
        )
        files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
        for fp in files:
            try:
                size = os.path.getsize(fp)
                total += size
                count += 1
                results.append({"path": fp, "size_bytes": size, "size_human": _format_size(size)})
            except OSError:
                pass
    except (subprocess.TimeoutExpired, OSError):
        pass
    results.sort(key=lambda x: x["size_bytes"], reverse=True)
    return {"count": count, "total_bytes": total, "total_human": _format_size(total), "files": results[:20]}


def disk_full_summary() -> dict:
    """Get overall disk usage."""
    try:
        usage = shutil.disk_usage("/")
        return {
            "total_gb": round(usage.total / 1e9, 1),
            "used_gb": round((usage.total - usage.free) / 1e9, 1),
            "free_gb": round(usage.free / 1e9, 1),
            "percent_free": round(usage.free / usage.total * 100, 1)
        }
    except Exception:
        return {"error": "unavailable"}


import shutil


def main():
    print("=" * 60)
    print(" OMNIS — Disk & Infra Safety Audit (READ-ONLY)")
    print(f" Started: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    report = {
        "generated_at": datetime.now().isoformat(),
        "repo": str(REPO),
    }

    # 0. Overall disk
    print("[0/5] Overall disk usage...")
    disk = disk_full_summary()
    report["disk_summary"] = disk
    print(f"  {disk['free_gb']} GB free / {disk['total_gb']} GB ({disk['percent_free']}%)")
    print()

    # 1. Project directories
    print("[1/5] Project directories...")
    projects = scan_project_dirs()
    report["project_directories"] = projects
    print()

    # 2. node_modules
    print("[2/5] node_modules scan (maxdepth 4)...")
    all_nm = []
    for name, path in SCAN_TARGETS:
        if path.exists():
            print(f"  searching {name}...", end=" ", flush=True)
            found = find_nm_dirs(path)
            all_nm.extend(found)
            print(f"{len(found)} found")
    report["node_modules"] = all_nm
    total_nm = sum(nm["size_bytes"] for nm in all_nm)
    print(f"  TOTAL node_modules: {len(all_nm)} dirs, {_format_size(total_nm)}")
    print()

    # 3. Large files
    print("[3/5] Large files (>100 MB)...")
    all_large = []
    for name, path in SCAN_TARGETS:
        if path.exists():
            print(f"  searching {name}...", end=" ", flush=True)
            found = find_large_files(path)
            all_large.extend(found)
            print(f"{len(found)} found")
    all_large.sort(key=lambda x: x["size_bytes"], reverse=True)
    all_large = all_large[:30]
    report["large_files"] = all_large
    for lf in all_large[:15]:
        print(f"  {lf['size_human']:>10}  {lf['path']}")
    print()

    # 4. Archives
    print("[4/5] Archive files (.zip, .tar.gz, .tgz, .rar)...")
    archives = find_archives(REPO.parent)
    report["archives"] = archives
    arches_sorted = sorted(archives["files"], key=lambda x: x["size_bytes"], reverse=True)
    print(f"  {archives['count']} files, {archives['total_human']} total")
    for a in arches_sorted[:10]:
        print(f"  {a['size_human']:>10}  {a['path']}")
    print()

    # 5. Docker reclaimable
    print("[5/5] Docker reclaimable (from omnis doctor)...")
    report["docker_reclaimable"] = DOCKER_RECLAIM_CMDS
    total_docker_safe = sum(d["est_gb"] for d in DOCKER_RECLAIM_CMDS if d["risk"] == "safe")
    print(f"  Safe reclaim: ~{total_docker_safe} GB (docker image prune + builder prune)")
    print(f"  Dangerous: ~75 GB (docker system prune --volumes)")
    print()

    # Summary
    print("=" * 60)
    print(" SUMMARY")
    print("=" * 60)
    print(f"  Disk:     {disk['free_gb']} GB free ({disk['percent_free']}%)")
    print(f"  Projects: {len(projects)} dirs ({sum(p['size_bytes'] for p in projects) / 1e9:.1f} GB)")
    print(f"  node_modules: {len(all_nm)} dirs ({total_nm / 1e9:.1f} GB)")
    print(f"  Archives: {archives['count']} files ({archives['total_bytes'] / 1e9:.1f} GB)")
    print(f"  Docker safe prune: ~{total_docker_safe} GB")
    print()
    print("  See docs/DISK_CLEANUP_CANDIDATES.md for detailed plan")
    print("  See docs/DISK_INFRA_SAFETY_PLAN.md for execution order")
    print()

    report_path = OUTPUT_DIR / "disk_audit_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  Report saved: {report_path}")

if __name__ == "__main__":
    main()
