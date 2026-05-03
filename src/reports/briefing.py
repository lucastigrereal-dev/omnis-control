"""Briefing — Health score + top 3 acoes do dia (Fase Cockpit)."""

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
LOGS = ROOT / "logs"


def _disk_score():
    total, _, free = shutil.disk_usage("C:/")
    pct = free / total * 100
    label = f"{free // 1024 ** 3}GB ({pct:.0f}%)" + (" [!]" if pct < 15 else "")
    return min(100, int(pct * 5)), label


def _pipeline_score():
    try:
        drafts_path = DATA / "caption_drafts.jsonl"
        if not drafts_path.is_file():
            return 0, "sem arquivo de drafts"
        raw = drafts_path.read_text(encoding="utf-8").strip()
        if not raw:
            return 0, "nenhum draft"
        drafts = [json.loads(l) for l in raw.splitlines()]
        approved = sum(1 for d in drafts if d.get("status") == "approved")
        pct = approved / len(drafts) * 100 if drafts else 0
        return min(100, int(pct * 2)), f"{approved}/{len(drafts)} aprovados"
    except Exception as e:
        return 0, f"erro: {e}"


def _containers_score():
    try:
        r = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=8,
        )
        lines = [l for l in r.stdout.strip().splitlines() if l]
        unhealthy = [l.split("\t")[0] for l in lines if "unhealthy" in l.lower()]
        healthy = len(lines) - len(unhealthy)
        score = int(healthy / len(lines) * 100) if lines else 50
        return score, f"{healthy}/{len(lines)} saudaveis", unhealthy
    except Exception:
        return 50, "docker indisponivel", []


def _queue_score():
    try:
        queue_path = DATA / "content_queue.jsonl"
        if not queue_path.is_file():
            return 0, "sem arquivo de queue"
        raw = queue_path.read_text(encoding="utf-8").strip()
        if not raw:
            return 0, "fila vazia"
        items = [json.loads(l) for l in raw.splitlines()]
        ready = sum(1 for i in items if i.get("status") == "caption_ready")
        score = min(100, int(ready / len(items) * 200)) if items else 0
        return score, f"{ready}/{len(items)} prontos"
    except Exception as e:
        return 0, f"erro: {e}"


def generate(save: bool = False) -> str:
    """Gera o briefing com health score + top 3 acoes."""
    disk_s, disk_l = _disk_score()
    pipe_s, pipe_l = _pipeline_score()
    cont_s, cont_l, unhealthy = _containers_score()
    queue_s, queue_l = _queue_score()

    score = int(disk_s * 0.30 + pipe_s * 0.40 + cont_s * 0.20 + queue_s * 0.10)
    icon = "ok" if score >= 80 else ("aviso" if score >= 60 else "critico")

    actions = []
    total, _, free = shutil.disk_usage("C:/")
    if free / total * 100 < 15:
        actions.append("omnis disk  (8% livre - analisar espaco)")
    if pipe_s < 20:
        actions.append("omnis approvals batch --limit 10")
    if unhealthy:
        actions.append(f"containers unhealthy: {', '.join(unhealthy[:2])}")
    # Akasha health
    try:
        from src.memory.akasha_reader import ping as akasha_ping
        if not akasha_ping():
            actions.append("Akasha offline — verificar container akasha-postgres")
    except Exception:
        actions.append("Akasha reader indisponivel")
    actions.append("Configurar META_APP_SECRET no publisher-os/.env")
    actions = actions[:3]

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sep = "=" * 44
    lines = [
        f"\n{sep}",
        f"  OMNIS BRIEFING {now}",
        sep,
        f"\nSAUDE: {score}/100 [{icon}]",
        f"\nPIPELINE:    {pipe_l}",
        f"DISCO:       {disk_l}",
        f"CONTAINERS:  {cont_l}",
        "\nPROXIMAS 3 ACOES:",
    ]
    for i, a in enumerate(actions, 1):
        lines.append(f"  {i}. {a}")
    lines.append(f"\n{sep}\n")
    result = "\n".join(lines)

    if save:
        date_str = datetime.now().strftime("%Y-%m-%d")
        (LOGS / f"briefing_{date_str}.md").write_text(result, encoding="utf-8")
        with (LOGS / "health_scores.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"date": now, "score": score}, ensure_ascii=False) + "\n")

    return result

