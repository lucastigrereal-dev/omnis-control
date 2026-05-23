"""
Video Pipeline Checker — Módulo de diagnóstico read-only.

Classifica o ecossistema quanto à maturidade do pipeline de vídeo:
  - operational: 4+ de 5 sinais fortes
  - partial: 2+ sinais de código executável ou integração real
  - documented_only: só .md / prompts / roadmap
  - not_found: nenhum sinal relevante
  - scan_timeout_partial: scan excedeu timeout
"""

import os
import time

import yaml

_ROOT = os.path.normpath(os.getenv("OMNIS_ROOT", os.path.expanduser("~/omnis-control")))
_CLAUDE = os.path.normpath(os.getenv("CLAUDE_DIR", os.path.expanduser("~/.claude")))
_PUB_OS = os.path.normpath(os.getenv("PUBLISHER_OS_DIR", os.path.expanduser("~/publisher-os")))

SEARCH_ROOTS = [
    os.path.join(_CLAUDE, "skills"),
    _PUB_OS,
    os.path.normpath(os.getenv("JARVIS_OS_DIR", os.path.expanduser("~/JARVIS_OS"))),
    _ROOT,
]
CONFIG_PATH = os.path.join(_ROOT, "config", "paths.yaml")
SCAN_TIMEOUT_S = 30


def _load_config() -> dict[str, object]:
    if not os.path.isfile(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("video_pipeline", {})
    except (yaml.YAMLError, OSError):
        return {}


def _scan_local_video_files(
    roots: list[str],
    exts: list[str],
    timeout_s: int,
) -> dict[str, object]:
    """Scan local directories for video files, with timeout."""
    deadline = time.time() + timeout_s
    found = []
    timed_out = False
    for root in roots:
        if time.time() > deadline:
            timed_out = True
            break
        if not os.path.isdir(root):
            continue
        try:
            for dirpath, _dirnames, filenames in os.walk(root, topdown=True):
                if time.time() > deadline:
                    timed_out = True
                    break
                for f in filenames:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in exts:
                        found.append(os.path.join(dirpath, f))
        except (OSError, PermissionError):
            continue
    return {"files": found, "count": len(found), "timed_out": timed_out}


def _check_keyword_in_path(roots: list[str], keywords: list[str]) -> list[dict[str, object]]:
    """Check for files/dirs matching video-related keywords."""
    evidence = []
    seen = set()
    for root in roots:
        if not os.path.isdir(root):
            continue
        try:
            for entry in os.listdir(root):
                entry_lower = entry.lower()
                for kw in keywords:
                    if kw in entry_lower:
                        dedup_key = f"{root}/{entry}"
                        if dedup_key not in seen:
                            seen.add(dedup_key)
                            evidence.append({
                                "path": os.path.join(root, entry),
                                "keyword": kw,
                                "type": "dir" if os.path.isdir(os.path.join(root, entry)) else "file",
                            })
                        break
        except (OSError, PermissionError):
            continue
    return evidence


def _check_video_to_content_skill() -> list[dict[str, object]]:
    """Check for video_to_content skill."""
    evidence = []
    skill_path = os.path.join(_CLAUDE, "skills", "video_to_content")
    if os.path.isdir(skill_path):
        evidence.append({
            "path": skill_path,
            "keyword": "video_to_content/run.py",
            "type": "skill_executable",
        })
    return evidence


def _check_argos_bridge_skill() -> list[dict[str, object]]:
    """Check for argos-bridge skill."""
    evidence = []
    skill_path = os.path.join(_CLAUDE, "skills", "argos-bridge")
    if os.path.isdir(skill_path):
        evidence.append({
            "path": skill_path,
            "keyword": "argos-bridge",
            "type": "skill_integration",
        })
    return evidence


def _check_publisher_video_code() -> list[dict[str, object]]:
    """Scan publisher-os for video/media related code."""
    evidence = []
    pub_root = _PUB_OS
    video_terms = ["video", "media", "asset", "reel", "scheduled", "published"]
    if not os.path.isdir(pub_root):
        return evidence
    try:
        for dirpath, _dirnames, filenames in os.walk(pub_root, topdown=True):
            for f in filenames:
                if f.endswith(".py"):
                    fpath = os.path.join(dirpath, f)
                    try:
                        with open(fpath, encoding="utf-8", errors="ignore") as fh:
                            content = fh.read(5000).lower()
                        for term in video_terms:
                            if term in content:
                                evidence.append({
                                    "path": fpath,
                                    "keyword": term,
                                    "type": "publisher_code",
                                })
                                break
                    except (OSError, PermissionError):
                        continue
    except (OSError, PermissionError):
        pass
    return evidence


def _check_video_asset_registry() -> dict[str, object]:
    """Check if the local Video Asset Registry exists and has data."""
    registry_path = os.path.join(_ROOT, "data", "video_assets.jsonl")
    result = {
        "exists": os.path.isfile(registry_path),
        "asset_count": 0,
    }
    if result["exists"]:
        try:
            with open(registry_path, encoding="utf-8") as f:
                result["asset_count"] = sum(1 for line in f if line.strip())
        except (OSError, PermissionError):
            pass
    return result


def _check_account_registry() -> dict[str, object]:
    """Check if the Account Registry exists and has data."""
    path = os.path.join(_ROOT, "data", "accounts.jsonl")
    result = {"exists": os.path.isfile(path), "account_count": 0}
    if result["exists"]:
        try:
            with open(path, encoding="utf-8") as f:
                result["account_count"] = sum(1 for line in f if line.strip())
        except (OSError, PermissionError):
            pass
    return result


def _check_content_queue() -> dict[str, object]:
    """Check if the Content Queue file exists and has data."""
    path = os.path.join(_ROOT, "data", "content_queue.jsonl")
    result = {"exists": os.path.isfile(path), "item_count": 0}
    if result["exists"]:
        try:
            with open(path, encoding="utf-8") as f:
                result["item_count"] = sum(1 for line in f if line.strip())
        except (OSError, PermissionError):
            pass
    return result


def check() -> dict[str, object]:
    """Run all checks and return structured diagnosis."""
    start = time.time()

    config = _load_config()
    search_roots = config.get("local_search_roots", SEARCH_ROOTS)
    known_exts = config.get("known_extensions", [".mp4", ".mov", ".m4v", ".avi", ".webm"])
    keywords = config.get("keywords", [])

    scans = _run_scans(search_roots, known_exts, keywords)
    all_evidence = _build_all_evidence(scans)
    signals = _build_signals(scans, all_evidence)
    deduped_evidence = _dedupe_evidence(all_evidence)
    classification, confidence = _classify_pipeline(scans, signals, deduped_evidence)
    risks = _build_risks(classification, signals, scans["registry"])

    duration_ms = int((time.time() - start) * 1000)

    return {
        "classification": classification,
        "confidence": confidence,
        "signals": signals,
        "counts": {
            "local_video_files": scans["video_files"]["count"],
            "keyword_hits": len(scans["keyword_hits"]),
            "total_evidence": len(deduped_evidence),
            "registry_assets": scans["registry"]["asset_count"],
            "registry_accounts": scans["accounts_reg"]["account_count"],
            "queue_items": scans["content_queue"]["item_count"],
            "scan_duration_ms": duration_ms,
            "scan_timed_out": scans["video_files"].get("timed_out", False),
        },
        "evidence": deduped_evidence[:20],
        "evidence_truncated": len(deduped_evidence) > 20 if deduped_evidence else False,
        "risks": risks,
    }


def _run_scans(
    search_roots: list[str],
    known_exts: list[str],
    keywords: list[str],
) -> dict[str, object]:
    video_files = _scan_local_video_files(search_roots, known_exts, SCAN_TIMEOUT_S)
    return {
        "video_files": video_files,
        "keyword_hits": _check_keyword_in_path(search_roots, keywords),
        "vtoc_evidence": _check_video_to_content_skill(),
        "argos_evidence": _check_argos_bridge_skill(),
        "pub_evidence": _check_publisher_video_code(),
        "registry": _check_video_asset_registry(),
        "accounts_reg": _check_account_registry(),
        "content_queue": _check_content_queue(),
    }


def _build_all_evidence(scans: dict[str, object]) -> list[dict[str, object]]:
    all_evidence = (
        scans["keyword_hits"]
        + scans["vtoc_evidence"]
        + scans["argos_evidence"]
        + scans["pub_evidence"]
    )
    registry = scans["registry"]
    accounts_reg = scans["accounts_reg"]
    content_queue = scans["content_queue"]
    if registry["exists"]:
        all_evidence.append({
            "path": os.path.join(_ROOT, "data", "video_assets.jsonl"),
            "keyword": "video_asset_registry",
            "type": "registry",
        })
    if accounts_reg["exists"]:
        all_evidence.append({
            "path": os.path.join(_ROOT, "data", "accounts.jsonl"),
            "keyword": "instagram_account_mapping",
            "type": "registry",
        })
    if content_queue["exists"]:
        all_evidence.append({
            "path": os.path.join(_ROOT, "data", "content_queue.jsonl"),
            "keyword": "daily_content_queue",
            "type": "registry",
        })
    return all_evidence


def _build_signals(
    scans: dict[str, object],
    all_evidence: list[dict[str, object]],
) -> dict[str, bool]:
    video_files = scans["video_files"]
    vtoc_evidence = scans["vtoc_evidence"]
    argos_evidence = scans["argos_evidence"]
    registry = scans["registry"]
    accounts_reg = scans["accounts_reg"]
    content_queue = scans["content_queue"]
    return {
        "local_video_files_found": video_files["count"] > 0,
        "google_drive_code_found": any("drive" in str(e.get("keyword", "")).lower() for e in all_evidence),
        "video_ingestion_code_found": bool(vtoc_evidence) or any(
            e.get("keyword") in ("video", "videos") and e.get("type") == "publisher_code"
            for e in all_evidence
        ),
        "video_asset_registry_found": registry["exists"] and registry["asset_count"] > 0,
        "video_asset_schema_found": any(
            e.get("keyword") in ("asset", "assets") and e.get("type") in ("publisher_code", "dir", "file")
            for e in all_evidence
        ),
        "content_queue_found": any(
            "queue" in str(e.get("keyword", "")).lower() for e in all_evidence
        ),
        "daily_queue_found": any(
            "queue" in str(e.get("keyword", "")).lower() for e in all_evidence
        ),
        "caption_generation_found": any(
            e.get("keyword") in ("caption", "hashtags", "seogram") for e in all_evidence
        ),
        "publisher_integration_found": bool(argos_evidence) or any(
            e.get("keyword") in ("publisher", "scheduled", "published") for e in all_evidence
        ),
        "instagram_account_mapping_found": any(
            e.get("keyword") in ("instagram", "instagram_account_mapping") for e in all_evidence
        ),
        "account_registry_found": accounts_reg["exists"] and accounts_reg["account_count"] > 0,
        "content_queue_found_explicit": content_queue["exists"] and content_queue["item_count"] > 0,
        "used_or_published_marker_found": any(
            e.get("keyword") in ("scheduled", "published", "calendar") for e in all_evidence
        ),
    }


def _dedupe_evidence(all_evidence: list[dict[str, object]]) -> list[dict[str, object]]:
    seen_paths = set()
    deduped_evidence = []
    for evidence in all_evidence:
        if evidence["path"] not in seen_paths:
            seen_paths.add(evidence["path"])
            deduped_evidence.append(evidence)
    return deduped_evidence


def _classify_pipeline(
    scans: dict[str, object],
    signals: dict[str, bool],
    deduped_evidence: list[dict[str, object]],
) -> tuple[str, str]:
    strong_signals = [
        signals["video_asset_registry_found"] or signals["video_asset_schema_found"],
        signals["content_queue_found"] or signals["daily_queue_found"],
        signals["publisher_integration_found"],
        signals["instagram_account_mapping_found"],
        signals["used_or_published_marker_found"],
    ]
    strong_count = sum(1 for signal in strong_signals if signal)
    partial_signals = [
        signals["video_ingestion_code_found"],
        signals["caption_generation_found"],
        signals["google_drive_code_found"],
        signals["local_video_files_found"],
        bool(scans["vtoc_evidence"]),
        bool(scans["argos_evidence"]),
        bool(scans["pub_evidence"]),
    ]
    partial_count = sum(1 for signal in partial_signals if signal)
    has_executable_code = (
        bool(scans["vtoc_evidence"])
        or bool(scans["argos_evidence"])
        or bool(scans["pub_evidence"])
    )

    if scans["video_files"].get("timed_out"):
        return "scan_timeout_partial", "low"
    if strong_count >= 4:
        return "operational", "high"
    if has_executable_code and partial_count >= 2:
        return "partial", "medium"
    if has_executable_code:
        return "partial", "low"
    if deduped_evidence:
        return "documented_only", "low"
    return "not_found", "high"


def _build_risks(
    classification: str,
    signals: dict[str, bool],
    registry: dict[str, object],
) -> list[str]:
    risks = []
    if classification == "not_found":
        risks.append("Nenhum pipeline de vídeo detectado — conteúdo de vídeo é gerenciado manualmente?")
    if classification == "documented_only":
        risks.append("Pipeline de vídeo documentado mas sem código executável — risco de defasagem entre docs e implementação.")
    if classification == "scan_timeout_partial":
        risks.append("Scan parcial por timeout — pode haver artefatos de vídeo não detectados.")
    if not signals.get("instagram_account_mapping_found"):
        risks.append("Nenhum mapeamento de conta Instagram para conteúdo de vídeo encontrado — publicação pode ser manual.")
    if not signals.get("used_or_published_marker_found"):
        risks.append(
            "Nenhum marcador de usado/publicado/agendado encontrado — "
            "não é possível distinguir conteúdo pendente de publicado."
        )
    if registry["exists"] and registry["asset_count"] == 0:
        risks.append("Registro de vídeo encontrado mas vazio — nenhum asset importado ainda.")
    return risks
