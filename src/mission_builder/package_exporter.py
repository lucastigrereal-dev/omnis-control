"""Mission Package Exporter — writes mission package to disk.

Creates:
  exports/mission_packages/<mission_id>/
    01_mission_brief.md
    02_context_used.md
    03_execution_plan.md
    04_outputs/        (empty dir)
    05_exports/        (empty dir)
    06_next_action.md
    mission_manifest.json

NUNCA publica. NUNCA chama Meta. NUNCA aciona OAuth.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from src.mission_builder.models import MissionPlan, MissionPackageManifest
from src.mission_builder.errors import MissionPackageError

BASE = Path(__file__).resolve().parent.parent.parent
PACKAGES_ROOT = BASE / "exports" / "mission_packages"


def _safe_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def export_package(
    plan: MissionPlan,
    packages_root: Path = PACKAGES_ROOT,
) -> MissionPackageManifest:
    """Write mission package to disk. Returns manifest."""
    pkg_dir = packages_root / plan.mission_id
    try:
        pkg_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise MissionPackageError(f"Cannot create package dir: {exc}") from exc

    files_created = []

    # 01 — Mission Brief
    brief = _build_brief(plan)
    _safe_write(pkg_dir / "01_mission_brief.md", brief)
    files_created.append("01_mission_brief.md")

    # 02 — Context Used
    context = _build_context(plan)
    _safe_write(pkg_dir / "02_context_used.md", context)
    files_created.append("02_context_used.md")

    # 03 — Execution Plan
    exec_plan = _build_execution_plan(plan)
    _safe_write(pkg_dir / "03_execution_plan.md", exec_plan)
    files_created.append("03_execution_plan.md")

    # 04 — Outputs dir (empty)
    (pkg_dir / "04_outputs").mkdir(exist_ok=True)
    files_created.append("04_outputs/")

    # 05 — Exports dir (empty)
    (pkg_dir / "05_exports").mkdir(exist_ok=True)
    files_created.append("05_exports/")

    # 06 — Next Action
    next_action = _build_next_action(plan)
    _safe_write(pkg_dir / "06_next_action.md", next_action)
    files_created.append("06_next_action.md")

    # manifest
    manifest = MissionPackageManifest(
        mission_id=plan.mission_id,
        request_text=plan.request_text,
        intent=plan.intent,
        deliverable=plan.deliverable,
        account_handle=plan.account_handle,
        package_dir=str(pkg_dir),
        files=files_created,
        dry_run=plan.dry_run,
        created_at=plan.created_at,
    )
    _safe_write(
        pkg_dir / "mission_manifest.json",
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2),
    )
    files_created.append("mission_manifest.json")
    manifest.files = files_created
    return manifest


def _build_brief(plan: MissionPlan) -> str:
    return f"""# Mission Brief — {plan.mission_id}

**Pedido:** {plan.request_text}

**Intent detectado:** {plan.intent}
**Entregável:** {plan.deliverable}
**Formato:** {plan.format}
**Conta alvo:** @{plan.account_handle}
**Objetivo:** {plan.objective}
**Slots estimados:** {plan.estimated_slots}
**Criado em:** {plan.created_at}
**Dry-run:** {"Sim" if plan.dry_run else "Nao"}

---

> NUNCA publicar sem aprovacao humana.
> NUNCA enviar para Meta sem OAuth validado (0/5 contas prontas).
"""


def _build_context(plan: MissionPlan) -> str:
    return f"""# Contexto Usado — {plan.mission_id}

**Conta:** @{plan.account_handle}
**Intent:** {plan.intent}
**Descricao:** {plan.description or "(sem descricao)"}

## Fontes de contexto consultadas

- [ ] Context Pack (@{plan.account_handle}) — verificar com `jarvis knowledge context-get {plan.account_handle}`
- [ ] Brand Kit (@{plan.account_handle}) — verificar com `jarvis delivery brand-kit-get {plan.account_handle}`
- [ ] Knowledge Packs relevantes — verificar com `jarvis knowledge pack-list`
- [ ] Akasha — offline nesta sessao (adicionar manualmente se disponivel)

## Fatos relevantes a preencher

| Fato | Valor |
|---|---|
| Cidade-alvo | _preencher_ |
| Tom | _preencher_ |
| Produto/servico | _preencher_ |
| Campanha de referencia | _preencher_ |
"""


def _build_execution_plan(plan: MissionPlan) -> str:
    steps_md = "\n".join(f"- [ ] {step}" for step in plan.steps)
    return f"""# Plano de Execucao — {plan.mission_id}

**Intent:** {plan.intent} | **Formato:** {plan.format}
**Slots:** {plan.estimated_slots}

## Etapas

{steps_md}

## Outputs esperados

- Pacote offline em: `exports/offline_factory/`
- Render HTML em: `exports/rendered/`
- Entrega final em: `exports/client_delivery/`

## Comandos relacionados

```powershell
# Criar pacote offline (carrossel)
python jarvis.py offline package-carousel <queue_id>

# Pontuar qualidade
python jarvis.py quality package <package_id>

# Ver dashboard
python jarvis.py dashboard offline
```
"""


def _build_next_action(plan: MissionPlan) -> str:
    cmd_map = {
        "carousel": f"python jarvis.py offline package-carousel <queue_id> --account {plan.account_handle}",
        "reels": f"python jarvis.py offline package-reels <queue_id>",
        "campaign": f"python jarvis.py campaign create --name \"{plan.request_text[:30]}\" --account {plan.account_handle}",
        "post": f"python jarvis.py offline package-post <queue_id>",
        "story": f"python jarvis.py offline package-post <queue_id>",
    }
    next_cmd = cmd_map.get(plan.intent, "python jarvis.py dashboard offline")
    return f"""# Proximo Passo — {plan.mission_id}

**Missao gerada em dry-run.** Para executar:

1. Revisar `01_mission_brief.md` e confirmar objetivo
2. Preencher `02_context_used.md` com fatos do negocio
3. Executar o comando abaixo:

```powershell
{next_cmd}
```

4. Verificar qualidade: `python jarvis.py quality package <id>`
5. Aprovar: `python jarvis.py approvals approve <draft_id>`

> **NUNCA publicar sem aprovacao.** OAuth gate: 0/5 contas prontas.
"""
