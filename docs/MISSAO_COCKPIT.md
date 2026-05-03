# MISSÃO COCKPIT — OMNIS
# Data: 2026-05-03
# Estado: 213 testes, 8 commits, 73GB livres (8%), 40 drafts needs_review

## REGRAS ABSOLUTAS (não discutir)
# D006: zero HTTP externo. D008: zero delete automático.
# D007: batch approve valida placeholder. Python puro + pathlib.
# pytest antes de commitar. Se quebrar: corrija antes de avançar.

## FASE 1 — omnis disk (15 min)

Criar scripts/disk_analyze.py:

```python
import shutil, subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent

def main():
    total, used, free = shutil.disk_usage("C:/")
    pct = free / total * 100
    warn = " ⚠" if pct < 15 else " ✓"
    print(f"\nDISCO C:  {free//1024**3}GB livres / {total//1024**3}GB ({pct:.1f}%){warn}")

    r = subprocess.run(["docker", "system", "df"], capture_output=True, text=True, timeout=10)
    print(f"\nDOCKER:\n{r.stdout.strip() if r.returncode == 0 else '  docker indisponivel'}")

    logs = sorted((ROOT / "logs").glob("*.jsonl"))
    print("\nLOGS OMNIS:")
    for f in logs:
        print(f"  {f.name:<35} {f.stat().st_size//1024:>6} KB")

    exports = list((ROOT / "data" / "exports").rglob("*.*"))
    total_kb = sum(f.stat().st_size for f in exports if f.is_file()) // 1024
    print(f"\nEXPORTS: {len(exports)} arquivos · {total_kb} KB total")

    print("\nSUGESTOES (nao executadas automaticamente):")
    print("  docker image prune -f")
    print("  docker builder prune -f")

if __name__ == "__main__":
    main()
```

CLI em omnis.py:
```python
@app.command()
def disk():
    """Analisa uso de disco - read-only."""
    import subprocess, sys
    subprocess.run([sys.executable, "scripts/disk_analyze.py"])
```

Teste tests/test_disk_analyze.py:
```python
import shutil
def test_disk_usage_positive():
    total, used, free = shutil.disk_usage("C:/")
    assert total > 0 and free > 0

def test_script_runs(capsys):
    from scripts.disk_analyze import main
    main()
    out = capsys.readouterr().out
    assert "DISCO" in out and "SUGESTOES" in out
```

## FASE 2 — omnis approvals batch (20 min)

Contexto: 40 drafts com status needs_review (nao pending).
Adicionar em src/caption_approval/approvals.py:

```python
from datetime import datetime
import csv

SKIP_PATTERNS = ["[", "]", "TODO", "REVISAR", "PLACEHOLDER"]

def batch_approve(limit: int = 5) -> dict:
    """Aprova ate limit drafts validos de needs_review."""
    drafts = load_drafts()
    candidates = [d for d in drafts if d.get("status") == "needs_review"]
    approved, skipped, reasons = 0, 0, []

    for draft in candidates:
        if approved >= limit:
            break
        content = str(draft.get("content") or draft.get("caption") or "")
        account = str(draft.get("account_id") or draft.get("account") or "")
        reason = None
        if not content.strip():
            reason = f"{draft.get('id','?')}: content vazio"
        elif not account:
            reason = f"{draft.get('id','?')}: sem account_id"
        else:
            for pat in SKIP_PATTERNS:
                if pat in content:
                    reason = f"{draft.get('id','?')}: placeholder '{pat}'"
                    break
        if reason:
            reasons.append(reason)
            skipped += 1
            continue
        draft["status"] = "approved"
        draft["approved_at"] = datetime.utcnow().isoformat()
        approved += 1

    if approved > 0:
        save_drafts(drafts)
        _export_approved_latest(drafts)

    return {"approved": approved, "skipped": skipped, "skip_reasons": reasons}


def _export_approved_latest(drafts: list) -> None:
    from pathlib import Path
    out = Path(__file__).parent.parent.parent / "data" / "exports" / "approved_latest.csv"
    out.parent.mkdir(exist_ok=True)
    approved = [d for d in drafts if d.get("status") == "approved"]
    if not approved:
        return
    fields = list(approved[0].keys())
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(approved)
```

CLI (adicionar ao approvals_app):
```python
@approvals_app.command("batch")
def approvals_batch(limit: int = typer.Option(5, help="Maximo de drafts a aprovar")):
    """Aprova ate N drafts validos sem placeholders."""
    from src.caption_approval.approvals import batch_approve
    r = batch_approve(limit=limit)
    print(f"Aprovados: {r['approved']} | Pulados: {r['skipped']}")
    for s in r["skip_reasons"]:
        print(f"  skip: {s}")

@approvals_app.command("status")
def approvals_status():
    """Contagem de drafts por status."""
    from src.caption_approval.approvals import load_drafts
    from collections import Counter
    counts = Counter(d.get("status","?") for d in load_drafts())
    for s, n in sorted(counts.items()):
        print(f"  {s:<20} {n}")
```

Testes tests/test_batch_approve.py — adaptar ao padrao de test_caption_approval.py existente:
- draft valido -> aprovado
- draft com placeholder -> skipped com reason
- draft sem content -> skipped
- limit=2 com 5 validos -> 2 aprovados
- zero drafts -> approved=0

## FASE 3 — omnis briefing (25 min)

Criar src/reports/briefing.py:

```python
import shutil, subprocess, json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "data"
LOGS = ROOT / "logs"

def _disk_score():
    total, _, free = shutil.disk_usage("C:/")
    pct = free / total * 100
    return min(100, int(pct * 5)), f"{free//1024**3}GB ({pct:.0f}%)" + (" ⚠" if pct < 15 else "")

def _pipeline_score():
    try:
        drafts = [json.loads(l) for l in (DATA/"caption_drafts.jsonl").read_text(encoding="utf-8").strip().splitlines()]
        approved = sum(1 for d in drafts if d.get("status") == "approved")
        pct = approved / len(drafts) * 100 if drafts else 0
        return min(100, int(pct * 2)), f"{approved}/{len(drafts)} aprovados"
    except Exception:
        return 0, "erro ao ler drafts"

def _containers_score():
    try:
        r = subprocess.run(["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
                           capture_output=True, text=True, timeout=8)
        lines = [l for l in r.stdout.strip().splitlines() if l]
        unhealthy = [l.split("\t")[0] for l in lines if "unhealthy" in l.lower()]
        healthy = len(lines) - len(unhealthy)
        score = int(healthy / len(lines) * 100) if lines else 50
        return score, f"{healthy}/{len(lines)} saudaveis", unhealthy
    except Exception:
        return 50, "docker indisponivel", []

def _queue_score():
    try:
        items = [json.loads(l) for l in (DATA/"content_queue.jsonl").read_text(encoding="utf-8").strip().splitlines()]
        ready = sum(1 for i in items if i.get("status") == "caption_ready")
        return min(100, int(ready / len(items) * 200)) if items else 0, f"{ready}/{len(items)} prontos"
    except Exception:
        return 0, "erro ao ler queue"

def generate(save: bool = False) -> str:
    disk_s, disk_l = _disk_score()
    pipe_s, pipe_l = _pipeline_score()
    cont_s, cont_l, unhealthy = _containers_score()
    queue_s, queue_l = _queue_score()

    score = int(disk_s*0.30 + pipe_s*0.40 + cont_s*0.20 + queue_s*0.10)
    icon = "ok" if score >= 80 else ("aviso" if score >= 60 else "critico")

    actions = []
    _, _, free = shutil.disk_usage("C:/")
    total, _, _ = shutil.disk_usage("C:/")
    if free/total*100 < 15:
        actions.append("omnis disk  (8% livre - analisar espaco)")
    if pipe_s < 20:
        actions.append("omnis approvals batch --limit 10")
    if unhealthy:
        actions.append(f"containers unhealthy: {', '.join(unhealthy[:2])}")
    actions.append("Configurar META_APP_SECRET no publisher-os/.env")
    actions = actions[:3]

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    sep = "=" * 44
    out = [f"\n{sep}", f"  OMNIS BRIEFING {now}", sep,
           f"\nSAUDE: {score}/100 [{icon}]",
           f"\nPIPELINE:    {pipe_l}",
           f"DISCO:       {disk_l}",
           f"CONTAINERS:  {cont_l}",
           "\nPROXIMAS 3 ACOES:"]
    for i, a in enumerate(actions, 1):
        out.append(f"  {i}. {a}")
    out.append(f"\n{sep}\n")
    result = "\n".join(out)

    if save:
        (LOGS / f"briefing_{datetime.now().strftime('%Y-%m-%d')}.md").write_text(result, encoding="utf-8")
        with (LOGS / "health_scores.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"date": now, "score": score}) + "\n")

    return result
```

CLI:
```python
@app.command()
def briefing(save: bool = typer.Option(False, "--save")):
    """Health score + top 3 acoes do dia."""
    from src.reports import briefing as b
    print(b.generate(save=save))
```

Testes tests/test_briefing.py:
- score entre 0 e 100
- output tem PIPELINE, DISCO, ACOES
- docker falha -> nao quebra
- save=True cria arquivo em logs/

## FASE FINAL

Adicionar ao .gitignore:
```
data/exports/
logs/briefing_*.md
```

Criar data/exports/.gitignore com conteudo: *

Rodar pytest. Se verde:
```
git add -A
git commit -m "feat(cockpit): disk analyze, batch approve, briefing

- scripts/disk_analyze.py: read-only, sugere sem executar (D008)
- batch_approve(limit=N): valida placeholders, skipa invalidos (D007)
- omnis approvals batch/status
- src/reports/briefing.py: health score + top 3 acoes
- omnis briefing [--save]
- D003/D006/D007/D008 respeitadas
- Tests: N passed"
```

## VERIFICACAO FINAL

```
python omnis.py disk
python omnis.py approvals batch
python omnis.py approvals status
python omnis.py briefing
python -m pytest tests/ -q
```

Nao fazer: HTTP externo, ler .env, docker prune automatico, tocar publisher-os/.claude/JARVIS_OS.

Bora.
